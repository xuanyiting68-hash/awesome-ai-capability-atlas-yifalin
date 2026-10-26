# YIFALIN · AI 能力落地蓝图 V1.3

以下为供隔离环境试验的开源组件组合，**不是已部署产品，不代表 API 可以自动连通或允许商用**。

<a id="video"></a>

## AI 视频工厂

**业务目标**：原创知识研究到合规短视频发布

**候选技术组件**：[remotion-dev/remotion](https://github.com/remotion-dev/remotion)、[FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg)、[SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)、[gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app)

| 阶段 | 验证任务 |
|---|---|
| 1 | 选题与来源授权 |
| 2 | 独立研究脚本与事实复核 |
| 3 | 视频/字幕/配音制作 |
| 4 | 人工内容审批 |
| 5 | 官方支持渠道发布及复盘 |

**审批/风险门禁**：版权授权；真人出镜与独立推导；财经内容不提供直接买卖建议；禁止未获授权的声纹克隆

**验证指标**：人工制作与复核耗时、视频完播率、有效咨询率

**进度**：方案设计阶段，尚无实际集成或生产验证。

---

<a id="social"></a>

## 自媒体智能运营

**业务目标**：多渠道原创内容排期、授权发布和效果归因

**候选技术组件**：[gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app)、[n8n-io/n8n](https://github.com/n8n-io/n8n)、[posthog/posthog](https://github.com/posthog/posthog)

| 阶段 | 验证任务 |
|---|---|
| 1 | 按各平台撰写原创版本 |
| 2 | 审批内容日历 |
| 3 | 平台 API 授权验证 |
| 4 | 排期发布与评论分流 |
| 5 | 平台指标与转化复盘 |

**审批/风险门禁**：遵守每个平台 API 和用户协议；不得自动刷评论/粉丝；原创表达与人工最终审核

**验证指标**：每周原创内容数、各渠道有效互动率、真实线索转化率

**进度**：方案设计阶段，尚无实际集成或生产验证。

---

<a id="leads"></a>

## 合规智能获客

**业务目标**：客户主动咨询、同意留资、线索分层和预约

**候选技术组件**：[formbricks/formbricks](https://github.com/formbricks/formbricks)、[baptisteArno/typebot.io](https://github.com/baptisteArno/typebot.io)、[TwentyHQ/twenty](https://github.com/TwentyHQ/twenty)、[calcom/cal.com](https://github.com/calcom/cal.com)

| 阶段 | 验证任务 |
|---|---|
| 1 | 原创活动/内容吸引咨询 |
| 2 | 表单明确告知与同意 |
| 3 | 数据校验和 CRM 去重 |
| 4 | 按自报需求进行分层 |
| 5 | 用户主动预约或人工沟通 |

**审批/风险门禁**：不得抓取私人资料；禁止未经授权的批量自动私信；记录营销同意和可撤销机制；敏感数据最小化

**验证指标**：自愿留资率、有效线索率、预约转化率

**进度**：方案设计阶段，尚无实际集成或生产验证。

---

<a id="crm"></a>

## 客户维护与服务

**业务目标**：工单、客户分层、教育内容、订阅与续费服务

**候选技术组件**：[TwentyHQ/twenty](https://github.com/TwentyHQ/twenty)、[chatwoot/chatwoot](https://github.com/chatwoot/chatwoot)、[mautic/mautic](https://github.com/mautic/mautic)、[posthog/posthog](https://github.com/posthog/posthog)

| 阶段 | 验证任务 |
|---|---|
| 1 | 权限隔离的 CRM 资料 |
| 2 | 客户问题受理与分类 |
| 3 | 知识库建议与人工复核 |
| 4 | 经同意的提醒与教育 |
| 5 | 留存、满意度和退订监控 |

**审批/风险门禁**：最小权限；退订与频次控制；不把 AI 回复伪装成人类承诺；审计与数据删除

**验证指标**：工单首响时长、问题解决率、续费率、退订率

**进度**：方案设计阶段，尚无实际集成或生产验证。

---

<a id="finance"></a>

## 金融 AI 研究

**业务目标**：金融研究、可复现量化实验、样本外和模拟盘验证

**候选技术组件**：[microsoft/qlib](https://github.com/microsoft/qlib)、[microsoft/RD-Agent](https://github.com/microsoft/RD-Agent)、[QuantConnect/Lean](https://github.com/QuantConnect/Lean)、[Arize-ai/phoenix](https://github.com/Arize-ai/phoenix)

| 阶段 | 验证任务 |
|---|---|
| 1 | 冻结研究假设与可追溯行情 |
| 2 | 检验泄漏、偏差和条件预测 |
| 3 | 真实交易成本模拟 |
| 4 | 样本外和模拟盘前瞻审查 |
| 5 | 独立审批风险参数和部署 |

**审批/风险门禁**：禁止直接授予 AI 实盘下单权限；不得承诺盈利；实盘前独立合法性与风险审查

**验证指标**：样本外校准、成本后净期望、最大回撤、风险门禁通过率

**进度**：方案设计阶段，尚无实际集成或生产验证。

---

<a id="education"></a>

## AI 互动教育

**业务目标**：多媒体课程知识管理、个性化练习和学习评估

**候选技术组件**：[docling-project/docling](https://github.com/docling-project/docling)、[infiniflow/ragflow](https://github.com/infiniflow/ragflow)、[openedx/edx-platform](https://github.com/openedx/edx-platform)、[ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp)

| 阶段 | 验证任务 |
|---|---|
| 1 | 课程版权和使用授权 |
| 2 | 文档结构化并保存引用 |
| 3 | 题目、案例、可视化练习 |
| 4 | 语音互动及错误诊断 |
| 5 | 学习前后测与质量抽检 |

**审批/风险门禁**：课程与图片版权；学生数据保护；教学答案要可验证；避免无依据的成绩承诺

**验证指标**：课程完成率、知识掌握提升、引用准确率、学习留存

**进度**：方案设计阶段，尚无实际集成或生产验证。

---

## 跨方案的标准门禁

1. 从原始仓库核对 LICENSE、依赖许可证、模型权重、素材授权与商用限制。
2. 第三方 Skills/Agents、API 工具在只读隔离环境评测，不执行未审查脚本。
3. 对外发布、营销邮件、客户资料处理必须记录授权/同意并支持人工接管。
4. 金融 AI 研究与订单执行隔离，样本外审计和合法合规审查优先。
5. 数据与指标保留审计证据；测不出效果的工具不升级为优先推荐。
