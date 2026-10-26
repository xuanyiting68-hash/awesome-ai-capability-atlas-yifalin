#!/usr/bin/env python3
"""Source-only catalog harvester. Does NOT execute third-party skills."""
from __future__ import annotations
import csv
import json
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCE = "VoltAgent/awesome-openclaw-skills"
SLUGS = """ai-and-llms apple-apps-and-services browser-and-automation calendar-and-scheduling clawdbot-tools cli-utilities coding-agents-and-ides communication data-and-analytics devops-and-cloud gaming git-and-github health-and-fitness image-and-video-generation ios-and-macos-development marketing-and-sales media-and-streaming moltbook notes-and-pkm pdf-and-documents personal-development productivity-and-tasks search-and-research security-and-passwords self-hosted-and-automation shopping-and-e-commerce smart-home-and-iot speech-and-transcription transportation web-and-frontend-development""".split()
PATTERN = re.compile(r"^\s*[-*]\s+\[([^\]]+)\]\((https://clawskills\.sh/skills/[^\s)]+)\)\s*[-–—]\s*(.*)$")
FIELDS = ["id", "name", "repo", "url", "type", "topic", "priority", "score", "description_zh", "use_case", "source", "verification", "safety_review", "risk", "fork_status"]
TOPICS = {"ai-and-llms":"AI研究", "browser-and-automation":"浏览器自动化", "coding-agents-and-ides":"开发工程", "web-and-frontend-development":"开发工程", "security-and-passwords":"安全评测", "marketing-and-sales":"自媒体运营", "search-and-research":"AI研究", "image-and-video-generation":"AI视频制作", "speech-and-transcription":"AI视频制作", "devops-and-cloud":"基础设施", "pdf-and-documents":"知识教育", "data-and-analytics":"增长分析", "self-hosted-and-automation":"业务自动化"}

def download(slug):
    url = f"https://raw.githubusercontent.com/{SOURCE}/main/categories/{slug}.md"
    req = urllib.request.Request(url, headers={"User-Agent":"YIFALIN-AI-Capability-Atlas/1.1","Accept":"text/plain"})
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read(1500000).decode("utf-8")

def extract(slug, text):
    rows = []
    seen = set()
    for line in text.splitlines():
        m = PATTERN.match(line)
        if not m:
            continue
        name, url, summary = (part.strip() for part in m.groups())
        if url in seen or not name or not summary:
            continue
        seen.add(url)
        rows.append({"id":"claw:"+url.rsplit("/",1)[-1],"name":name,"repo":"clawskills.sh / "+slug,"url":url,"type":"skill","topic":TOPICS.get(slug,"其他领域"),"priority":"bulk","score":0,"description_zh":summary[:500],"use_case":"公开候选索引，安装或 Fork 前独立审查","source":f"{SOURCE}/categories/{slug}.md","verification":"indexed-upstream","safety_review":"not-audited","risk":"high","fork_status":"check-license-before-fork"})
    return rows

def round_robin(curated, grouped, limit=5000):
    out = list(curated)
    seen = set(x["url"] for x in out)
    pointers = {slug:0 for slug in SLUGS}
    while len(out) < limit:
        made = False
        for slug in SLUGS:
            rows = grouped.get(slug, [])
            while pointers[slug] < len(rows):
                row = rows[pointers[slug]]
                pointers[slug] += 1
                if row["url"] in seen:
                    continue
                out.append(row)
                seen.add(row["url"])
                made = True
                break
            if len(out) >= limit:
                break
        if not made:
            break
    return out

def main():
    curated = json.loads((ROOT/"data"/"curated.json").read_text("utf-8"))
    results = {}
    errors = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        tasks = {pool.submit(download, slug):slug for slug in SLUGS}
        for future in as_completed(tasks):
            slug = tasks[future]
            try:
                results[slug] = extract(slug, future.result())
            except Exception as exc:
                errors[slug] = str(exc)
    if errors:
        print("Refusing partial snapshot because source categories failed:", json.dumps(errors,ensure_ascii=False),file=sys.stderr)
        return 2
    data = round_robin(curated, results, 5000)
    folder = ROOT/"data"
    folder.mkdir(parents=True, exist_ok=True)
    (folder/"catalog.json").write_text(json.dumps(data,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    with (folder/"catalog.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
    report={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"curated":len(curated),"public_candidates":len(data)-len(curated),"total":len(data),"categories_ok":len(results),"source":SOURCE,"security_audited":False,"third_party_skills_executed":False}
    (folder/"provenance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (folder/"excluded.json").write_text("[]\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
