"""V1.1 industry task-to-workflow Expert Studio. No third-party packages or network.

Run after build.py (build.py itself invokes build() at the bottom).
"""
from __future__ import annotations
from pathlib import Path
from datetime import date
import json, csv, html, re
ROOT=Path(__file__).parent

# Expert-curated two use cases per sector, as IDs in V1.0 taxonomy.
PAIRS='''
s01|documents|risk
s02|research|forecast
s03|documents|support
s04|documents|knowledge
s05|research|documents
s06|learning|analytics
s07|research|knowledge
s08|learning|hr
s09|knowledge|maintenance
s10|vision|supply
s11|documents|simulation
s12|support|maintenance
s13|sales|forecast
s14|content|support
s15|documents|supply
s16|support|forecast
s17|knowledge|vision
s18|maintenance|forecast
s19|knowledge|maintenance
s20|documents|geo
s21|legal|documents
s22|documents|risk
s23|hr|learning
s24|research|analytics
s25|knowledge|support
s26|research|content
s27|content|analytics
s28|design|content
s29|support|forecast
s30|coding|security
s31|support|maintenance
s32|content|automation
'''.strip()

# Scenario-specific, concrete prototype contracts. All are *proposals*, never performance claims.
PROTO={
 'knowledge':('证据可追溯知识问答','有权限的公开资料、文件版本号、10个测试问题','建立文档授权清单→按页码和版本索引→设计检索与引用→准备无法回答的负样本→抽样人工审核','来源可核对率、拒答质量、平均检索用时'),
 'research':('来源可信的研究证据图谱','研究问题、公开文献、纳入排除标准','定义研究问题与搜索边界→登记每项来源时间和作者→抽取证据/反例→建立引用矩阵→专业人员核验结论','引文可回溯率、遗漏率、研究用时'),
 'analytics':('业务分析与异常解释','脱敏指标表、原分析基线、指标字典','锁定指标定义→清洗脱敏表格→对照人工计算→输出原因假设→复核异常及保留查询日志','指标误差、可复现率、人工复核用时'),
 'risk':('风险事件分流与审计','公开或脱敏的审计案例、风控分类口径','列出风险分类→建立负例和严重性等级→输出仅作预警的信号→记录误报漏报→风控人员签发','漏报率、误报率、审计追踪完整率'),
 'support':('客服知识检索与人工升级','可公开的FAQ、工单标签、升级条件','核查知识授权和时效→构建意图分类→运行合成测试→敏感问题直接转人工→追踪回访和错误案例','首响时间、解决率、错误转人工率'),
 'sales':('同意管理的销售线索分类','自愿提供且可撤回的测试线索、同意记录','确认来源与同意→去重及标记需求→起草个性化回复→人工审核再发送→记录投诉及撤回','合格线索比例、人工处理时间、撤回响应'),
 'content':('原创内容生产与品牌审查','自有内容资产、品牌规范、渠道政策','确定目标读者和事实依据→生成不同版本草稿→检查版权和真实性→人工发布→A/B 对照评估','内容返工率、合规问题、有效互动率'),
 'documents':('文档抽取、比对与溯源','已获授权的文档样本、页码、字段标准','定义抽取字段→建立引用定位→对照人工标注→标记低置信度和空值→专业人员复核','字段准确率、漏检率、单件处理时间'),
 'automation':('有审批关卡的流程自动化','流程图、模拟事件、读写权限矩阵','标记每个读写动作→先做只读演练→为外发和写入设置审批→模拟失败/重试/撤销→记录审计日志','重复执行率、审批绕过次数、人工处理时间'),
 'learning':('分层学习练习与反馈','课程目标、获授权教案、匿名练习样本','分解学习目标→生成多级练习→核对答案与依据→教师审核并试教→比较前后测结果','知识掌握变化、错误反馈率、教师准备时间'),
 'clinical':('临床记录草稿与核对','脱敏模拟病例、标准模板、人工复核标准','限制为模拟/获授权数据→生成结构化草稿→标记药物剂量等歧义→临床人员逐字段核验→保留更正日志','关键差错数、专业更正率、文书用时'),
 'forecast':('基线可比较的预测试点','按时间排序的匿名历史记录、未来留出集','固定预测目标和时间窗口→构造简单基线→仅用历史信息训练→未来留出集比较→观察漂移与停止条件','MAE或业务损失、缺失率、失效触发次数'),
 'maintenance':('只读设备维护预警','脱敏设备日志、维护记录、可用传感器指标','划定不可控制设备边界→按时间整理日志→工程师标记故障案例→测试预警误报/漏报→仅输出待审工单','停机预警提前量、漏报率、工程复核用时'),
 'vision':('人工复判的视觉质检','获授权的图像、缺陷标签、批次信息','建立缺陷标注标准→按批次隔离测试集→跑图像识别基线→复核罕见关键缺陷→决定是否仅作提示','重要缺陷漏检率、误报率、复判耗时'),
 'design':('设计方案多版本比对','授权设计资产、约束与验收标准','收集约束→生成多个方案草稿→逐条检查品牌/工程约束→设计师复审→登记返工原因','方案周期、返工率、约束不符合项'),
 'supply':('采购与供应链异常整理','匿名订单、交付状态、库存口径','建统一SKU和供应商字段→按时间匹配订单→列出延迟与缺货异常→模拟补货选项→人工确认实际变更','缺货率、交付延误率、计划误差'),
 'legal':('法律条款定位与差异初审','已授权合同与司法辖区、律师审查清单','限定司法辖区→对齐条款与原文页码→列出义务和差异→标记不确定项→由执业专业人士审查','条款漏检率、引用准确率、审阅时间'),
 'hr':('岗位技能与培训建议','去标识化岗位要求、本人授权能力材料','去除敏感属性→定义岗位技能矩阵→对照授权经历→生成培训建议→人工检验公平和解释','技能映射可复核率、投诉率、培训完成率'),
 'coding':('可回滚的软件研发协作','可公开测试代码、任务说明、CI标准','建立独立分支→按最小变更实现→生成测试→复核依赖与安全→通过CI后人工合并','缺陷逃逸率、测试覆盖、交付周期'),
 'security':('Agent与工具权限红队评估','模拟用户、测试环境、工具权限清单','审计所需权限→构造越权与注入负例→验证写操作拒绝→记录审计事件→审查恢复和撤回','未经授权成功率、负例覆盖、回滚成功率'),
 'meeting':('会议证据与行动项整理','经所有参与者允许的录音或会议记录','确认录制同意→生成草稿纪要→标注决定与负责人→对照原文→参会者确认','行动项遗漏率、转写准确率、确认耗时'),
 'simulation':('规则明确的模拟决策试验','系统约束、模拟输入、人工专业审查','界定模型范围和禁区→建立人工基线→模拟不同场景→逐项审查安全约束→记录无法外推的风险','约束违反数、模拟偏差、专家审核时间'),
 'geo':('遥感与空间变化解释','合规地理数据、坐标参考、采集时间','核对坐标系与时间→清洗空间数据→对照人工标注→生成变化提示→专业人员现场核验','定位误差、漏报率、现场复核成本')
}
HIGH_SECTORS={'s02','s03','s04','s05','s06','s07','s08','s11','s16','s18','s19','s20','s21','s22','s23','s25','s30','s31'}
HIGH_SCENARIOS={'clinical','risk','legal','hr','security','maintenance','simulation','forecast'}
SOURCES=[
 {'id':'ms2026','title':'Microsoft Work Trend Index 2026','url':'https://www.microsoft.com/en-us/worklab/work-trend-index/agents-human-agency-and-the-opportunity-for-every-organization','use':'跨行业工作重构方法背景；不作为具体方案有效性证据'},
 {'id':'anthropic2026','title':'Anthropic Economic Index 2026','url':'https://www.anthropic.com/economic-index','use':'职业任务的自动化与增强分类背景；不推断个别岗位替代率'},
 {'id':'nist600','title':'NIST AI RMF Generative AI Profile','url':'https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence','use':'生成式AI风险管理框架'},
 {'id':'who','title':'WHO Healthcare AI Governance','url':'https://www.who.int/publications/i/item/9789240084759','use':'医疗AI临床使用需额外安全和专业验证'},
 {'id':'unesco','title':'UNESCO Teacher AI Competency Framework','url':'https://www.unesco.org/en/articles/ai-competency-framework-teachers?hub=365','use':'教师AI能力与教育情境'},
 {'id':'wef','title':'WEF Future of Jobs 2025','url':'https://www.weforum.org/publications/the-future-of-jobs-report-2025/','use':'技能转型与劳动力趋势背景；不是个别岗位预测'},
]

def build():
 data=json.loads((ROOT/'data.json').read_text(encoding='utf-8'))
 sectors={x['id']:x for x in data['sectors']}
 scenes={x['id']:x for x in data['scenarios']}
 tools=data['tools']; skills=data['first_party_skills']
 recipes=[]
 for sec_id,tag_a,tag_b in (x.split('|') for x in PAIRS.splitlines()):
  sec=sectors[sec_id]
  assert len({tag_a,tag_b})==2 and all(t in sec['scenarios'] for t in (tag_a,tag_b)),(sec_id,tag_a,tag_b)
  for order,tag in enumerate((tag_a,tag_b),1):
   p=PROTO[tag]; role=sec['roles'].split('、')[0]
   linked=[]
   for t in tools:
    if tag not in t['scenarios']:continue
    if t['industries'] and sec['name'] not in t['industries']:continue
    linked.append((3 if sec['name'] in t['industries'] else 0,2 if t['type'] in ('行业应用','知识库','自动化','文档工具','Agent/框架') else 0, t['name'].lower(),t))
   linked.sort(key=lambda v:(-v[0],-v[1],v[2]))
   selected=[v[3] for v in linked[:5]]
   skill=[s for s in skills if tag in s['scenarios']]
   tier='高敏感—只读/草稿+专业审批' if sec_id in HIGH_SECTORS or tag in HIGH_SCENARIOS else '一般—授权数据+人工抽查'
   recipe={
    'id':f'{sec_id}-{tag}', 'industry_id':sec_id,'industry':sec['name'],'group':sec['group'],
    'role':role, 'scenario_id':tag,'scenario':scenes[tag]['name'],
    'title':f'{sec["name"]}｜{p[0]}','problem':sec['pain'],
    'input_contract':p[1], 'steps':[x.strip() for x in p[2].split('→')],
    'expected_outputs':[p[0]+'结果草稿','原始证据与失败样本记录','人工审核/停止决策'],
    'kpi':p[3], 'start_point':sec['quick'] if order==1 else sec['mid'],
    'future_hypothesis':sec['future'], 'guardrail':sec['risk'],
    'risk_tier':tier, 'candidate_tools':[{'id':t['id'],'name':t['name'],'url':t['url'],'type':t['type']} for t in selected],
    'skill_templates':[{'id':s['id'],'name':s['name'],'path':'skills/'+s['slug']+'/SKILL.md'} for s in skill[:2]],
    'evidence_status':'编辑方案 / 未进行真实业务测试','sources':['ms2026','anthropic2026','nist600'] + (['who'] if sec_id=='s04' else []) + (['unesco'] if sec_id in ('s06','s07','s08') else []),
    'review_gate':'以同一测试集比较人工与AI流程。引用、权限、错误和成本未通过则不部署。',
    'published_at':'2026-11-01'
   }
   # Empty candidates are a valid and explicit catalog coverage gap; never invent a vendor.
   recipes.append(recipe)
 assert len(recipes)==64
 ds={'version':'1.1.0','as_of':'2026-11-01','state':'editorial-prototypes-not-verified-business-results',
     'industry_count':len(sectors),'scenario_count':len(scenes),'workflow_count':len(recipes),
     'sources':SOURCES,'workflows':recipes,
     'taxonomy':{'industries':[{'id':s['id'],'name':s['name'],'group':s['group']} for s in sectors.values()],
                 'scenarios':[{'id':s['id'],'name':s['name']} for s in scenes.values()]}}
 (ROOT/'workflows.json').write_text(json.dumps(ds,ensure_ascii=False,indent=2),encoding='utf-8')
 with (ROOT/'workflows.csv').open('w',encoding='utf-8-sig',newline='') as f:
  cols=['id','industry','role','scenario','title','problem','input_contract','steps','kpi','risk_tier','guardrail','evidence_status','candidate_tools']
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
  for r in recipes:
   w.writerow({k:('；'.join(r[k]) if k=='steps' else '、'.join(t['name'] for t in r['candidate_tools']) if k=='candidate_tools' else r.get(k,'')) for k in cols})
 # Self-contained offline expert tool; valid without server or fetch.
 page=PAGE.replace('__JSON__',json.dumps(ds,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
 (ROOT/'expert.html').write_text(page,encoding='utf-8')
 home=ROOT/'index.html'
 body=home.read_text(encoding='utf-8')
 if 'href="expert.html"' not in body:
  body=body.replace('<header>', '<header><div style="background:#194438;color:#e4fff8;text-align:center;padding:9px 12px;font-size:13px">新增：<a href="expert.html" style="color:#99ffe8;text-decoration:underline;font-weight:800">进入 AI 行业专家工作台 V1.1 →</a> · 64 个可检索试点方案／ROI 情景计算／跨行业借鉴</div>',1)
  home.write_text(body,encoding='utf-8')
 readme=ROOT/'README.md'
 with readme.open('a',encoding='utf-8') as f:
  f.write('\n## V1.1 · 行业 AI 专家工作台（新增）\n\n打开 `expert.html` 按行业/岗位/场景检索64套五步工作流，含专业审核、工具与技能映射、跨行业迁移、ROI情景测算和 Markdown / CSV 导出。离线运行，无API、无敏感数据上传。数据源为 `workflows.json` / `workflows.csv`，生成器为 `upgrade_v11.py`。新增6个核验过官方产品页面的候选工具，但没有独立商用与安全实测。\n\n运行：`python build.py` 后执行 `python validate.py && python check.py && python check_expert.py && python check_workflows.py`。\n\n所有64套均属于编辑研究假说而非真实客户案例，工具推荐不是已验证兼容性保证；ROI 是用户输入的算术情景、不是已实现收益。\n')
 print(f'V1.1 built: {len(recipes)} workflows, {len(page.encode("utf-8"))//1024}KiB self-contained expert.html')

PAGE=r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 行业专家工作台 V1.1 · YIFALIN</title><meta name="description" content="32行业×64工作流｜场景诊断、工具与Skills关联、人工审批与ROI情景测算"><style>
:root{color-scheme:dark;--bg:#08111f;--card:#122239;--edge:#28425e;--ink:#eff9ff;--muted:#a5b9ca;--mint:#64dfbf;--gold:#f7c783}*{box-sizing:border-box}body{margin:0;font:14px/1.65 system-ui,"Microsoft YaHei",sans-serif;background:radial-gradient(circle at 10% 0%,#173c4e,transparent 42%),var(--bg);color:var(--ink)}a{color:#9aeed9}a:hover{text-decoration:underline}button,input,select{font:inherit}button{cursor:pointer}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{outline:2px solid #9aeed9;outline-offset:3px}header{border-bottom:1px solid var(--edge);background:#0c1a2dbb;padding:17px max(18px,calc((100vw - 1260px)/2));display:flex;justify-content:space-between;gap:15px;align-items:center;flex-wrap:wrap}.logo{font-weight:850;font-size:15px}.logo b{color:var(--mint)}main{max-width:1280px;padding:0 20px 70px;margin:auto}.hero{padding:40px 0 17px}.sub{color:var(--mint);letter-spacing:1.5px;font-weight:800;font-size:11px}.hero h1{font-size:clamp(29px,4.5vw,52px);margin:10px 0;line-height:1.2}.hero h1 span{color:var(--mint)}.lead{color:var(--muted);max-width:930px;font-size:15px}.stats{display:flex;gap:11px;flex-wrap:wrap;margin:20px 0}.stat{background:#12263a;border:1px solid #305165;border-radius:13px;padding:12px 20px}.stat b{font-size:25px}.stat small{display:block;color:var(--muted)}.alert{background:#312c27;color:#e8d1af;padding:12px 16px;border:1px solid #66503c;border-radius:12px;margin:18px 0;font-size:12px}.panels{display:grid;grid-template-columns:1.22fr .95fr;gap:17px;margin-top:24px}.card{background:linear-gradient(145deg,#13263a,#0e1c2e);border:1px solid var(--edge);border-radius:17px;padding:20px;min-width:0}.card h2{margin:0 0 14px;font-size:21px}.controls{display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px;margin:13px 0}.controls label{display:block;color:var(--muted);font-size:12px}.controls select,.controls input,.calcgrid input{width:100%;background:#091728;border:1px solid #34556e;padding:10px 11px;border-radius:10px;color:white;margin-top:5px;min-width:0}.buttons{display:flex;gap:8px;flex-wrap:wrap;margin:13px 0}.btn{background:#1a3e4d;border:1px solid #3c786f;color:#d7ffef;border-radius:10px;padding:9px 13px;font-weight:700}.btn.primary{background:#59d4b5;color:#08271d;border-color:transparent}.btn.alt{background:#19283f;border-color:#324663}.muted{color:var(--muted)}.small{font-size:12px}.list{display:grid;gap:10px;max-height:555px;overflow:auto;padding-right:5px}.item{background:#0b1b2e;border:1px solid #2b435c;padding:13px 16px;border-radius:12px}.item.active{border-color:var(--mint);background:#16363e}.item h3{font-size:15px;margin:3px 0}.item p{margin:3px 0;color:var(--muted);font-size:12px}.item button{border:0;background:none;padding:0;color:var(--mint);font-weight:700;text-align:left}.pill{display:inline-block;border:1px solid #3c586b;border-radius:999px;padding:1px 8px;color:#b7ccdd;font-size:11px;margin:3px 3px 2px 0}.risk{color:#f4c68b}.kv{border-top:1px solid #2b4760;padding:10px 0}.kv strong{color:#78e3cb;display:block;font-size:12px}.steps{padding-left:20px}.steps li{margin:7px 0}.toolbox{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0}.tool{background:#173647;border:1px solid #30576b;border-radius:10px;padding:5px 9px;font-size:12px}.calcgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.calcgrid label{font-size:12px;color:#b8cce2}.calcresult{background:#0b1e2c;border:1px solid #3b526d;padding:12px 14px;border-radius:12px;margin-top:12px}.calcresult b{font-size:24px;color:var(--mint)}.foot{margin:16px 0;color:#a9bdd1;font-size:12px}.empty{padding:28px;text-align:center;color:var(--muted)}.sources a{display:inline-block;margin:0 11px 8px 0}.analog{margin-top:8px}.analog button{border:1px solid #3c5b6d;background:#152c3e;border-radius:9px;color:#b3eedd;padding:7px 10px;margin:0 7px 7px 0}footer{border-top:1px solid var(--edge);margin-top:26px;padding:20px 0;color:var(--muted)}@media(max-width:900px){.panels{grid-template-columns:1fr}.controls{grid-template-columns:1fr 1fr}.controls label:first-child{grid-column:1/-1}.list{max-height:440px}}@media(max-width:500px){.controls{grid-template-columns:1fr}.controls label:first-child{grid-column:auto}.calcgrid{grid-template-columns:repeat(2,1fr)}.stats .stat{flex:1}}
</style></head><body>
<header><div class="logo">◈ YIFALIN <b>行业 AI 专家工作台</b> / Expert Studio</div><nav><a href="index.html">← 返回32行业工具图谱</a>　<a href="https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin" target="_blank" rel="noopener">原有5,000条资源 Atlas ↗</a></nav></header>
<main><section class="hero"><div class="sub">WORK DESIGN · SKILLS · AGENTS · EVIDENCE</div><h1>从你的工作问题出发，<span>找到可执行的 AI 转型路径。</span></h1><p class="lead">选择行业和业务任务，查看输入要求、具体步骤、适用工具与 Skills、风险审批门槛；还可以用自己的工时与费用假设估算试点净收益。所有方案均为研究型蓝图，不是已经验证的客户案例。</p><div class="stats"><div class="stat"><b id="nWorkflow">64</b><small>工作流方案</small></div><div class="stat"><b>32</b><small>行业</small></div><div class="stat"><b>23</b><small>场景</small></div><div class="stat"><b>6</b><small>跨行业参考来源</small></div></div></section>
<div class="alert">证据标识：本页64套均为<strong>编辑建议 / 未进行真实业务测试</strong>。工具链接为候选入口，不是实际API兼容性、商业许可、性能或安全审计结果。跨行业相似关系只是场景重叠，不代表能直接复用。</div>
<div class="card"><h2>01 · 查找行业业务蓝图</h2><div class="controls"><label>关键词／岗位／痛点<input id="query" placeholder="例如：教师、合同、设备维护、客服、金融" aria-label="搜索关键词"></label><label>行业<select id="sector" aria-label="行业筛选"><option value="">全部行业</option></select></label><label>场景<select id="scene" aria-label="场景筛选"><option value="">全部场景</option></select></label></div><div class="buttons"><button class="btn alt" id="reset">重置筛选</button><button class="btn alt" id="random">随机查看其他行业</button><span id="resultCount" class="muted small" aria-live="polite"></span></div></div>
<div class="panels"><section class="card"><h2>02 · 具体任务清单</h2><div id="results" class="list"></div></section><section class="card"><h2>03 · 方案详情与落地路线</h2><div id="detail" aria-live="polite"></div></section></div>
<div class="panels"><section class="card"><h2>04 · 试点 ROI 情景计算器</h2><p class="muted small">输入你自己的假设，计算每月净节省工时及成本。它只做算术，不预测未来收益；不考虑机会成本、现金流贴现与无法量化的重大风险。</p><div class="calcgrid"><label>每月任务件数<input id="volume" type="number" value="100" min="0" step="1"></label><label>原每件分钟<input id="before" type="number" value="20" min="0"></label><label>AI每件分钟<input id="after" type="number" value="7" min="0"></label><label>人工复核分钟<input id="review" type="number" value="5" min="0"></label><label>每小时人力成本（元）<input id="hourly" type="number" value="80" min="0"></label><label>每月工具及运维成本（元）<input id="fixed" type="number" value="300" min="0"></label><label>失败返工额外分钟/件<input id="rework" type="number" value="2" min="0"></label><label>可被使用的比例（%）<input id="adoption" type="number" value="70" min="0" max="100"></label></div><div class="calcresult" id="calcOutput" aria-live="polite"></div><div class="buttons"><button class="btn alt" id="calcReset">恢复示例参数</button><button class="btn primary" id="calcExport">导出计算假设 CSV</button></div></section>
<section class="card"><h2>05 · 跨行业迁移与证据治理</h2><p class="muted small">在同一业务场景中参考其他行业的试验方法，注意行业监管和决策权限不能照搬。</p><div id="analogs" class="analog"></div><div class="kv"><strong>证据层次</strong>官方页面或研究报告 ≠ 独立真实业务试点 ≠ 能商用且适合生产。当前只提供来源与候选映射，未为每一项建立独立质量结论。</div><div class="kv"><strong>试点停用触发器</strong>发现引用失真、隐私/权限越界、关键错误、重试造成重复写入、成本超出预算、真实业务结果低于基线时立即暂停。</div><div class="kv"><strong>技能资源</strong>相关 Skill 模板详见主图谱的“Skills”专区；从下载开始并不代表允许执行或授权访问账户。</div><div class="sources" id="sources"></div></section></div><footer>YIFALIN 全行业 AI 能力图谱 · V1.1 · 静态离线版 · 数据快照 2026-11-01 · 不收集输入数据，不联网发送计算参数。</footer></main>
<script id="DATA" type="application/json">__JSON__</script><script>
'use strict';const D=JSON.parse(document.getElementById('DATA').textContent),$=x=>document.getElementById(x),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let active='';
function setup(){for(let s of D.taxonomy.industries)$('sector').add(new Option(s.name,s.id));for(let s of D.taxonomy.scenarios)$('scene').add(new Option(s.name,s.id));for(let x of ['query','sector','scene'])$(x).addEventListener(x==='query'?'input':'change',render);$('reset').onclick=()=>{$('query').value='';$('sector').value='';$('scene').value='';active='';render()};$('random').onclick=()=>{let w=D.workflows[Math.floor(Math.random()*D.workflows.length)];$('query').value='';$('sector').value=w.industry_id;$('scene').value=w.scenario_id;active=w.id;render()};$('results').addEventListener('click',e=>{const b=e.target.closest('[data-id]');if(b){active=b.dataset.id;render()}});for(let id of ['volume','before','after','review','hourly','fixed','rework','adoption'])$(id).addEventListener('input',calc);$('calcReset').onclick=()=>{for(let [k,v] of Object.entries({volume:100,before:20,after:7,review:5,hourly:80,fixed:300,rework:2,adoption:70}))$(k).value=v;calc()};$('calcExport').onclick=exportCalc;$('analogs').addEventListener('click',e=>{let b=e.target.closest('[data-id]');if(b){let w=D.workflows.find(w=>w.id===b.dataset.id);if(w){$('query').value='';$('sector').value=w.industry_id;$('scene').value=w.scenario_id;active=w.id;render();$('detail').scrollIntoView({behavior:'smooth',block:'start'})}}});$('detail').addEventListener('click',e=>{if(e.target.closest('#downloadPlan'))downloadPlan()});$('sources').innerHTML=D.sources.map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a>`).join('');render();calc()}
function filtered(){let q=$('query').value.trim().toLocaleLowerCase('zh-CN'),sector=$('sector').value,scene=$('scene').value;return D.workflows.filter(w=>(!sector||w.industry_id===sector)&&(!scene||w.scenario_id===scene)&&(!q||[w.title,w.problem,w.role,w.scenario,w.start_point,w.kpi,...w.candidate_tools.map(t=>t.name)].join(' ').toLocaleLowerCase('zh-CN').includes(q)))}
function render(){let rows=filtered();$('resultCount').textContent=`匹配 ${rows.length} / ${D.workflows.length} 套方案`;if(!rows.some(r=>r.id===active))active=rows[0]?.id||'';$('results').innerHTML=rows.map(w=>`<div class="item ${w.id===active?'active':''}"><span class="pill">${esc(w.group)}</span><span class="pill">${esc(w.scenario)}</span><h3><button data-id="${esc(w.id)}">${esc(w.title)}</button></h3><p>岗位：${esc(w.role)} · ${esc(w.problem)}</p><p class="risk">${esc(w.risk_tier)} · 编辑建议，未实测</p></div>`).join('')||'<div class="empty">没有符合条件的方案，试试其他关键词或行业。</div>';let w=D.workflows.find(r=>r.id===active);$('detail').innerHTML=w?`<span class="pill">${esc(w.industry)}</span><span class="pill">${esc(w.scenario)}</span><h3>${esc(w.title)}</h3><div class="kv"><strong>岗位及原问题</strong>${esc(w.role)} · ${esc(w.problem)}</div><div class="kv"><strong>输入资料最低要求</strong>${esc(w.input_contract)}</div><div class="kv"><strong>执行步骤（研究型方案）</strong><ol class="steps">${w.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol></div><div class="kv"><strong>交付物</strong>${esc(w.expected_outputs.join('；'))}</div><div class="kv"><strong>可评测KPI</strong>${esc(w.kpi)}；需要旧流程对照，禁止只看模型生成速度</div><div class="kv"><strong>工具候选（非排名、未实测）</strong><div class="toolbox">${w.candidate_tools.length?w.candidate_tools.map(t=>`<a class="tool" target="_blank" rel="noopener noreferrer" href="${esc(t.url)}">${esc(t.name)} ↗</a>`).join(''):'暂无适配候选；需要补充核验'}</div></div><div class="kv"><strong>匹配 Skills</strong>${esc(w.skill_templates.map(s=>s.name).join('、')||'待建立专用技能')}</div><div class="kv"><strong>后续机会假说</strong>${esc(w.future_hypothesis)}</div><div class="kv"><strong>风险等级及人工门槛</strong>${esc(w.risk_tier)}；${esc(w.guardrail)}；${esc(w.review_gate)}</div><div class="buttons"><button id="downloadPlan" class="btn primary">下载本行业试点方案（Markdown）</button></div><p class="muted small">证据状态：${esc(w.evidence_status)}；方案更新时间：${esc(w.published_at)}</p>`:'<p class="empty">请选择一个方案。</p>';renderAnalogs(w)}
function renderAnalogs(w){if(!w){$('analogs').innerHTML='';return}const other=D.workflows.filter(x=>x.industry_id!==w.industry_id && x.group!==w.group && x.scenario_id===w.scenario_id);const seen=new Set(),r=other.filter(x=>!seen.has(x.industry_id)&&seen.add(x.industry_id)).slice(0,5);$('analogs').innerHTML=`<p><strong>${esc(w.scenario)}</strong> 在其他行业的研究方案：</p>`+r.map(x=>`<button data-id="${esc(x.id)}">${esc(x.industry)} · ${esc(x.role)}</button>`).join('')+'<p class="muted small">仅按场景标签关联；行业之间的数据许可、风险与有效性没有自动继承。</p>'}
function num(k){let v=Number($(k).value);return Number.isFinite(v)?Math.max(0,v):0}function calcData(){let n=num('volume'),b=num('before'),a=num('after'),r=num('review'),rw=num('rework'),rate=Math.min(100,num('adoption'))/100,cost=num('hourly'),fixed=num('fixed');let hours=n*rate*(b-a-r-rw)/60;return {n,b,a,r,rw,rate,cost,fixed,hours,net:hours*cost-fixed}}
function calc(){let d=calcData();$('calcOutput').innerHTML=`<div class="small muted">月度有效处理量：${(d.n*d.rate).toFixed(0)} 件；包含人工复核与返工时间</div><div>月净节省工时：<b>${d.hours.toFixed(1)} h</b></div><div>月净节省金额（情景测算）：<b>${d.net.toLocaleString('zh-CN',{maximumFractionDigits:0})} 元</b></div><div class="small muted">若为负值，代表当前假设下成本高于节省。未纳入模型错误造成的潜在损失。</div>`}
function dl(name,content,type){let blob=new Blob([content],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1200)}
function downloadPlan(){let w=D.workflows.find(x=>x.id===active);if(!w)return;let lines=[`# ${w.title}`,'',`证据等级：${w.evidence_status} · 版本 ${D.version}`,'',`## 岗位与痛点`,`- 岗位：${w.role}`,`- 问题：${w.problem}`,'',`## 必要输入`,w.input_contract,'',`## 5步试点`,...w.steps.map((s,i)=>`${i+1}. ${s}`),'',`## 工具候选（未进行兼容与许可审计）`,...w.candidate_tools.map(t=>`- ${t.name}: ${t.url}`),'',`## 交付及指标`,w.expected_outputs.join('；'),w.kpi,'',`## 人工签发门槛`,w.guardrail,w.review_gate,'',`## 中长期机会假设（待验证）`,w.future_hypothesis];dl(w.id+'-pilot.md',lines.join('\n'),'text/markdown;charset=utf-8')}
function exportCalc(){let d=calcData(),cols=['monthly_tasks','before_minutes','after_minutes','review_minutes','rework_minutes','adoption_fraction','hourly_cost_yuan','fixed_cost_yuan','saved_hours','net_saving_yuan'],vals=[d.n,d.b,d.a,d.r,d.rw,d.rate,d.cost,d.fixed,d.hours,d.net];dl('ai-pilot-roi-scenario.csv','\uFEFF'+cols.join(',')+'\r\n'+vals.join(',')+'\r\n','text/csv;charset=utf-8')}
setup();
</script></body></html>'''

if __name__=='__main__':build()