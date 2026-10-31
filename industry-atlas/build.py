from pathlib import Path
import json, csv, re, html, collections, datetime
ROOT=Path(__file__).parent
STAMP='2026-11-01'
SECTORS='''银行与金融服务|金融|银行经理、投研、风控、运营|信息碎片化、核验耗时、审计压力|财报与政策知识库；投研文档溯源|合规问答与风控案例工作流|可追溯多智能体投研、风险监测协作|资料核验时间、错误率、审查覆盖率|敏感账户信息、投资建议和模型漂移需人工审批|knowledge,research,analytics,risk,documents
证券与资管|金融|量化分析师、基金经理、交易员|研究重复、数据孤岛、模型过拟合|研报抽取、数据字典和行情摘要|研究实验注册、组合分析和报告核查|多源预测与可审计策略研究工厂|研究复用率、样本外表现、净成本后风险收益|禁止以回测收益推定实盘；不得自动执行交易|research,analytics,forecast,risk,documents
保险|金融|核保、理赔、精算、客服|资料审核慢、欺诈风险、客户体验差|理赔材料分类和保单问答|核保辅助与异常索赔分流|个性化保障方案与人机协作理赔|理赔周转时间、漏检率、申诉率|公平性、个人敏感信息及拒赔决定需人工复核|documents,support,risk,analytics,automation
医疗服务|健康|医生、护士、医院运营|病历录入耗时、院内知识分散|临床记录草稿、院内制度知识搜索|转诊协作和医疗流程文书核对|以临床验证为前提的个体化诊疗支持|文书时间、临床纠错率、医患满意度|高风险；诊断治疗、患者数据必须专业审核|clinical,documents,knowledge,automation,research
制药与生物科技|健康|药物研发、临床试验、法规事务|文献爆炸、试验设计复杂、监管提交繁琐|文献证据图谱、试验文件索引|实验假说检索与监管文档辅助|多模态研究与实验闭环（需真实验证）|检索召回率、试验周期、实验复现率|实验结论、药物安全和医学证据不能由生成文本替代|research,knowledge,documents,analytics,forecast
基础教育|教育|教师、教研员、校长|备课耗时、分层教学困难、反馈延迟|教案草稿、题目分层、教学资料索引|基于教师审查的个性化反馈|持续诊断式学习与教师主导教学协作|备课时间、学习进步、误判率|未成年人隐私、学术诚信与教学公平|learning,content,knowledge,analytics,documents
高等教育与科研|教育|教授、研究助理、学生|文献密集、研究流程重复、复现困难|文献矩阵、引文定位与数据清理|研究工作流与实验复现管理|可审计 AI 研究助理、跨学科知识发现|文献核验率、复现率、研究周期|禁止捏造引文、论文作者身份和实验结果|research,learning,knowledge,analytics,coding
职业培训与企业学习|教育|培训经理、讲师、HRBP|课程更新慢、培训效果不透明|课程知识库与技能差距评估|岗位技能图谱、智能练习|工作过程内嵌个性化持续学习|完课率、岗位表现、知识保留率|员工评估避免歧视与过度监控|learning,knowledge,hr,analytics,content
工业制造|工业|工厂经理、工艺工程师、质检员|停机损失、质检成本、经验难传承|SOP 检索、维修记录问答|视觉质检、预测性维护试点|数字孪生与柔性智能制造|停机时间、废品率、OEE|生产系统隔离、工业安全和模型漂移|maintenance,vision,knowledge,forecast,simulation
汽车与零部件|工业|研发、生产、售后|研发迭代与供应链协调复杂|设计评审摘要、故障工单整理|质量追溯、生产缺陷检验|仿真驱动的产品开发与供应协同|质量缺陷率、研发周期、返修率|安全关键部件需独立验证|design,vision,maintenance,supply,simulation
建筑工程与设计|工业|建筑师、施工经理、造价师|图纸冲突、进度风险、招投标文件复杂|图纸与合同知识搜索|现场图像进度核对、工程问答|BIM 联动的项目风险预测与方案优化|返工率、延期天数、审图覆盖率|工程安全、施工决策及审批责任|documents,design,vision,forecast,simulation
房地产与物业|服务|经纪人、物业经理、资产运营|线索分散、维修响应慢、资产数据割裂|房源资料标准化、物业知识库|客户问答与工单分流|建筑能耗与资产全生命周期运营|工单响应时间、出租周期、投诉率|房源真实性、公平住房和客户隐私|support,knowledge,sales,maintenance,analytics
零售与连锁门店|商业|店长、品类经理、门店运营|库存错配、陈列效率低、客流变化快|商品问答、营销内容生成|需求预测与补货优化|门店智能运营与动态供应链|缺货率、库存周转、转化率|价格歧视、消费者隐私与促销真实性|sales,content,forecast,supply,analytics
电商与跨境贸易|商业|电商运营、卖家、客服|多语种运营成本高、客服高峰、投放效率低|商品素材与多语翻译|营销实验、客服和订单协作|跨渠道预测与个性化服务闭环|退货率、CAC、复购率、转化率|遵守平台政策、营销授权和跨境数据规定|content,sales,support,forecast,automation
物流与仓储|交通|运输经理、仓储规划师、调度|路线优化难、库存不可见、异常处理慢|运单抽取与异常知识库|需求预测、库存可视化|端到端动态供应链协调代理|准时交付率、单位配送成本、库存准确率|调度系统必须有人为覆盖机制|supply,forecast,documents,analytics,automation
交通运输与出行|交通|交通规划师、车队经理、司机|调度波动、运力利用率低|客服和道路政策知识库|车队维护提醒、运力预测|安全约束下的智能交通协同|准点率、能耗、事故率|车辆控制与交通安全须严格审批|forecast,maintenance,support,simulation,analytics
农业与种植|资源|农场主、农艺师、合作社|病虫害难识别、天气影响大、投入品成本高|农业知识问答与记录整理|遥感监测、病害辅助识别|气候与生产联合决策系统|每公顷产量、药剂投入、病害误报率|农业建议须结合地区法规和实地验证|vision,geo,forecast,knowledge,analytics
能源与电力|资源|能源分析师、电网运营、设备经理|资产复杂、故障成本高、负荷波动|运维手册搜索、事故记录分类|负荷预测、设备异常监测|智能电网数字孪生与需求响应|计划外停机、预测误差、能耗|关键基础设施及电网控制必须隔离|forecast,maintenance,simulation,analytics,knowledge
矿业与材料|资源|矿业工程师、选矿专家、现场管理|地质数据分散、安全要求高|勘探报告与矿山 SOP 搜索|传感监测和设备维护预测|地质模型、采矿与能源协同优化|设备可用率、事故率、资源回收率|重大安全和生态影响决策需专业审核|simulation,maintenance,vision,forecast,knowledge
环境与可持续发展|资源|ESG 分析师、环境工程师|监测数据多、披露核验困难|排放资料整理、标准比对|遥感与监测异常分析|可审计环境数字孪生与适应策略|核算误差、数据覆盖率、响应时间|防范虚假绿色声明与误报|geo,analytics,documents,forecast,research
法律服务|专业服务|律师、法务、合规官|条款审查繁琐、法规更新快、证据检索耗时|合同抽取、法条知识检索|条款差异审查和审阅工单|可追溯法律研究与争议分析助手|审阅时间、错误率、来源可核验率|法律意见由执业人员签发；司法区差异|legal,documents,knowledge,research,automation
会计税务与审计|专业服务|会计师、审计师、财务主管|票据繁杂、审计样本量大、政策频繁变化|凭证分类、对账差异识别|异常交易提示和税务资料辅助|持续审计与可解释财务控制|对账时间、审计覆盖率、例外误报率|会计结论、税务申报及外部审计需复核|documents,analytics,risk,automation,legal
人力资源与招聘|专业服务|招聘经理、HRBP、人才发展|简历筛选量大、培训个性化不足|职位说明和面试题草稿|岗位能力图谱与培训推荐|技能为中心的人才流动匹配|招聘周期、留存率、培训效果|就业歧视、候选人数据隐私|hr,learning,knowledge,analytics,automation
咨询与企业管理|专业服务|咨询师、运营总监、战略经理|行业资料碎片化、反复出报告|资料搜集与访谈纪要整理|行业对标与决策备选方案引擎|企业实时情报与跨职能协作代理|分析交付周期、引用核验率、决策采纳率|客户保密、利益冲突和幻觉|research,documents,analytics,knowledge,automation
政府与公共服务|公共|政务办事、政策研究、公共服务|政策检索难、材料审核重复、便民压力|政策问答和办事指引|多部门工单分流、材料初审|透明可解释的公共服务协同|办结时间、可及性、投诉率|行政决定权、人权、公平性和数据主权|knowledge,documents,support,automation,legal
媒体新闻与出版|创意|编辑、记者、出版运营|素材检索慢、多渠道内容适配繁琐|采访转录、稿件校对与资料定位|内容生产流水线与事实核查|多模态生产与可信内容溯源|采编时间、纠错率、阅读留存|版权、肖像权、真实性及来源可追溯|content,research,documents,design,automation
广告营销与品牌|创意|市场经理、创意总监、投放经理|素材迭代快、获客成本波动|创意草稿、品牌知识库|活动自动化和 A/B 测试|从受众研究到素材的可控增长系统|CAC、线索质量、转化率|平台规则、广告真实性和用户同意|content,sales,design,analytics,automation
影视游戏与内容创作|创意|导演、设计师、游戏策划|美术成本高、制作链条长、需求变化快|概念图、视频脚本、原型素材|跨媒体生产工作流|实时交互世界生成与制作协作|迭代周期、素材复用率、返工率|版权、演员权益、深伪标识|design,content,simulation,coding,automation
餐饮酒店与旅游|服务|餐厅经理、酒店运营、旅行顾问|服务高峰、预订变动、评价管理|菜单翻译、服务知识库|预订咨询与需求预测|个性化旅行与服务协作|人均服务时间、预订转化、客诉率|不得伪造订单、评价和实时可用性|support,forecast,content,sales,automation
IT 软件与网络安全|技术|开发者、产品经理、安全运营|迭代压力、技术债、告警噪音|代码助手、文档问答|自动测试与工单协作|具备验证与回滚能力的软件开发代理|交付周期、缺陷逃逸率、告警误报率|最小权限、密钥安全和代码审查|coding,security,automation,knowledge,analytics
电信与互联网服务|技术|网络运维、客服、产品运营|网络告警复杂、用户服务工单量大|技术知识库和客服辅助|告警归因、网络流量分析|自适应网络保障与智能运维|MTTR、客户流失率、故障率|关键通信系统的授权与可靠性|maintenance,support,analytics,automation,security
中小微企业与个体经营|通用|创业者、自由职业者、个体商户|预算有限、重复事务占用时间|文案、表格、客服常见问答|发票/预约/CRM 轻量自动化|单人多 Agent 的小型企业运营|工时节省、线索转化、毛利率|先用不含敏感数据的流程试点|content,support,sales,automation,analytics'''
SCENARIOS='''knowledge|知识库与RAG|找得到、答得有来源
research|研究与信息检索|证据搜集和归纳
analytics|数据分析|看板、SQL 与洞察
risk|风控与审计|检测异常和留痕
support|客服与服务|问答、分类、转人工
sales|销售与获客|线索管理与CRM
content|营销与内容|文案、视频、传播
documents|文档与OCR|抽取、比对、归档
automation|工作流自动化|跨软件编排与审批
learning|学习培训|教案、个性化练习
clinical|临床文书支持|医疗记录草稿与审查
forecast|预测与优化|需求、负荷和风险预测
maintenance|设备运维|检修助手、故障预测
vision|计算机视觉|质检、识别、现场巡检
design|设计与创意|原型、建筑、设计
supply|供应链与采购|库存、采购、调度
legal|法规与法律检索|法律文书审阅
hr|人力与招聘|岗位能力与学习路径
coding|软件研发|编码、测试、部署
security|安全与治理|权限、评测、监控
meeting|会议与协作|录音转录、会议决策
simulation|数字孪生与仿真|设计验证与场景模拟
geo|遥感与空间数据|GIS、卫星监测'''
TOOLS='''ChatGPT|模型/助手|research,content,documents,analytics,learning|*|全球|SaaS|https://chatgpt.com/|通用任务、推理、文件与学习辅助
Claude|模型/助手|research,coding,documents,content|*|全球|SaaS|https://claude.ai/|长文档阅读、写作与代码任务
Gemini|模型/助手|research,learning,content,analytics|*|全球|SaaS|https://gemini.google.com/|Google 生态通用助手
DeepSeek|模型/助手|research,coding,analytics,content|*|中国/全球|SaaS/API|https://www.deepseek.com/|中文推理与技术辅助
Kimi|模型/助手|research,documents,content|*|中国/全球|SaaS|https://www.kimi.com/|文档阅读与资料整理
豆包|模型/助手|content,documents,learning|*|中国|SaaS|https://www.doubao.com/|中文内容与办公助手
通义|模型/助手|research,content,coding|*|中国|SaaS|https://tongyi.aliyun.com/|国内生态通用助手
Perplexity|研究/数据|research,knowledge|*|全球|SaaS|https://www.perplexity.ai/|带来源的网络研究入口
Microsoft 365 Copilot|模型/助手|documents,knowledge,analytics,meeting|*|全球|SaaS|https://www.microsoft.com/en-us/microsoft-365/copilot|Microsoft 365 办公协作
Google Workspace Gemini|模型/助手|documents,knowledge,content,meeting|*|全球|SaaS|https://workspace.google.com/solutions/ai/|Google Workspace 办公内嵌AI
NotebookLM|知识库|knowledge,research,learning,documents|*|全球|SaaS|https://notebooklm.google.com/|基于上传来源的学习和研究笔记
Dify|Agent/框架|knowledge,automation,support,research|*|全球/中国|自托管/云|https://dify.ai/|可视化 Agent、工作流与 RAG 应用
RAGFlow|知识库|knowledge,documents,research|*|全球/中国|自托管|https://github.com/infiniflow/ragflow|面向复杂文档的 RAG 系统
LlamaIndex|知识库|knowledge,documents,research|*|全球|代码/云|https://www.llamaindex.ai/|面向非结构化数据的 Agent/RAG 框架
AnythingLLM|知识库|knowledge,documents,research|*|全球|本地/自托管|https://anythingllm.com/|私有知识库与聊天入口
Glean|知识库|knowledge,research,hr|*|全球|企业SaaS|https://www.glean.com/|企业搜索与知识发现
Notion AI|知识库|knowledge,documents,automation|*|全球|SaaS|https://www.notion.so/product/ai|团队文档、任务与AI检索
飞书|知识库|knowledge,documents,automation,meeting|*|中国|SaaS|https://www.feishu.cn/|文档、知识库及协作平台
n8n|自动化|automation,support,sales,documents|*|全球/中国|自托管/云|https://n8n.io/|可视化业务工作流与Agent编排
Make|自动化|automation,sales,content,support|*|全球|SaaS|https://www.make.com/|跨应用自动化与条件逻辑
Zapier|自动化|automation,sales,support,content|*|全球|SaaS|https://zapier.com/|SaaS 软件连接和自动化
Activepieces|自动化|automation,documents,support|*|全球/中国|自托管/云|https://www.activepieces.com/|开源可自托管流程自动化
Power Automate|自动化|automation,documents,analytics|*|全球|SaaS/企业|https://www.microsoft.com/en-us/power-platform/products/power-automate|微软生态流程自动化
Copilot Studio|Agent/框架|automation,support,knowledge|*|全球|企业SaaS|https://www.microsoft.com/en-us/microsoft-copilot/microsoft-copilot-studio|可配置企业代理及工具接入
LangGraph|Agent/框架|automation,research,coding|*|全球|代码/自托管|https://www.langchain.com/langgraph|有状态 Agent 工作流
CrewAI|Agent/框架|automation,research,documents|*|全球|代码/云|https://www.crewai.com/|多Agent任务编排
AutoGen|Agent/框架|automation,coding,research|*|全球|开源代码|https://github.com/microsoft/autogen|多Agent研究与开发框架
Flowise|Agent/框架|knowledge,automation,support|*|全球|自托管/云|https://flowiseai.com/|低代码 LLM/Agent 流程
扣子 Coze|Agent/框架|automation,support,knowledge,content|*|中国|SaaS|https://www.coze.cn/|中文智能体构建平台
OpenAI Agents SDK|Agent/框架|automation,coding,research|*|全球|开源代码|https://openai.github.io/openai-agents-python/|多智能体/工具调用SDK
Agent Skills 标准|Skills/MCP|automation,coding,knowledge|*|全球|开放标准|https://agentskills.io/|可复用的技能包规范
Anthropic Skills|Skills/MCP|automation,coding,documents|*|全球|开源目录|https://github.com/anthropics/skills|技能模板与参考实现
OpenAI Skills|Skills/MCP|automation,coding,documents|*|全球|开源目录|https://github.com/openai/skills|技能样例资源
n8n 官方 Skills|Skills/MCP|automation,coding|*|全球|开源目录|https://github.com/n8n-io/skills|面向n8n构建的官方技能包
MCP Registry|Skills/MCP|automation,knowledge,coding|*|全球|注册目录|https://registry.modelcontextprotocol.io/|MCP连接器索引；质量与安全需另核验
Dify Marketplace|Skills/MCP|automation,knowledge,support|*|全球/中国|插件目录|https://marketplace.dify.ai/|Dify插件与Agent策略目录
Hugging Face|资源/目录|research,coding,vision|*|全球|社区/云|https://huggingface.co/|模型、数据、Space与评估资源
Kaggle|资源/目录|analytics,forecast,research|*|全球|社区/云|https://www.kaggle.com/|公开数据集、比赛、Notebook
Docling|文档工具|documents,knowledge,research|*|全球|开源代码|https://github.com/docling-project/docling|复杂文档结构化解析
MarkItDown|文档工具|documents,knowledge|*|全球|开源代码|https://github.com/microsoft/markitdown|多种文件转Markdown
Unstructured|文档工具|documents,knowledge|*|全球|自托管/云|https://unstructured.io/|非结构化文本和文档预处理
Firecrawl|研究/数据|research,documents,knowledge|*|全球|自托管/云|https://www.firecrawl.dev/|网页抓取和结构化输出
Elicit|研究/数据|research,knowledge|高等教育与科研,制药与生物科技|全球|SaaS|https://elicit.com/|学术文献工作流与论文检索
Consensus|研究/数据|research,knowledge|高等教育与科研,医疗服务|全球|SaaS|https://consensus.app/|研究文献问答
Semantic Scholar|研究/数据|research,knowledge|高等教育与科研,制药与生物科技|全球|网站/API|https://www.semanticscholar.org/|论文与引用搜索
Cursor|开发工具|coding,automation|IT 软件与网络安全,高等教育与科研|全球|桌面应用|https://cursor.com/|AI 编程环境
GitHub Copilot|开发工具|coding,automation|IT 软件与网络安全|全球|SaaS/IDE|https://github.com/features/copilot|代码补全和编码助手
OpenAI Codex|开发工具|coding,automation|IT 软件与网络安全|全球|应用/CLI|https://openai.com/codex/|AI 软件开发代理
Claude Code|开发工具|coding,automation|IT 软件与网络安全|全球|CLI/IDE|https://www.anthropic.com/claude-code|代理式代码开发
Replit Agent|开发工具|coding,automation|IT 软件与网络安全,中小微企业与个体经营|全球|SaaS|https://replit.com/|网页应用构建
Lovable|开发工具|coding,design|中小微企业与个体经营,IT 软件与网络安全|全球|SaaS|https://lovable.dev/|自然语言应用原型
Roboflow|行业应用|vision,analytics|工业制造,农业与种植,汽车与零部件|全球|云/SDK|https://roboflow.com/|视觉数据标注与模型流程
LandingAI|行业应用|vision,documents|工业制造,建筑工程与设计|全球|SaaS/企业|https://landing.ai/|工业视觉与文档AI
Siemens Industrial AI|行业应用|maintenance,simulation,forecast|工业制造,能源与电力,矿业与材料|全球|企业产品|https://www.siemens.com/en-us/company/artificial-intelligence/|工业AI、设备诊断和数字孪生
Autodesk Fusion|行业应用|design,simulation|工业制造,汽车与零部件|全球|企业SaaS|https://www.autodesk.com/products/fusion-360/overview|产品设计与制造集成
Autodesk Forma|行业应用|design,simulation,documents|建筑工程与设计|全球|企业SaaS|https://www.autodesk.com/products/forma/overview|建筑工程设计与项目智能
OpenSpace|行业应用|vision,simulation|建筑工程与设计,房地产与物业|全球|企业SaaS|https://www.openspace.ai/|现场视觉记录与项目协同
NVIDIA Omniverse|行业应用|simulation,design|工业制造,汽车与零部件,影视游戏与内容创作|全球|开发平台|https://www.nvidia.com/en-us/omniverse/|数字孪生仿真生态
Plantix|行业应用|vision,knowledge|农业与种植|全球|移动应用|https://plantix.net/|作物病害辅助识别
EOSDA Crop Monitoring|行业应用|geo,forecast|农业与种植,环境与可持续发展|全球|SaaS|https://eos.com/crop-monitoring/|农业遥感与地块监控
Google Earth Engine|研究/数据|geo,analytics|农业与种植,环境与可持续发展,能源与电力|全球|平台/API|https://earthengine.google.com/|遥感时空数据分析
Esri GeoAI|行业应用|geo,forecast|环境与可持续发展,政府与公共服务|全球|GIS/企业|https://www.esri.com/en-us/arcgis/products/arcgis/geoai|空间智能与机器学习
Abridge|行业应用|clinical,documents|医疗服务|全球|医疗企业|https://www.abridge.com/|临床对话与文书辅助
Nabla|行业应用|clinical,documents|医疗服务|全球|医疗企业|https://www.nabla.com/|临床文书辅助
Microsoft Dragon Copilot|行业应用|clinical,documents|医疗服务|全球|医疗企业|https://learn.microsoft.com/en-us/industry/healthcare/dragon-copilot/about/|临床记录草稿与临床工作流
Khanmigo|行业应用|learning,knowledge|基础教育,职业培训与企业学习|全球|教育SaaS|https://www.khanacademy.org/khan-labs|Khan Academy教学与学习AI
MagicSchool|行业应用|learning,content|基础教育|全球|教育SaaS|https://www.magicschool.ai/|教师备课与课堂辅助
Brisk Teaching|行业应用|learning,content|基础教育|全球|浏览器插件|https://www.briskteaching.com/|教师任务与教学材料辅助
Harvey|行业应用|legal,documents,research|法律服务|全球|法律企业|https://www.harvey.ai/|法律AI研究与起草平台
Thomson Reuters CoCounsel|行业应用|legal,research,documents|法律服务,会计税务与审计|全球|法律企业|https://www.thomsonreuters.com/|专业服务研究与AI协作产品入口
Qlib|研究/数据|forecast,analytics,risk|证券与资管,银行与金融服务|全球|开源代码|https://github.com/microsoft/qlib|量化投资研究框架
OpenBB|研究/数据|research,analytics|银行与金融服务,证券与资管|全球|开源/企业|https://openbb.co/|金融数据和分析工作台
FinGPT|研究/数据|research,analytics|证券与资管,银行与金融服务|全球|开源代码|https://github.com/AI4Finance-Foundation/FinGPT|金融语言模型研究生态
Salesforce Agentforce|行业应用|support,sales,automation|零售与连锁门店,保险,电商与跨境贸易|全球|企业SaaS|https://www.salesforce.com/agentforce/|企业CRM代理
HubSpot Breeze|行业应用|sales,support,content|中小微企业与个体经营,广告营销与品牌|全球|SaaS|https://www.hubspot.com/products/artificial-intelligence|营销、销售、客服AI工具
Intercom Fin|行业应用|support,knowledge|电商与跨境贸易,餐饮酒店与旅游|全球|企业SaaS|https://www.intercom.com/fin|AI 客户服务
Zendesk AI|行业应用|support,knowledge|电商与跨境贸易,电信与互联网服务|全球|企业SaaS|https://www.zendesk.com/ai/|客户支持自动化
Shopify Magic|行业应用|sales,content,support|电商与跨境贸易,零售与连锁门店|全球|SaaS|https://www.shopify.com/magic|电商经营与内容AI
Chatwoot|行业应用|support,sales|中小微企业与个体经营,电商与跨境贸易|全球|自托管/云|https://www.chatwoot.com/|开源客服协作平台
Twenty CRM|行业应用|sales,automation|中小微企业与个体经营,广告营销与品牌|全球|自托管/云|https://twenty.com/|可自托管CRM
Clay|行业应用|sales,analytics|广告营销与品牌,咨询与企业管理|全球|SaaS|https://www.clay.com/|B2B线索数据研究及工作流
Canva Magic Studio|内容/设计|content,design|*|全球|SaaS|https://www.canva.com/magic-studio/|视觉设计与AI素材
Adobe Firefly|内容/设计|content,design|*|全球|SaaS|https://firefly.adobe.com/|生成式设计与媒体素材
Runway|内容/设计|content,design|影视游戏与内容创作,媒体新闻与出版,广告营销与品牌|全球|SaaS|https://runwayml.com/|AI 视频制作
CapCut 剪映|内容/设计|content,design|*|中国/全球|桌面/手机|https://www.capcut.com/|视频剪辑与AI创作
ElevenLabs|内容/设计|content,meeting|媒体新闻与出版,影视游戏与内容创作|全球|SaaS/API|https://elevenlabs.io/|语音合成与音频工作流
HeyGen|内容/设计|content,design|广告营销与品牌,职业培训与企业学习|全球|SaaS|https://www.heygen.com/|虚拟人物视频制作
Gamma|内容/设计|content,design|咨询与企业管理,职业培训与企业学习|全球|SaaS|https://gamma.app/|演示文稿生成
Figma AI|内容/设计|design,coding|IT 软件与网络安全,广告营销与品牌|全球|SaaS|https://www.figma.com/ai/|设计、原型与产品协作
DeepL|文档工具|documents,content|*|全球|SaaS/API|https://www.deepl.com/|文本与文档翻译
Otter.ai|文档工具|meeting,documents|*|全球|SaaS|https://otter.ai/|会议转录与摘要
Fireflies.ai|文档工具|meeting,documents|*|全球|SaaS|https://fireflies.ai/|会议记录辅助
Dataiku|研究/数据|analytics,forecast,automation|*|全球|企业平台|https://www.dataiku.com/|企业数据分析与AI开发
Databricks|研究/数据|analytics,forecast,coding|*|全球|企业平台|https://www.databricks.com/|数据和ML平台
Snowflake Cortex|研究/数据|analytics,knowledge|*|全球|企业平台|https://www.snowflake.com/|企业数据平台中的AI功能
PostHog|研究/数据|analytics,sales|广告营销与品牌,IT 软件与网络安全,电商与跨境贸易|全球|SaaS/自托管|https://posthog.com/|产品分析与实验
Power BI|研究/数据|analytics,forecast|*|全球|企业SaaS|https://www.microsoft.com/en-us/power-platform/products/power-bi|数据看板与AI辅助分析
Tableau|研究/数据|analytics,forecast|*|全球|企业SaaS|https://www.tableau.com/|商业智能与数据探索
UiPath|自动化|automation,documents|会计税务与审计,保险,政府与公共服务|全球|企业平台|https://www.uipath.com/|RPA与企业工作流
SAP Business AI|行业应用|supply,forecast,analytics|工业制造,物流与仓储,能源与电力|全球|企业SaaS|https://www.sap.com/products/artificial-intelligence.html|ERP与企业AI集成
ServiceNow Now Assist|行业应用|support,automation,maintenance|IT 软件与网络安全,电信与互联网服务|全球|企业SaaS|https://www.servicenow.com/products/now-assist.html|ITSM 与服务工作流AI
Workday AI|行业应用|hr,analytics|人力资源与招聘,职业培训与企业学习|全球|企业SaaS|https://www.workday.com/|HR与企业管理AI
Promptfoo|评测/治理|security,coding,automation|*|全球|开源代码|https://www.promptfoo.dev/|LLM和Agent评测、红队测试
DeepEval|评测/治理|security,knowledge,automation|*|全球|开源代码|https://github.com/confident-ai/deepeval|LLM应用评测框架
Langfuse|评测/治理|security,analytics,automation|*|全球|自托管/云|https://langfuse.com/|Agent可观测性与追踪
Arize Phoenix|评测/治理|security,analytics,automation|*|全球|开源/云|https://phoenix.arize.com/|AI调用追踪与评测
OWASP GenAI Security|评测/治理|security,knowledge|*|全球|公益文档|https://genai.owasp.org/|LLM安全风险参考
NIST AI RMF|评测/治理|security,risk|*|全球|政策框架|https://www.nist.gov/itl/ai-risk-management-framework|跨行业AI风险管理框架
IBM Maximo|行业应用|maintenance,analytics,forecast|工业制造,汽车与零部件,房地产与物业,能源与电力,矿业与材料|全球|企业SaaS|https://www.ibm.com/products/maximo|资产运维、设备监测与维护管理候选（官方产品资料）
o9 Solutions|行业应用|supply,forecast,analytics|工业制造,汽车与零部件,零售与连锁门店,物流与仓储|全球|企业SaaS|https://o9solutions.com/solutions/supply-chain-planning|供应链需求与供给规划候选（官方产品资料）
MindBridge|行业应用|risk,analytics|会计税务与审计,银行与金融服务|全球|企业SaaS|https://www.mindbridge.ai/|财务异常检索与风险分析候选（官方产品资料）
Esri ArcGIS|行业应用|geo,analytics,vision|农业与种植,环境与可持续发展,矿业与材料|全球|企业SaaS|https://www.esri.com/en-us/arcgis/geospatial-platform/overview|地理信息与空间分析候选（官方产品资料）
Palantir AIP|行业应用|automation,analytics,knowledge,supply|工业制造,能源与电力,物流与仓储,汽车与零部件|全球|企业平台|https://www.palantir.com/platforms/aip|企业业务数据与AI工作流平台候选（官方产品资料）
V7 Go|行业应用|documents,knowledge,automation|法律服务,制药与生物科技,保险|全球|企业SaaS|https://www.v7labs.com/go|知识中心、文件与工作流代理候选（官方产品资料）'''
SKILLS='''ai-workflow-diagnosis|AI 工作流程体检|automation,analytics|识别适合 AI 处理但可撤回的高频流程|岗位说明、流程步骤、每月次数、单次耗时、错误及数据类别|画出原流程;记录人工作业与决策点;把步骤分成只读/草稿/审批/写入;建立优先级和基线|瓶颈矩阵、试点优先级、RACI、30天计划|处理时间/错误率/成本|不访问生产系统；未经业务Owner批准不作写操作
source-grounded-rag|有来源的知识库问答|knowledge,documents|让回答返回对应来源和不足证据标记|授权文档、版本、问题样本、标准答案|检查授权和隐私;清洗并标记文件页码;建立检索与引用;以负例测试拒答;人工抽样核对|引用式问答规范、误答样本、失效条件|引用准确率/拒答合理率|禁止臆造来源；不把机密资料发到未经批准的云
contract-review-draft|合同条款差异初审|legal,documents|辅助专业人员定位条款差异而非出具法律意见|两个合同版本、司法辖区、条款清单|文本提取与页码锁定;比对义务/日期/金额;列出异常与引用;标记不能确认处;交给律师复核|对照表、差异项、出处与待核问句|漏检率/人工复核时间|不得形成自动法律意见或签约动作
clinical-document-draft|临床记录草稿检查|clinical,documents|协助专业人员审阅记录而非诊断|经许可且脱敏的病例示例、标准模板|检查保密与最小必要;按模板整理语音/文字;追溯原始记录;标记模糊药物剂量;由临床人员签发|病历草稿、待确认项目、审查日志|医生更正率/文书时间|不提供独立诊断、用药或治疗决定
lesson-design-review|差异化课程设计|learning,content|帮助教师针对不同水平制作经过审查的教学练习|课程目标、学段、教材授权、学生能力范围|识别教学目标;生成难度分层任务;给出解析和可能错因;教师校验;设计学习效果测量|教案、难度梯度、评分准则|知识掌握度/批改时间|不上传未成年人识别信息；教师负责最终教学
research-evidence-map|研究证据矩阵|research,knowledge|可追溯整理观点、论文与反例|研究问题、允许的文献来源、纳排标准|固定查询策略;记录每个来源及日期;抽取研究设计和限制;辨识相互矛盾证据;列出研究空白|文献矩阵、证据等级、未解决问题|来源核验率/复现率|禁止杜撰 DOI、作者、研究结论
service-triage|客服分流与人工升级|support,automation|将常见问答自动分类并安全转人工|FAQ、工单标签、人工升级阈值|设置分类标签;用合成样本测试意图;高风险提问直接转人工;记录失败案例;建立定期更新|分类规则、标准回答草稿、升级策略|首响时间/误分流率|不自动退款、承诺、索取敏感资料
consent-lead-triage|合规线索登记与CRM分流|sales,automation|只处理已授权的线索和后续跟进建议|自愿提交的线索、用途同意、撤回机制|校验同意和数据来源;去重;按需求标签路由;生成待审回复;保留撤回和删除流程|客户需求分类、草稿、审查与撤回记录|线索质量/撤回响应时间|禁止抓取私人邮箱、未经授权群发或伪装身份
marketing-test-design|内容实验与转化测量|content,analytics|为营销素材制定可验证的内容实验|受众需求、品牌约束、渠道规则、预算上限|明确假设与指标;产出不同文案草稿;检查真实性与版权;随机实验;记录结果和不确定性|活动计划、原创素材建议、实验表|转化率/CAC/投诉率|不伪造评价，不进行暗中数据采集
predictive-maintenance-pilot|设备维护异常监测试点|maintenance,forecast|在不接管设备控制的前提下评测维护预警|历史传感器、维修工单、设备手册|脱敏数据清理;锁定训练和未来时段;建立基线预测;测试漏报/误报;由工程师审核告警|异常样本、模型对比、告警流程|误报率/提前预警时长|不得自动改变工业控制参数
visual-inspection-evaluation|工业视觉质检评测|vision,analytics|以有标签图片验证视觉质检模型|经授权的训练与独立测试图像、缺陷标准|分类缺陷类型;按批次/时间分割样本;评估精确率和召回;关注罕见重大缺陷;记录人工复判|缺陷标签表、混淆矩阵、失败案例|漏检率/人工复判时长|不因模型分数替代安全检验标准
ai-pilot-roi-audit|AI试点成本效益审计|analytics,risk|区别演示效果和实际可复制收益|原流程用时、成本、质量、试点日志、人工复核耗时|计算基线;核实模型与维护费用;加入返工及错误成本;做敏感性分析;明确因果识别限制|ROI区间、指标口径、风险登记簿|净节省时间/全成本/错误率|无对照证据时不承诺ROI
agent-permission-review|Agent 权限与安全审查|security,automation|在实施前检查 Agent、Skills、MCP 的真实权限|候选技能清单、依赖、触发器、敏感资源|检查作者与许可证;列出读写权限;运行隔离恶意输入测试;验证人工审批;制定中止与回滚步骤|权限矩阵、负面测试、上线门槛|越权率/无授权调用次数|不得默认授予密钥、终端、支付或生产写入权限
audit-ready-financial-research|可审计金融研究简报|research,risk|用可复核证据形成金融研究简报草稿|公开财报、数据截面、日期、假设|记录来源与访问时间;抽取结构化事实;区分事实和预测;检查滞后与幸存者偏差;由专业人士审阅|研究简报、假设/证据表、风险说明|事实准确率/来源完整率|不构成投资建议或交易执行指令'''
SOURCES=[
 ('McKinsey 2026 AI Survey','行业与职能的Agent扩展差异','https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai'),
 ('Microsoft Work Trend Index 2026','工作重构、人机协同与评测','https://www.microsoft.com/en-us/worklab/work-trend-index/agents-human-agency-and-the-opportunity-for-every-organization'),
 ('NIST AI RMF','跨行业AI风险治理','https://www.nist.gov/itl/ai-risk-management-framework'),
 ('WHO 大模型医疗治理','医疗AI专业审查与患者安全','https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models'),
 ('UNESCO 教师AI能力框架','教师AI能力要求','https://www.unesco.org/zh/articles/ai-competency-framework-teachers?hub=66370'),
 ('MCP Registry','官方MCP注册目录（收录不代表安全审计）','https://registry.modelcontextprotocol.io/'),
 ('Agent Skills 标准','可移植技能标准','https://agentskills.io/'),
 ('Siemens Industrial AI','工业AI产品及方向','https://www.siemens.com/en-us/company/artificial-intelligence/'),
 ('Autodesk Forma AI','建筑工程AI场景','https://construction.autodesk.com.au/workflows/artificial-intelligence-construction/'),
 ('Microsoft Copilot Studio Docs','企业Agent设计、发布与治理','https://learn.microsoft.com/en-us/microsoft-copilot-studio/'),
 ('Thomson Reuters专业服务调查','法律、税务和审计的AI采用','https://www.thomsonreuters.com/'),
 ('Abridge','临床文书产品官方资料','https://www.abridge.com/'),
 ('YIFALIN AI Capability Atlas','已有5,000条目录索引与研究档案','https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin'),
]
scenarios=[]
for line in SCENARIOS.splitlines():
 s=line.split('|'); assert len(s)==3, line
 scenarios.append(dict(id=s[0],name=s[1],tip=s[2]))
ids={s['id'] for s in scenarios}
sectors=[]
for ix,line in enumerate(SECTORS.splitlines()):
 v=line.split('|'); assert len(v)==10,(len(v),line)
 name,group,roles,pain,quick,mid,future,kpi,risk,tags=v
 ts=tags.split(',');assert set(ts)<=ids, (name,set(ts)-ids)
 sectors.append(dict(id=f's{ix+1:02d}',name=name,group=group,roles=roles,pain=pain,quick=quick,mid=mid,future=future,kpi=kpi,risk=risk,scenarios=ts))
tools=[]
for ix,line in enumerate(TOOLS.splitlines()):
 v=line.split('|'); assert len(v)==8,(len(v),line)
 name,kind,tags,applies,region,deployment,url,desc=v
 ts=tags.split(',');assert set(ts)<=ids,(name,set(ts)-ids)
 industry=[] if applies=='*' else applies.split(',')
 assert all(n in [s['name'] for s in sectors] for n in industry),(name,industry)
 assert url.startswith('https://'),(name,url)
 tools.append(dict(id=f't{ix+1:03d}',name=name,type=kind,scenarios=ts,industries=industry,region=region,deployment=deployment,url=url,desc=desc,source=('2026-11-01 官方产品页面核验' if name in {'IBM Maximo','o9 Solutions','MindBridge','Esri ArcGIS','Palantir AIP','V7 Go'} else '官方主页或公开维护仓库'),review='产品入口存在／未进行业务实测' if name in {'IBM Maximo','o9 Solutions','MindBridge','Esri ArcGIS','Palantir AIP','V7 Go'} else '初步收录／未实测'))
assert len({x['url'] for x in tools})==len(tools), 'duplicate urls'
assert len({x['name'] for x in tools})==len(tools),'duplicate names'
skills=[]
for line in SKILLS.splitlines():
 x=line.split('|'); assert len(x)==9,(len(x),line)
 slug,title,tags,goal,inputs,steps,outputs,metric,gate=x
 assert set(tags.split(','))<=ids
 skills.append(dict(id='skill-'+slug,slug=slug,name=title,scenarios=tags.split(','),goal=goal,inputs=inputs,steps=steps.split(';'),outputs=outputs,metric=metric,gate=gate,status='第一方草案 / 未在业务环境执行'))
SKROOT=ROOT/'skills';SKROOT.mkdir(exist_ok=True)
for skill in skills:
 folder=SKROOT/skill['slug'];folder.mkdir(exist_ok=True)
 body=f"""---
name: {skill['slug']}
description: {skill['goal']}
---

# {skill['name']}

**状态：** 第一次发布的工作流模板；未验证具体生产系统。不自动调用外部工具。

## 目标
{skill['goal']}

## 授权输入
{skill['inputs']}

## 步骤
"""+''.join(f'{i}. {step}\n' for i,step in enumerate(skill['steps'],1))+f"""
## 交付物
{skill['outputs']}

## 验收指标
{skill['metric']}

## 人工审批 / 风险门槛
{skill['gate']}

## 执行约束
只在明确授权的数据、工具与环境中工作；输出包含来源、限制、待确认事项；任何外部写入或高风险操作先审批；不得宣称未执行过的真实测试已通过。
"""
 (folder/'SKILL.md').write_text(body,encoding='utf-8')
dataset={'as_of':STAMP,'version':'1.0.0','sectors':sectors,'scenarios':scenarios,'tools':tools,'first_party_skills':skills,'sources':[{'name':s[0],'desc':s[1],'url':s[2]} for s in SOURCES]}
(ROOT/'data.json').write_text(json.dumps(dataset,ensure_ascii=False,indent=2),encoding='utf-8')
# Explicit, joinable knowledge graph: industry, role, scenario, tool and relations.
roles=[]; links=[]
for sec in sectors:
 for label in sec['roles'].split('、'):
  rid='role-'+str(len(roles)+1).zfill(3)
  roles.append({'id':rid,'name':label,'sector_id':sec['id'],'sector':sec['name']})
  links.append({'source':sec['id'],'target':rid,'relation':'HAS_ROLE','evidence':'editorial'})
 for sid in sec['scenarios']:
  links.append({'source':sec['id'],'target':sid,'relation':'RELEVANT_SCENARIO','evidence':'editorial'})
for tool in tools:
 for sid in tool['scenarios']:
  links.append({'source':tool['id'],'target':sid,'relation':'SUPPORTS_SCENARIO','evidence':'editorial'})
 for name in tool['industries']:
  sec=next(s for s in sectors if s['name']==name)
  links.append({'source':tool['id'],'target':sec['id'],'relation':'INDUSTRY_SPECIFIC_CANDIDATE','evidence':'editorial'})
for sk in skills:
 for sid in sk['scenarios']:
  links.append({'source':sk['id'],'target':sid,'relation':'SKILL_TEMPLATE_FOR','evidence':'draft'})
nodes=([{'id':s['id'],'type':'industry','name':s['name']} for s in sectors]
 + [{'id':t['id'],'type':'tool','name':t['name'],'url':t['url']} for t in tools]
 + [{'id':s['id'],'type':'scenario','name':s['name']} for s in scenarios]
 + [{'id':r['id'],'type':'role','name':r['name']} for r in roles]
 + [{'id':sk['id'],'type':'skill-template','name':sk['name']} for sk in skills])
ids_all={n['id'] for n in nodes}
assert len(ids_all)==len(nodes)
assert all(e['source'] in ids_all and e['target'] in ids_all for e in links)
(ROOT/'graph.json').write_text(json.dumps({'as_of':STAMP,'nodes':nodes,'edges':links},ensure_ascii=False,indent=2),encoding='utf-8')
for name,records,columns in [('roles.csv',roles,['id','name','sector_id','sector']),('edges.csv',links,['source','target','relation','evidence'])]:
 with (ROOT/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(records)

for name,rows,cols in [('industries.csv',sectors,['id','name','group','roles','pain','quick','mid','future','kpi','risk','scenarios']),('tools.csv',tools,['id','name','type','scenarios','industries','region','deployment','url','desc','review'])]:
 with (ROOT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader()
  for row in rows:w.writerow({k:(', '.join(row[k]) if isinstance(row.get(k),list) else row.get(k,'')) for k in cols})
TEMPLATE=r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="全行业AI转型图谱：行业方案、工具导航、Skills、Agents、知识库、工作流和实施路线"><title>AI 时代 · 全行业转型图谱 | YIFALIN Atlas</title>
<style>
:root{--bg:#080d19;--panel:#101a2b;--panel2:#15243a;--line:#283b57;--text:#e9f1ff;--muted:#a3b7d0;--teal:#56dfca;--blue:#77adff;--orange:#f5bf74;--radius:17px;--shadow:0 14px 50px #0004}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 8% 0%,#142a42 0,transparent 42%),linear-gradient(135deg,#070d19,#09121e);font:15px/1.62 system-ui,-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:var(--text);min-height:100vh}a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}button,select,input{font:inherit}button{cursor:pointer}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{outline:2px solid var(--teal);outline-offset:2px}header{border-bottom:1px solid var(--line);background:#080f1cdd;backdrop-filter:blur(14px);position:sticky;top:0;z-index:20}.head{max-width:1440px;margin:auto;display:flex;align-items:center;justify-content:space-between;padding:12px 24px;gap:12px}.brand{font-size:16px;letter-spacing:.4px;font-weight:800;white-space:nowrap}.brand em{color:var(--teal);font-style:normal}.topnav{display:flex;gap:4px;overflow:auto}.topnav button{background:none;color:var(--muted);border:0;border-radius:9px;padding:9px 12px;white-space:nowrap}.topnav button.active{background:#24435a;color:var(--teal)}.topnav button:hover{background:#192d46}main{max-width:1440px;padding:0 24px 65px;margin:auto}.hero{padding:54px 0 28px;display:grid;grid-template-columns:1.5fr .8fr;align-items:center;gap:32px}.eyebrow{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:var(--teal);font-weight:700}.hero h1{font-size:clamp(34px,4vw,56px);line-height:1.19;letter-spacing:-1px;margin:12px 0}.hero h1 span{color:var(--teal)}.lead{color:var(--muted);max-width:790px;font-size:16px}.hero-info{background:linear-gradient(140deg,#1c344e,#101b30);padding:23px;border:1px solid #37617c;border-radius:21px;box-shadow:var(--shadow)}.hero-info .stat{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid #36506b;padding:8px 0}.stat:last-child{border:0}.stat strong{font-size:27px;color:#e6fcfa}.stat small{color:var(--muted)}.hint{font-size:12px;color:var(--muted)}.controls{background:#101b2cee;border:1px solid var(--line);padding:18px;display:grid;grid-template-columns:2fr repeat(3,1fr) auto;gap:10px;border-radius:18px;align-items:end}.control label{display:block;color:#b5cadf;font-size:12px;padding-bottom:5px}.control input,.control select{width:100%;background:#0a1424;color:var(--text);border:1px solid #324965;border-radius:10px;padding:11px 11px;min-height:45px}.button{background:#16384a;color:#d7fefa;border:1px solid #296477;padding:10px 14px;border-radius:11px;font-weight:650}.button:hover{background:#245568}.button.primary{background:#3ac6aa;color:#082621;border-color:transparent}.button.secondary{background:#17253a;color:var(--text);border-color:var(--line)}.button.danger{background:#52353a;border-color:#6d4a51}.button:disabled{opacity:.45;cursor:not-allowed}.actions{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.section-top{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:30px 0 15px}.section-top h2{font-size:24px;margin:0}.small{font-size:12px;color:var(--muted)}.tag{display:inline-block;padding:2px 9px;border:1px solid #315068;background:#13283c;border-radius:999px;font-size:11px;color:#b7e7ef;margin:3px 4px 1px 0}.tag.warm{color:#f8cf8b;border-color:#755b37;background:#32281f}.tag.green{color:#78e6c4;border-color:#276d60;background:#143d39}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.card{background:linear-gradient(165deg,#122038,#0f1929);border:1px solid var(--line);border-radius:16px;padding:20px;display:flex;flex-direction:column;min-height:190px;box-shadow:0 9px 25px #0001}.card:hover{border-color:#447b87}.card h3{font-size:18px;line-height:1.38;margin:0 0 9px}.card h3 a{color:var(--text)}.card p{margin:3px 0;color:#bacbde}.meta{font-size:12px;color:#96b5d0}.card .foot{margin-top:auto;padding-top:14px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}.card .foot .button{font-size:12px;padding:7px 10px}.card .summary{font-size:13px;margin-top:4px}.card .insight{background:#172b40;padding:10px 12px;border-left:3px solid var(--teal);border-radius:7px;font-size:13px;margin:8px 0;color:#cce1f2}.tabs-panels>section[hidden]{display:none!important}.pillrow{display:flex;gap:5px;flex-wrap:wrap;margin:10px 0}.chip{border:1px solid #34516c;border-radius:999px;background:#122b40;padding:6px 10px;font-size:12px;color:#c0d8eb}.chip.active{background:#1f615c;color:#ddfff8;border-color:#46a796}.notice{border:1px solid #4b5373;background:#1c2439;color:#bdcde0;padding:13px 17px;border-radius:12px;font-size:12px;margin:20px 0}.notice strong{color:#e6d29e}.empty{padding:45px;text-align:center;color:var(--muted);border:1px dashed #3b556d;border-radius:16px}.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:14px;max-height:650px}.matrix{border-collapse:collapse;width:max-content;min-width:100%;font-size:12px}.matrix th,.matrix td{padding:7px 8px;text-align:center;border:1px solid #243750}.matrix th{position:sticky;top:0;background:#1b2a40;z-index:2;white-space:nowrap}.matrix th:first-child,.matrix td:first-child{position:sticky;left:0;background:#122138;text-align:left;min-width:155px;z-index:1}.matrix th:first-child{z-index:3}.cell{border:0;width:30px;height:30px;border-radius:7px;font-weight:700}.cell.hit{background:#15564f;color:#84f6db}.cell.none{background:#142337;color:#5c7892}.cell.hit:hover{background:#27857a}.two-cols{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{background:#112038;border:1px solid var(--line);border-radius:16px;padding:22px}.panel h3{margin-top:0}.planner{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}.planner label{font-size:12px;color:var(--muted)}.planner select,.planner input{display:block;width:100%;margin-top:5px;background:#0a1628;color:#fff;border:1px solid #38526f;border-radius:9px;padding:10px}.roadmap{display:grid;gap:12px}.step{padding:12px 16px;border-left:3px solid #4dcaba;background:#192d43;border-radius:8px}.step b{color:#7febe0}.step p{margin:4px 0;color:#b6cee4}.toolmini{font-size:12px;color:#9cccf1}.kv{padding:9px 0;border-bottom:1px solid #28435b}.kv:last-child{border:0}.kv b{display:block;color:#83dccc;font-size:12px}.modal{position:fixed;inset:0;background:#050914e9;z-index:50;display:none;align-items:center;justify-content:center;padding:20px}.modal.open{display:flex}.modal-content{width:min(760px,100%);max-height:90vh;overflow:auto;background:#122139;border:1px solid #416277;border-radius:17px;box-shadow:var(--shadow);padding:26px}.modal-top{display:flex;justify-content:space-between;gap:15px;align-items:start}.modal-top h2{margin:0;font-size:25px}.modal .x{border:1px solid #435e7a;background:#1e3046;color:#fff;padding:4px 11px;border-radius:8px;font-size:22px}footer{border-top:1px solid var(--line);padding:30px 24px 50px;text-align:center;color:var(--muted);font-size:12px}.source-links{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.source-links a{padding:13px;background:#13243b;border:1px solid #2d4562;border-radius:12px;display:block}.source-links a span{display:block;color:var(--muted);font-size:12px}.statusbar{margin:13px 0;color:var(--muted);font-size:12px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}.callout{font-size:13px;background:#172a40;border-radius:10px;padding:13px;color:#d3e6ef}#toast{position:fixed;right:20px;bottom:18px;padding:12px 19px;background:#2b5e65;color:#fff;border-radius:12px;display:none;z-index:99;max-width:85vw}@media(max-width:1120px){.controls{grid-template-columns:2fr 1fr 1fr}.controls>:last-child{grid-column:1/-1}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:760px){main{padding:0 14px 55px}.head{flex-direction:column;align-items:stretch;padding:8px 12px}.topnav{justify-content:space-between}.topnav button{font-size:12px;padding:8px}.hero{grid-template-columns:1fr;padding:28px 0 18px;gap:10px}.hero h1{font-size:32px}.controls{grid-template-columns:1fr 1fr;padding:12px}.controls .control:first-child{grid-column:1/-1}.grid,.two-cols,.source-links{grid-template-columns:1fr}.planner{grid-template-columns:1fr}.card{min-height:unset;padding:16px}.section-top h2{font-size:20px}.hero-info{padding:13px}.modal-content{padding:17px}}
</style></head><body>
<header><div class="head"><div class="brand">◈ <em>YIFALIN</em> · ALL INDUSTRY AI ATLAS</div><nav class="topnav" aria-label="主导航"><button data-tab="industries" class="active">行业方案</button><button data-tab="tools">工具导航</button><button data-tab="skills">任务 Skills</button><button data-tab="matrix">交叉图谱</button><button data-tab="plan">落地路线</button><button data-tab="sources">来源与说明</button></nav></div></header>
<main><div class="hero"><div><div class="eyebrow">Future of Work · Human + AI + Agents</div><h1>找出你所在行业的<br><span>AI 时代新工作方式</span></h1><p class="lead">不只告诉你有什么工具，更从岗位、痛点和业务流程出发，连接知识库、Skills、Agents、行业软件和实施方案。支持中文/英文关键词、交叉筛选、收藏、导出与行业定制路线。</p><div class="actions"><button class="button primary" id="jumpTools">探索工具 →</button><button class="button secondary" id="jumpPlan">生成行业路线图</button><span class="small">资料基线：<span id="stamp"></span> · 离线可用 · 无追踪代码</span></div></div><aside class="hero-info"><div class="stat"><small>覆盖行业</small><strong id="sectorN"></strong></div><div class="stat"><small>首批工具 / 标准 / 资源</small><strong id="toolN"></strong></div><div class="stat"><small>跨行业 AI 场景</small><strong id="scenarioN"></strong></div><p class="hint">首批人工策划的入口与研究假设，不代表完成逐个产品实测、付费许可审查或效果验证。</p></aside></div>
<div class="controls" role="search"><div class="control"><label for="q">输入行业、职业、痛点、工具名或关键词</label><input id="q" type="search" placeholder="例如：教师 / 投研 / 质检 / 预算 / 法律 / Agent / RAG"></div><div class="control"><label for="industryFilter">行业</label><select id="industryFilter"><option value="">全部行业</option></select></div><div class="control"><label for="scenarioFilter">工作场景</label><select id="scenarioFilter"><option value="">全部场景</option></select></div><div class="control"><label for="typeFilter">资源类型</label><select id="typeFilter"><option value="">全部类型</option></select></div><button class="button secondary" id="reset">重置筛选</button></div>
<div class="statusbar"><span id="summary">加载中…</span><div class="actions"><label><input id="onlyFavorites" type="checkbox"> 仅看我的收藏</label><button id="exportCsv" class="button secondary">导出当前结果 CSV</button><button id="exportJson" class="button secondary">导出 JSON</button></div></div>
<div class="notice"><strong>证据等级提示：</strong>官方链接仅表明有对应产品或资料入口。适用行业、实施机会、未来突破口是编辑研究判断；未逐个核验当日可用性、收费、合规许可或真实 ROI。医疗、法律、金融、公共行政和关键基础设施保持人工决策。</div>
<div class="tabs-panels"><section id="tab-industries"><div class="section-top"><div><h2>行业转型方案</h2><span class="small">点击行业查看岗位、三阶段路径、风险与匹配工具</span></div><span id="industryCount" class="small"></span></div><div id="sectorCards" class="grid"></div></section>
<section id="tab-tools" hidden><div class="section-top"><div><h2>AI 工具 / Skills / Agent 资源导航</h2><span class="small">分类、适用工作流、部署形态及官方链接</span></div><span id="toolCount" class="small"></span></div><div id="toolCards" class="grid"></div></section>
<section id="tab-skills" hidden><div class="section-top"><div><h2>可复用行业工作 Skills（第一方草案）</h2><span class="small">每个模板包含输入、步骤、交付物、验收与人工审批门槛；不是已执行的 Agent</span></div><span class="small" id="skillCount"></span></div><div class="grid" id="skillCards"></div></section><section id="tab-matrix" hidden><div class="section-top"><div><h2>行业 × AI 场景交叉矩阵</h2><span class="small">点击亮起的格子同时筛选行业与场景；对应编辑适用性，不是技术验证</span></div></div><div class="tablewrap"><table id="matrixTable" class="matrix"></table></div><div class="two-cols" style="margin-top:20px"><div class="panel"><h3>高复用场景</h3><div id="scenarioBars"></div></div><div class="panel"><h3>如何解读跨行业共性</h3><p class="small">同一个能力可跨不同行业复用：例如文档抽取在保险理赔、法务合同、工程招投标都可使用，但数据规范、质量阈值和审批权不同。平台应该复用技术积木，同时保留行业专用的证据、规则和专业审核。</p><p class="small">矩阵以每个行业编辑给出的核心 5 个场景构建，并非衡量工具成熟度或自动化可行性。</p></div></div></section>
<section id="tab-plan" hidden><div class="section-top"><div><h2>4 周试点 → 90 天扩展 → 未来创新</h2><span class="small">本地根据所选行业生成行动清单；不上传你的输入</span></div></div><div class="two-cols"><div class="panel"><h3>告诉系统你的起点</h3><div class="planner"><label>行业<select id="planIndustry"></select></label><label>主要目标<select id="planGoal"><option value="time">节省人力时间</option><option value="quality">降低错误 / 改善质量</option><option value="growth">增长 / 获客</option><option value="knowledge">建设组织知识库</option><option value="innovation">探索新产品 / 商业模式</option></select></label><label>团队规模<select id="planSize"><option value="solo">个人 / 1-5 人</option><option value="smb">6-100 人</option><option value="enterprise">100 人以上</option></select></label><label>数据敏感程度<select id="planData"><option value="public">公开资料 / 合成数据</option><option value="internal">一般内部业务资料</option><option value="regulated">个人敏感信息 / 强监管数据</option></select></label></div><div class="actions" style="margin-top:16px"><button class="button primary" id="generate">生成实施建议</button><button class="button secondary" id="downloadPlan">下载 Markdown 路线图</button></div><p class="small">原则：先选 KPI 与验证样本，再选工具；先只读/草稿与人工审核，再引入写操作。</p></div><div class="panel" id="planOutput"><p class="small">选择行业与目标，点击生成后显示每周任务、适用工具、衡量指标、风险闸门与下一阶段方向。</p></div></div></section>
<section id="tab-sources" hidden><div class="section-top"><div><h2>研究来源与证据边界</h2><span class="small">优先官方研究、官方文档、开源上游；每个产品可跳转原始网址</span></div></div><div class="panel"><h3>来源导航</h3><div class="source-links" id="sourceLinks"></div></div><div class="two-cols" style="margin-top:16px"><div class="panel"><h3>信息成熟度</h3><div class="kv"><b>收录 / Indexed</b>有网址、名称、分类；不等于安装通过。</div><div class="kv"><b>研究 / Researched</b>有应用推演与候选 KPI；不等于真实应用。</div><div class="kv"><b>试点 / Piloted</b>应有样本、成本、错误率、对照实验与审批记录；本批尚未完成。</div><div class="kv"><b>生产 / Production</b>需法律许可、权限、监控、回滚和实际运营验收；本批没有此认证。</div></div><div class="panel"><h3>可持续建设建议</h3><p>每个资源应维护：规范 URL、开发者/供应商、功能标签、行业适用性、来源、最近核验时间、权限需求、许可/收费、可复现案例、负面测试和维护人。</p><p>对于热门第三方 Skills、MCP、Agent，收录与执行严格分离；先隔离评测，再依据最小权限进行接入。</p><p class="small">该页面为原型静态快照，不会抓取你设备上的文件，不会自动连接第三方账号或安装技能。</p></div></div></section></div></main>
<div class="modal" id="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle"><div class="modal-content"><div class="modal-top"><h2 id="modalTitle"></h2><button class="x" id="modalClose" aria-label="关闭详情">×</button></div><div id="modalBody"></div></div></div>
<div id="toast" role="status"></div><footer>YIFALIN AI Capability Atlas · 全行业转型研究版 V1.0 · 2026-11-01<br>研究推演 ≠ 已验证商业收益 · 不提供医疗、法律、投资或关键设施自动决策建议</footer>
<script id="atlasData" type="application/json">__DATA__</script><script>
'use strict';
const D=JSON.parse(document.querySelector('#atlasData').textContent);
const SC=Object.fromEntries(D.scenarios.map(x=>[x.id,x]));
const $=q=>document.querySelector(q), $$=q=>Array.from(document.querySelectorAll(q));
let tab='industries', currentPlan='', lastFocus=null;
let state={query:'',industry:'',scenario:'',type:'',favorites:false};
const norm=v=>String(v||'').toLowerCase().normalize('NFKC').replace(/\s+/g,'');
let fallbackFav=[];const getFav=()=>{try{return JSON.parse(localStorage.getItem('industry-atlas-favorites-v1')||'[]')}catch{return fallbackFav}};
const saveFav=a=>{fallbackFav=a;try{localStorage.setItem('industry-atlas-favorites-v1',JSON.stringify(a))}catch{showToast('收藏仅在当前页面有效：浏览器禁用本地存储')}};
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const isSafe=u=>{try{return new URL(u).protocol==='https:'}catch{return false}};
const link=(url,label)=>isSafe(url)?`<a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(label||'打开来源')} ↗</a>`:'';
const tags=items=>items.map(k=>`<span class="tag">${escapeHTML(SC[k]?.name||k)}</span>`).join('');
const sectorById=id=>D.sectors.find(x=>x.id===id);
const matchSector=s=>{const q=norm(state.query);return(!state.industry||s.name===state.industry)&&(!state.scenario||s.scenarios.includes(state.scenario))&&(!q||norm([s.name,s.group,s.roles,s.pain,s.quick,s.mid,s.future,s.kpi,...s.scenarios.map(k=>SC[k].name)].join(' ')).includes(q))&&(!state.favorites||getFav().includes(s.id));};
const matchTool=t=>{let industry=state.industry ? D.sectors.find(s=>s.name===state.industry) : null;let q=norm(state.query);return(!state.type||t.type===state.type)&&(!state.scenario||t.scenarios.includes(state.scenario))&&(!industry||t.industries.includes(industry.name)||(!t.industries.length&&t.scenarios.some(k=>industry.scenarios.includes(k))))&&(!q||norm([t.name,t.type,t.desc,t.region,t.deployment,t.industries.join(' '),...t.scenarios.map(k=>SC[k].name)].join(' ')).includes(q))&&(!state.favorites||getFav().includes(t.id));};
const toolScore=(t,s)=>t.scenarios.filter(k=>s.scenarios.includes(k)).length*2+(t.industries.includes(s.name)?7:0)+(t.industries.length===0?1:0);
function bestTools(s,n=7){return D.tools.filter(t=>t.scenarios.some(k=>s.scenarios.includes(k))&&(t.industries.length===0||t.industries.includes(s.name))).sort((a,b)=>toolScore(b,s)-toolScore(a,s)||a.name.localeCompare(b.name)).slice(0,n)}
const matchSkill=sk=>{const q=norm(state.query);return(!state.scenario||sk.scenarios.includes(state.scenario))&&(!q||norm([sk.name,sk.goal,sk.inputs,sk.outputs,sk.metric,sk.steps.join(' '),...sk.scenarios.map(k=>SC[k].name)].join(' ')).includes(q))&&(!state.favorites||getFav().includes(sk.id))&&(!state.industry||sk.scenarios.some(k=>D.sectors.find(s=>s.name===state.industry)?.scenarios.includes(k)))};
const byType=()=>[...new Set(D.tools.map(x=>x.type))].sort();
function setup(){D.sectors.forEach(s=>{$('#industryFilter').add(new Option(s.name,s.name));$('#planIndustry').add(new Option(s.name,s.id))});D.scenarios.forEach(s=>$('#scenarioFilter').add(new Option(s.name,s.id)));byType().forEach(t=>$('#typeFilter').add(new Option(t,t)));$('#sectorN').textContent=D.sectors.length;$('#toolN').textContent=D.tools.length;$('#scenarioN').textContent=D.scenarios.length;$('#stamp').textContent=D.as_of;$$('[data-tab]').forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.tab)));$('#jumpTools').onclick=()=>switchTab('tools');$('#jumpPlan').onclick=()=>switchTab('plan');$('#q').oninput=e=>{state.query=e.target.value;render()};$('#industryFilter').onchange=e=>{state.industry=e.target.value;render()};$('#scenarioFilter').onchange=e=>{state.scenario=e.target.value;render()};$('#typeFilter').onchange=e=>{state.type=e.target.value;render()};$('#onlyFavorites').onchange=e=>{state.favorites=e.target.checked;render()};$('#reset').onclick=()=>{state={query:'',industry:'',scenario:'',type:'',favorites:false};$('#q').value='';$('#industryFilter').value='';$('#scenarioFilter').value='';$('#typeFilter').value='';$('#onlyFavorites').checked=false;render()};$('#exportCsv').onclick=()=>exportCurrent('csv');$('#exportJson').onclick=()=>exportCurrent('json');$('#generate').onclick=generatePlan;$('#downloadPlan').onclick=()=>{if(!currentPlan)generatePlan();download('all-industry-ai-roadmap.md',currentPlan,'text/markdown;charset=utf-8')};$('#modalClose').onclick=closeModal;$('#modal').onclick=e=>{if(e.target.id==='modal')closeModal()};document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});$('#sectorCards').addEventListener('click',handleCards);$('#toolCards').addEventListener('click',handleCards);$('#skillCards').addEventListener('click',handleCards);$('#matrixTable').addEventListener('click',e=>{let c=e.target.closest('[data-si]');if(!c)return;let s=sectorById(c.dataset.si);state.industry=s.name;state.scenario=c.dataset.sc;$('#industryFilter').value=s.name;$('#scenarioFilter').value=c.dataset.sc;switchTab('tools')});fillSources();renderMatrix();render()}
function switchTab(t){tab=t;$$('[data-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.tab===t);b.setAttribute('aria-current',b.dataset.tab===t?'page':'false')});$$('[id^="tab-"]').forEach(x=>x.hidden=x.id!==`tab-${t}`);render();document.querySelector('main').scrollIntoView({behavior:'smooth',block:'start'})}
function favButton(id){return `<button class="button secondary" data-fav="${id}" aria-label="收藏或取消收藏">${getFav().includes(id)?'★ 已收藏':'☆ 收藏'}</button>`}
function handleCards(e){const f=e.target.closest('[data-fav]');if(f){const a=getFav(),idx=a.indexOf(f.dataset.fav);if(idx<0)a.push(f.dataset.fav);else a.splice(idx,1);saveFav(a);render();return}let b=e.target.closest('[data-detail]');if(b)openDetail(b.dataset.detail)}
function render(){const ss=D.sectors.filter(matchSector),ts=D.tools.filter(matchTool);const ssks=D.first_party_skills.filter(matchSkill);$('#summary').textContent=`当前：${ss.length} 个行业方案 · ${ts.length} 个工具/资源 · ${ssks.length} 个 Skills 模板 · 收藏 ${getFav().length} 项`;$('#skillCount').textContent=`${ssks.length} / ${D.first_party_skills.length}`;$('#skillCards').innerHTML=ssks.length?ssks.map(sk=>`<article class=\"card\"><div class=\"meta\">第一方工作流草案 · ${escapeHTML(sk.scenarios.map(k=>SC[k].name).join(' / '))}</div><h3>${escapeHTML(sk.name)}</h3><p class=\"summary\">${escapeHTML(sk.goal)}</p><div class=\"insight\">交付：${escapeHTML(sk.outputs)}</div><div class=\"foot\"><button class=\"button\" data-detail=\"${sk.id}\">查看模板</button>${favButton(sk.id)}</div></article>`).join(''):'<div class=\"empty\">没有符合筛选条件的任务模板。</div>';
$('#industryCount').textContent=`${ss.length} / ${D.sectors.length}`;$('#toolCount').textContent=`${ts.length} / ${D.tools.length}`;
$('#sectorCards').innerHTML=ss.length?ss.map(s=>`<article class="card"><div class="meta">${escapeHTML(s.group)} · ${escapeHTML(s.roles)}</div><h3>${escapeHTML(s.name)}</h3><p class="summary">${escapeHTML(s.pain)}</p><div class="insight"><strong>立即可做：</strong>${escapeHTML(s.quick)}</div><div class="pillrow">${tags(s.scenarios.slice(0,3))}</div><div class="foot"><button class="button" data-detail="${s.id}">查看完整路线</button>${favButton(s.id)}</div></article>`).join(''):'<div class="empty">没有符合条件的行业。请减少筛选条件或重置。</div>';
$('#toolCards').innerHTML=ts.length?ts.map(t=>`<article class="card"><div class="meta">${escapeHTML(t.type)} · ${escapeHTML(t.deployment)}</div><h3>${escapeHTML(t.name)}</h3><p class="summary">${escapeHTML(t.desc)}</p><div class="pillrow">${tags(t.scenarios.slice(0,3))}</div><div class="meta">${escapeHTML(t.region)} · 收录，尚未实测</div><div class="foot"><button class="button" data-detail="${t.id}">适用方式</button>${link(t.url,'官方网站')}${favButton(t.id)}</div></article>`).join(''):'<div class="empty">没有匹配工具。尝试更换搜索关键词或切换行业。</div>'}
function openDetail(id){let s=D.sectors.find(x=>x.id===id),t=D.tools.find(x=>x.id===id);const sk=D.first_party_skills.find(x=>x.id===id);if(!s&&!t&&!sk)return;lastFocus=document.activeElement;$('#modalTitle').textContent=s?s.name:t?t.name:sk.name;let body='';if(s){const hits=bestTools(s,8);body=`<p class="meta">${escapeHTML(s.group)} · 典型岗位：${escapeHTML(s.roles)}</p><div class="kv"><b>痛点</b>${escapeHTML(s.pain)}</div><div class="kv"><b>0–30 天 · Quick Win</b>${escapeHTML(s.quick)}</div><div class="kv"><b>1–3 个月 · Workflow</b>${escapeHTML(s.mid)}</div><div class="kv"><b>6–24 个月 · 研究推演，不是已发生事实</b>${escapeHTML(s.future)}</div><div class="kv"><b>指标参考</b>${escapeHTML(s.kpi)}</div><div class="kv"><b>主要风险闸门</b>${escapeHTML(s.risk)}</div><h3>行业高关联工具（匹配候选，非质量排名）</h3><div class="callout">${hits.map(t=>`${link(t.url,t.name)} <span class="meta">(${escapeHTML(t.type)})</span>`).join(' · ')}</div><h3>关联场景</h3><div>${tags(s.scenarios)}</div><div class="actions" style="margin-top:16px"><button class="button primary" id="fromSector">按此行业生成计划</button>${favButton(s.id)}</div>`}else if(sk){const lines=sk.steps.map((st,i)=>`<li>${escapeHTML(st)}</li>`).join('');body=`<p class=\"meta\">${escapeHTML(sk.status)}</p><div class=\"kv\"><b>目标</b>${escapeHTML(sk.goal)}</div><div class=\"kv\"><b>输入</b>${escapeHTML(sk.inputs)}</div><div class=\"kv\"><b>工作步骤</b><ol>${lines}</ol></div><div class=\"kv\"><b>交付物</b>${escapeHTML(sk.outputs)}</div><div class=\"kv\"><b>衡量标准</b>${escapeHTML(sk.metric)}</div><div class=\"kv\"><b>人工审核门槛</b>${escapeHTML(sk.gate)}</div><div class=\"actions\"><button class=\"button primary\" id=\"downloadSkillMd\">下载 SKILL.md</button>${favButton(sk.id)}</div>`}else{const industries=t.industries.length?t.industries.join('、'):'跨行业：根据所选场景评估';body=`<p class="meta">${escapeHTML(t.type)} · ${escapeHTML(t.deployment)} · ${escapeHTML(t.region)}</p><p>${escapeHTML(t.desc)}</p><div class="kv"><b>适用领域</b>${escapeHTML(industries)}</div><div class="kv"><b>场景标签</b>${tags(t.scenarios)}</div><div class="kv"><b>来源等级</b>${escapeHTML(t.source)}；${escapeHTML(t.review)}</div><div class="kv"><b>采用前检查</b>查看官方文档和费用、核验许可证/数据存储与权限、基于真实任务做对照评测、先使用脱敏样本、记录失败案例。</div><div class="actions" style="margin-top:16px">${link(t.url,'查看官方资料 / 仓库')}${favButton(t.id)}</div>`}$('#modalBody').innerHTML=body;$('#modal').classList.add('open');document.body.style.overflow='hidden';$('#modalClose').focus();$('#modalBody').querySelector('[data-fav]')?.addEventListener('click',()=>{const a=getFav(),i=a.indexOf(id);if(i<0)a.push(id);else a.splice(i,1);saveFav(a);openDetail(id);render()});if(sk)$('#downloadSkillMd').onclick=()=>download('SKILL-'+sk.slug+'.md',skillMarkdown(sk),'text/markdown;charset=utf-8');if(s)$('#fromSector').onclick=()=>{$('#planIndustry').value=s.id;closeModal();switchTab('plan');generatePlan()}}
function skillMarkdown(sk){return ['---','name: '+sk.slug,'description: '+sk.goal,'---','','# '+sk.name,'','状态：第一方草案，不代表已验证','', '## 目标',sk.goal,'','## 授权输入',sk.inputs,'','## 步骤',...sk.steps.map((a,i)=>`${i+1}. ${a}`),'','## 交付物',sk.outputs,'','## 验收指标',sk.metric,'','## 审核与安全',sk.gate,'','不自动调用外部工具；任何高风险写操作先获得明确批准。'].join('\n')}
function closeModal(){$('#modal').classList.remove('open');document.body.style.overflow='';lastFocus?.focus?.()}
function fillSources(){$('#sourceLinks').innerHTML=D.sources.map(s=>`<a href="${escapeHTML(s.url)}" target="_blank" rel="noopener noreferrer"><strong>${escapeHTML(s.name)} ↗</strong><span>${escapeHTML(s.desc)}</span></a>`).join('')}
function renderMatrix(){const order=D.scenarios.filter(s=>D.sectors.some(t=>t.scenarios.includes(s.id)));let h='<thead><tr><th>行业 / 场景</th>'+order.map(x=>`<th title="${escapeHTML(x.tip)}">${escapeHTML(x.name)}</th>`).join('')+'</tr></thead><tbody>';for(let s of D.sectors){h+=`<tr><td>${escapeHTML(s.name)}</td>`;for(let c of order){const hit=s.scenarios.includes(c.id);h+=`<td>${hit?`<button class="cell hit" title="${escapeHTML(s.name)} × ${escapeHTML(c.name)}" data-si="${s.id}" data-sc="${c.id}">✓</button>`:'<span class="cell none" aria-label="非核心分类">·</span>'}</td>`}h+='</tr>'}$('#matrixTable').innerHTML=h+'</tbody>';const freq=order.map(c=>({name:c.name,count:D.sectors.filter(s=>s.scenarios.includes(c.id)).length})).sort((a,b)=>b.count-a.count).slice(0,9);$('#scenarioBars').innerHTML=freq.map(x=>`<div class="statusbar"><span>${escapeHTML(x.name)}</span><b>${x.count} 个行业</b></div><div style="background:#1e3951;border-radius:8px;height:8px;overflow:hidden"><div style="height:100%;width:${x.count/D.sectors.length*100}%;background:#47bfb1"></div></div>`).join('')}
function generatePlan(){const s=sectorById($('#planIndustry').value)||D.sectors[0],goal=$('#planGoal').value,size=$('#planSize').value,level=$('#planData').value;const goals={time:'减少重复劳动与人工处理时间',quality:'降低错误与改善质量',growth:'提高获客转化与客户服务效率',knowledge:'建设可追溯组织知识库',innovation:'验证新产品或商业模式'};const advice=level==='regulated'?'强监管/敏感：优先仅使用合成或脱敏数据做离线评测；DPIA/权限/供应商合同/跨境数据审核通过前，不得把生产资料交给第三方。':level==='internal'?'内部资料：先进行分类分级、访问控制、保留策略和供应商安全评估，禁止未经授权上传。':'公开或合成样本：可低成本开展实验，但需要核验引用与版权。';const team=size==='solo'?'优先无代码、低成本 SaaS 或轻量本地工具；不要先建复杂基础设施。':size==='smb'?'设定业务 Owner + 技术支持 + 审核人，形成重复可用流程。':'设立业务、数据、法务安全、IT、审计跨职能项目组与变更审批。';const hits=bestTools(s,6);let plan=[`# ${s.name} · AI转型试点路线图`,`生成依据：YIFALIN行业图谱 V${D.version}（数据快照 ${D.as_of}）`,``, `目标：${goals[goal]}`,`人员：${s.roles}`,`痛点：${s.pain}`,``, `## 第1周 · 识别流程与基线`,`- 选定一个高频、可逆、可人工审查的任务，不以工具采购为起点。`,`- 记录现有处理时间、错误率和待审样本；选定基准样本集。`,`- 典型立即可做：${s.quick}`,``, `## 第2周 · 小样本只读试点`,`- 收集20–50个公开/脱敏样本，建立输入、标准输出、引用和人工复核流程。`,`- 逐个验证官方功能、成本、数据权限、法律许可和错误行为。`,`- 工具候选：${hits.map(t=>`${t.name}（${t.url}）`).join('；')}`,``, `## 第3周 · 测量与失败测试`,`- 和旧流程同样本比较：正确率、返工率、时间、人力及费用。`,`- 检查：无来源、过期信息、提示词注入、权限越界、错误数据和撤回。`,`- 观察指标：${s.kpi}`,``, `## 第4周 · 人机协同上线评审`,`- 仅在质量门槛通过后用于人工审核辅助；保留日志、回滚、停用开关。`,`- ${team}`,``, `## 30–90天 · 工作流改造`,`- ${s.mid}`,`- 建立专门的知识源、版本、人工审批和持续评测。`,``, `## 6–24个月 · 机会假设（未经实证）`,`- ${s.future}`,``, `## 安全与治理`,`- ${s.risk}`,`- ${advice}`,`- 研究候选不等于安全审计、采购建议、商业许可或实际ROI证明。`].join('\n');currentPlan=plan;$('#planOutput').innerHTML=`<h3>${escapeHTML(s.name)} · 研究型实施路线</h3><p class="small">目标：${escapeHTML(goals[goal])}</p><div class="roadmap"><div class="step"><b>第 1 周｜基线</b><p>${escapeHTML(s.pain)}；登记可测量的原流程。</p></div><div class="step"><b>第 2 周｜脱敏试点</b><p>${escapeHTML(s.quick)}；选用20–50条样本。</p></div><div class="step"><b>第 3 周｜对照测量</b><p>${escapeHTML(s.kpi)}；记录异常与人工纠错。</p></div><div class="step"><b>第 4 周｜审批门槛</b><p>${escapeHTML(team)}</p></div><div class="step"><b>1–3个月｜流程改造</b><p>${escapeHTML(s.mid)}</p></div><div class="step"><b>6–24个月｜机会推演</b><p>${escapeHTML(s.future)}</p></div></div><h4>工具候选（非质量排名）</h4><p class="toolmini">${hits.map(t=>link(t.url,t.name)).join(' · ')}</p><h4>风险与数据边界</h4><p class="small">${escapeHTML(s.risk)}。${escapeHTML(advice)}</p><div class="callout">必须用真实业务样本证明收益；本报告不宣称已完成试点。</div>`;showToast('路线图已生成，可下载Markdown')}
function showToast(msg){let el=$('#toast');el.textContent=msg;el.style.display='block';clearTimeout(showToast.t);showToast.t=setTimeout(()=>el.style.display='none',2200)}
function download(name,body,mime){let a=document.createElement('a'),u=URL.createObjectURL(new Blob([body],{type:mime}));a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1200)}
function exportCurrent(format){let rows=tab==='industries'?D.sectors.filter(matchSector):tab==='tools'?D.tools.filter(matchTool):tab==='skills'?D.first_party_skills.filter(matchSkill):tab==='plan'?[{title:'本地计划',text:currentPlan||'请先生成路线图'}]:D.tools.filter(matchTool);if(format==='json')return download(`ai-atlas-${tab}.json`,JSON.stringify({exported_at:D.as_of,view:tab,count:rows.length,items:rows},null,2),'application/json;charset=utf-8');const cols=[...new Set(rows.flatMap(r=>Object.keys(r)))];const cell=v=>'"'+String(Array.isArray(v)?v.join('、'):v??'').replace(/"/g,'""')+'"';const csv='\uFEFF'+[cols.map(cell).join(','),...rows.map(r=>cols.map(k=>cell(r[k])).join(','))].join('\r\n');download(`ai-atlas-${tab}.csv`,csv,'text/csv;charset=utf-8')}
setup();
</script></body></html>'''
html_file=TEMPLATE.replace('__DATA__',json.dumps(dataset,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
(ROOT/'index.html').write_text(html_file,encoding='utf-8')
readme=f'''# 全行业 AI 转型与能力图谱 V1.0

本项目把 **行业 → 岗位 → 痛点 → 场景 → 工具 → 试点计划 → KPI/治理** 做成可使用的离线静态网页，而不仅是工具名录。

## 运行

直接双击 `index.html`，可离线使用。浏览器支持本地收藏、筛选、行业/工具详情、交叉矩阵、生成 4 周试点+90天路径、导出 CSV/JSON 和 Markdown 计划。无需登录、服务器、API Key 或依赖。

- `index.html` 独立网页（含数据快照）
- `data.json` 可供二次开发的数据
- `industries.csv` 行业研究表
- `tools.csv` 工具 / Agent / Skill / 知识库目录\n- `skills/*/SKILL.md` 14 个第一方行业工作流程模板（未实测）\n- `roles.csv` 典型岗位实体；`graph.json` / `edges.csv` 显式关联图，可导入图数据库
- `build.py` 网页和数据构建源（Python 3.10+ 标准库；执行 `python build.py`）

## 首批覆盖

- 行业数：{len(sectors)}
- 工具/公开资源入口：{len(tools)}
- 场景：{len(scenarios)}\n- 第一方工作流 Skills：{len(skills)}
- 来源文档入口：{len(SOURCES)}
- 数据快照：{STAMP}

## 边界声明

1. 本次是 **编辑整理的产品/项目链接与行业适配假说**，不是对所有 URL 的当日可用性、厂商承诺、收费、质量或许可逐项审计。
2. 行业未来方向是推演，不是事实或财务预测；30–90天计划是建议模板，不代表任何客户已经部署。
3. 本项目不安装 Skills/MCP，不向第三方发送数据，不接入真实业务账户，更不授权自动下单、诊疗、作出法律/行政决定。
4. 每个案例正式上线前应进行数据治理、授权、质量评测、采购/许可、人工审批与回滚审查。
5. 优先将该行业应用层与既有 [YIFALIN Global AI Capability Atlas](https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin) 的真实资源目录双向关联，避免复制维护 5000 条索引。

## 未来结构化数据字段

`industry_id, role_id, scenario_id, tool_id, workflow_id, source_url, source_checked_at, last_evaluated_at, maturity, data_classification, deployment_mode, jurisdiction, license, pricing_verified_at, evidence_level, benchmark_id, review_owner`

最重要的验收：**从场景到可执行工作流 / 对照试验，而不是单纯增加条目数量。**
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')
print({'industries':len(sectors),'tools':len(tools),'scenarios':len(scenarios),'html_kb':round(len(html_file.encode('utf-8'))/1024,1),'path':str(ROOT/'index.html')})

# V1.1 extension: keep V1.0 data provenance and offline source as published baseline.
import upgrade_v11
upgrade_v11.build()