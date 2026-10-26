#!/usr/bin/env python3
"""YIFALIN Atlas multi-source indexer: read public metadata, NEVER install or run skills."""
from __future__ import annotations
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import csv
import json
import os
import re
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.harvest import SLUGS, SOURCE as OPENCLAW_SOURCE, extract as extract_openclaw, FIELDS

ROOT=Path(__file__).resolve().parents[1]
LIMIT=5000
AGENT_SKILL=re.compile(r"(?:^|/)SKILL\.md$")
REPO_SOURCES=[
    ("anthropics/skills",24,"official-source"),
    ("openai/skills",60,"official-source"),
    ("microsoft/skills",200,"publisher-repository"),
    ("github/awesome-copilot",520,"publisher-repository"),
    ("wshobson/agents",340,"community-repository"),
    ("Zie619/n8n-workflows",950,"workflow-repository"),
    ("sickn33/agentic-awesome-skills",1100,"community-repository"),
]
MCP_GITHUB_QUOTA=220
MCP_REGISTRY_QUOTA=220
OPENCLAW_QUOTA=2400
FIELDS_WITH_PROVENANCE=FIELDS+["ecosystem","source_kind","review_level","license_review","discovery_method"]
UA="YIFALIN-AI-Capability-Atlas/1.3 (public metadata, no skill execution)"

def get_json(url, allow=None):
    if not (url.startswith("https://api.github.com/") or url.startswith("https://registry.modelcontextprotocol.io/")):
        raise ValueError("External API URL not on allowlist")
    headers={"Accept":"application/vnd.github+json","User-Agent":UA}
    token=os.environ.get("GITHUB_TOKEN")
    if url.startswith("https://api.github.com/") and token:
        headers["Authorization"]="Bearer "+token
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers=headers),timeout=28) as response:
                payload=response.read(9_000_000)
            if len(payload)>=9_000_000:
                raise RuntimeError("Response larger than 9 MB safe limit")
            return json.loads(payload)
        except HTTPError as exc:
            if exc.code in (403,429,500,502,503) and attempt<2:
                time.sleep(2*(attempt+1))
                continue
            raise

def topic_from_path(name):
    s=name.lower()
    for terms, topic in [
        (("video","youtube","tiktok","short","reels","remotion","movie","media","subtitle","voice"),"AI视频制作"),
        (("marketing","social","twitter","instagram","linkedin","seo","content-creator"),"自媒体运营"),
        (("sales","lead","prospect","scrap","outreach"),"智能获客"),
        (("customer","crm","support","retention","service"),"客户关系维护"),
        (("growth","analytics","measurement","conversion","ab-test"),"增长分析"),
        (("financ","trade","quant","stock","market","investment"),"金融量化"),
        (("education","tutor","learn","course","teacher","academic"),"知识教育"),
        (("security","audit","secret","red-team","privacy"),"安全评测"),
        (("devops","cloud","kubernetes","docker","terraform"),"基础设施"),
        (("agent","coding","python","typescript","javascript","github"),"开发工程")
    ]:
        if any(k in s for k in terms):return topic
    return "其他领域"

def mkrow(*,name,url,repo,kind,ecosystem,source_kind,source_path="",description="",discovery="repo-tree"):
    return {
      "id":ecosystem+":"+re.sub(r"[^a-zA-Z0-9._/-]","-",source_path or name)[:190],
      "name":str(name)[:110],"repo":repo,"url":url,"type":kind,"topic":topic_from_path(name+" "+source_path),
      "priority":"bulk","score":0,"description_zh":str(description or (kind.upper()+" candidate from public "+ecosystem+" index; read original source."))[:350],
      "use_case":"来自公开目录的候选资源，需独立复核用途、授权与安全",
      "source":repo+"/"+source_path,"verification":"indexed-upstream",
      "safety_review":"not-audited","risk":"unassessed","fork_status":"check-license-before-fork",
      "ecosystem":ecosystem,"source_kind":source_kind,"review_level":"discovery-only",
      "license_review":"not-checked","discovery_method":discovery}

def tree_candidate(repo,path,level):
    if path.startswith((".github/workflows/","tests/","test/","docs/examples/")):return None
    kind="skill" if AGENT_SKILL.search(path) else ("agent" if path.endswith((".agent.md",)) or re.search(r"/agents/[^/]+\.md$",path) else "workflow" if path.endswith(".json") else None)
    if kind is None:return None
    if repo=="anthropics/skills" and not re.fullmatch(r"skills/[^/]+/SKILL\.md",path):return None
    if repo=="openai/skills" and not re.fullmatch(r"skills/[^/]+/[^/]+/SKILL\.md",path):return None
    if repo=="microsoft/skills" and not (AGENT_SKILL.search(path) or re.fullmatch(r"\.github/agents/[^/]+\.agent\.md",path)):return None
    if repo=="github/awesome-copilot" and not (re.fullmatch(r"(?:\.github/)?skills/[^/]+/SKILL\.md",path) or re.fullmatch(r"agents/[^/]+\.agent\.md",path)):return None
    if repo=="wshobson/agents" and not re.fullmatch(r"plugins/[^/]+/(?:skills/[^/]+/SKILL\.md|agents/[^/]+\.md)",path):return None
    if repo=="Zie619/n8n-workflows" and not re.fullmatch(r"workflows/[^/]+/[^/]+\.json",path):return None
    if repo=="sickn33/agentic-awesome-skills" and not re.fullmatch(r"plugins/agentic-awesome-skills/skills/[^/]+/SKILL\.md",path):return None
    slug=path.removesuffix("/SKILL.md").rsplit("/",1)[-1]
    if path.endswith(".agent.md"):slug=slug[:-9]
    if path.endswith(".json"):slug=slug[:-5]
    name=slug.replace("_"," ").replace("-"," ").strip()[:110]
    url="https://github.com/"+repo+"/blob/main/"+quote(path,safe="/")
    return mkrow(name=name,url=url,repo=repo,kind=kind,ecosystem=repo.split("/")[0]+"-skills" if kind=="skill" else ("n8n-workflows" if kind=="workflow" else "github-agents"),source_kind=level,source_path=path,discovery="repo-tree")

def evenly_select(rows,limit):
    if len(rows)<=limit:return rows
    return [rows[i*len(rows)//limit] for i in range(limit)]

def load_repo(repo,quota,level):
    if repo=="sickn33/agentic-awesome-skills":
        # Avoid the >9MB monorepo: traverse the canonical skills plugin only.
        base="https://api.github.com/repos/"+repo+"/git/trees/"
        root=get_json(base+"main")
        plugins=next(item["sha"] for item in root["tree"] if item["path"]=="plugins" and item["type"]=="tree")
        p_tree=get_json(base+plugins)
        canonical=next(item["sha"] for item in p_tree["tree"] if item["path"]=="agentic-awesome-skills" and item["type"]=="tree")
        obj=get_json(base+canonical+"?recursive=1")
        prefix="plugins/agentic-awesome-skills/"
    else:
        obj=get_json("https://api.github.com/repos/"+repo+"/git/trees/main?recursive=1")
        prefix=""
    if obj.get("truncated"):raise RuntimeError("Git tree truncated, refusing misleading partial data: "+repo)
    paths=sorted(prefix+x["path"] for x in obj.get("tree",[]) if x.get("type")=="blob")
    matches=[row for p in paths if (row:=tree_candidate(repo,p,level))]
    if not matches:raise RuntimeError("No eligible paths found: "+repo)
    return evenly_select(matches,quota)

def load_openclaw():
    from scripts.harvest import download
    grouped={}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures={pool.submit(download,slug):slug for slug in SLUGS}
        for future in as_completed(futures):
            slug=futures[future]
            grouped[slug]=extract_openclaw(slug,future.result())
    result=[]
    pos={slug:0 for slug in SLUGS}
    while len(result)<OPENCLAW_QUOTA:
        found=False
        for slug in SLUGS:
            rows=grouped[slug]
            if pos[slug]>=len(rows):continue
            d=dict(rows[pos[slug]])
            pos[slug]+=1
            d.update({"ecosystem":"openclaw","source_kind":"community-directory","review_level":"discovery-only",
              "license_review":"not-checked","discovery_method":"markdown-link","risk":"unassessed"})
            result.append(d)
            found=True
            if len(result)>=OPENCLAW_QUOTA:break
        if not found:break
    return result

def load_github_mcp():
    items=[]
    for page in (1,2,3):
        params=urlencode({"q":"topic:mcp-server archived:false","sort":"stars","order":"desc","per_page":100,"page":page})
        resp=get_json("https://api.github.com/search/repositories?"+params)
        for item in resp.get("items",[]):
            full=item.get("full_name","")
            url=item.get("html_url","")
            if not full or not url or item.get("archived"):continue
            items.append(mkrow(name=item.get("name",full),url=url,repo=full,kind="mcp",ecosystem="github-mcp",source_kind="github-topic-search",
               source_path=full,description=item.get("description") or "GitHub MCP Server topic candidate",discovery="github-search"))
        if len(items)>=MCP_GITHUB_QUOTA:break
    return evenly_select(items,MCP_GITHUB_QUOTA)

def load_registry():
    items=[]
    cursor=None
    visited=set()
    while len(items)<MCP_REGISTRY_QUOTA:
        params={"limit":100,"version":"latest"}
        if cursor:params["cursor"]=cursor
        response=get_json("https://registry.modelcontextprotocol.io/v0.1/servers?"+urlencode(params))
        for wrapped in response.get("servers",[]):
            entry=wrapped.get("server",wrapped)
            if not isinstance(entry,dict):continue
            name=entry.get("name") or ""
            if not name:continue
            repo=entry.get("repository") or {}
            ref=repo.get("url") if isinstance(repo,dict) else None
            # Preserve a unique, authoritative detail link for every registry entry.
            detail="https://registry.modelcontextprotocol.io/v0.1/servers/"+quote(name,safe="")+"/versions/latest"
            url=ref if isinstance(ref,str) and ref.startswith("https://") else detail
            items.append(mkrow(name=name,url=url,repo=name,kind="mcp",ecosystem="official-mcp-registry",
              source_kind="published-registry-record",source_path=name,
              description=entry.get("description") or "MCP Registry published server",
              discovery="mcp-registry"))
            if len(items)>=MCP_REGISTRY_QUOTA:break
        cursor=(response.get("metadata") or {}).get("nextCursor")
        if not cursor or cursor in visited:break
        visited.add(cursor)
    if not items:raise RuntimeError("MCP registry returned no server records")
    return items

def assemble(curated,groups,limit=LIMIT):
    out=[];urls=set()
    def add(row):
        url=row.get("url","")
        key=url.lower().rstrip("/")
        if not key or key in urls:return False
        urls.add(key)
        out.append(row)
        return True
    for row in curated:add(row)
    for source in ["anthropics/skills","openai/skills","microsoft/skills","github/awesome-copilot",
                   "wshobson/agents","Zie619/n8n-workflows","sickn33/agentic-awesome-skills",
                   "official-mcp-registry","github-mcp","openclaw"]:
        for row in groups.get(source,[]):
            if len(out)>=limit:return out
            add(row)
    return out

def main():
    curated=json.loads((ROOT/"data"/"curated.json").read_text(encoding="utf-8"))
    for row in curated:
        row.setdefault("ecosystem","curated")
        row.setdefault("source_kind","editorial-selection")
        row.setdefault("review_level","repo-exists-not-audited")
        row.setdefault("license_review","not-checked")
        row.setdefault("discovery_method","human-shortlist")
    tasks=[(repo,lambda repo=repo,quota=q,level=level:load_repo(repo,quota,level)) for repo,q,level in REPO_SOURCES]
    tasks.extend([("official-mcp-registry",load_registry),("github-mcp",load_github_mcp),("openclaw",load_openclaw)])
    groups={}
    warnings={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fn):key for key,fn in tasks}
        for future in as_completed(futures):
            key=futures[future]
            try:groups[key]=future.result()
            except Exception as exc:warnings[key]=str(exc)
    required={"anthropics/skills","openai/skills","github/awesome-copilot",
              "wshobson/agents","Zie619/n8n-workflows","sickn33/agentic-awesome-skills","openclaw"}
    missing=sorted(required-groups.keys())
    if missing:
        print("REFUSING incomplete multi-ecosystem index:",json.dumps({"missing":missing,"errors":warnings},ensure_ascii=False),file=sys.stderr)
        return 2
    rows=assemble(curated,groups)
    if len(rows)<4900:
        print("REFUSING undersized catalog:",len(rows),json.dumps(warnings),file=sys.stderr)
        return 2
    if len({r["url"].lower().rstrip("/") for r in rows}) != len(rows):
        print("Duplicate URLs in output",file=sys.stderr)
        return 3
    out=ROOT/"data"
    out.mkdir(exist_ok=True)
    report={
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "total":len(rows),
        "curated":len(curated),
        "public_candidates":len(rows)-len(curated),
        "source_counts":dict(Counter(r.get("ecosystem","unknown") for r in rows)),
        "source_failures":warnings,
        "sources_successful":list(groups),
        "reviewed_for_safety":0,
        "license_clearance_done":0,
        "third_party_code_executed":False,
        "methodology":"GitHub repository tree + MCP registry + GitHub MCP-topic discovery + OpenClaw public directory; source filenames / metadata only; URLs deduped"
    }
    (out/"catalog.json").write_text(json.dumps(rows,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    with (out/"catalog.csv").open("w",encoding="utf-8-sig",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=FIELDS_WITH_PROVENANCE,extrasaction="ignore")
        writer.writeheader();writer.writerows(rows)
    (out/"provenance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"excluded.json").write_text("[]\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
