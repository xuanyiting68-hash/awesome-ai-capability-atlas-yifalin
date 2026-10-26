# V1.3 多生态来源与风险分级

本次将原先由 OpenClaw 单一大目录主导的 5,000 条索引升级为多生态发现层。**每个来源的实际数量只以 data/provenance.json 为准。**

| 来源 | 索引方式 | 内容 | 审核状况 |
|---|---|---|---|
| Anthropic Skills | GitHub Tree | SKILL.md | 未审计 |
| OpenAI Skills | GitHub Tree | SKILL.md | 未审计 |
| Microsoft Skills | GitHub Tree | SKILL.md | 未审计 |
| GitHub awesome-copilot | GitHub Tree | Skills + Agents | 未审计 |
| wshobson/agents | GitHub Tree | Agents + Skills | 未审计 |
| sickn33/agentic-awesome-skills | GitHub Tree | Skills | 未审计 |
| Zie619/n8n-workflows | GitHub Tree | JSON workflows | 未审计 |
| MCP Official Registry | 官方元数据 API | MCP Server | 未审计 |
| GitHub MCP Server Topic | GitHub 搜索 | MCP 项目 | 未审计 |
| VoltAgent OpenClaw | 公开目录 Markdown | Skill 条目 | 未审计 |

说明：官方发布者或注册表代表来源身份，不代表所列技能/服务器安全认证。采集仅获取公开文件路径、仓库信息或登记元数据，不下载并执行技能。

## 风险标记

- discovery-only：仅目录发现。
- repo-exists-not-audited：精选仓库存在性核验，不意味着代码审查。
- not-audited：未做安全审查。
- license_review=not-checked：未核对 LICENSE、依赖、权重或素材商业授权。
- risk=unassessed：风险未知，绝非低风险。

## 后续建议

对可复用的头部项目做二次深入筛选、隔离复现、许可证审查、可解释评价；避免把 Github Stars 或目录出现频率当成质量评分。
