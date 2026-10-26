# 来源可追溯研究档案贡献规范（Pilot v1）

> 最后核验：2026-10-27（悉尼时间）。这份规范是项目内部的研究门禁，不是第三方软件的安全认证或许可证法律意见。

## 本期范围

- 首批仅 4 项：Qlib、LangGraph、Remotion、Twenty；研究信息保存在 `data/research_briefs.json`。
- 全部显示为 **Curated（编辑研究）**，不能因读过 README、Stars 较多、有 SPDX、官网写了 Production-ready 就升级成 Reviewed、Reproduced 或 Production Candidate。
- 原有 30 项仍 `HOLD`，不修改冻结的 `data/top30_evidence.json` 历史审查结论。
- `scripts/validate_research_briefs.py` 拒绝没有证据的晋级：这是一道硬性安全门禁，不允许绕过。升级更高层次需要重新制定并审查新数据结构和独立证据要求。

## 为候选项目创建研究档案

1. **确认身份。** GitHub URL 是规范化 `owner/repo`；来源必须对应 Top 30 的真实仓库。记录阅读时间为带时区 UTC，不得补填未来时间。
2. **固定 README 字节来源。** 从 GitHub Contents API 获得 README 的 git blob SHA（40 字符），保留 `https://api.github.com/repos/<owner>/<repo>/git/blobs/<sha>` 快照与可读的官方 README 链接。请注意：Git Blob 只能固定 README 文件，不代表已固定该项目所有依赖或整仓提交。
3. **链接官方文档。** 不从搜索摘要、转载教程或星数推导功能。每一条声称“官方支持”的能力都必须引用本条档案的 `readme` 或 `docs` 来源 ID。未核验的用户案例不得写成已证实。
4. **判断适配边界。** 用中英两种语言回答“适合谁 / 不适合谁”，优先写真实能力、主要局限和需要用户承担的额外成本。
5. **提出可反驳的实验。** 用自有/合成/授权数据列出输入、三步以上的实验过程、验证指标、成功及停止门槛。请写清 **proposed—not executed**。
6. **注明风险。** 许可证原文、依赖、媒体资产、数据出境、密钥/工具权限与第三方成本需要分别核验；未知必须是未知。
7. **独立 QA。** 审稿人核对数据文件、正式发布渲染、双语内容、移动端、过期证据和外部链接；通过 CI 不等于全部法律/安全审查完成。

## 五级证据晋级责任

| 层级 | 最低证据 | 不足时 |
| --- | --- | --- |
| Discovery | 标准资源 URL、基本归属、发现时间、去重 | 不进入目录 |
| Curated | 两个官方出处、业务价值与边界、署名编辑方案 | 留在 Discovery |
| Reviewed | LICENSE 原文与适用范围、依赖许可证、权限/维护/安全桌面审核、审稿人和日期 | HOLD，不进入 Reviewed |
| Reproduced | 固定仓库 commit、隔离环境与依赖锁、运行命令与输入哈希、日志、失败案例、独立复跑 | 标记 not-tested |
| Production Candidate | 在 Reproduced 基础上补充授权、成本、安全/隐私、运营/回滚和适用环境的明确批准 | 仍 HOLD |

**不同级别不可仅由 Stars、Forks、GitHub SPDX 或模型主观评分决定。**

## 发布门禁

```bash
python scripts/validate_research_briefs.py
python -m unittest scripts.test_research_briefs -v
python scripts/build_site.py
npm run test:e2e
npm run test:staged
```

CI 会进行数据与 JavaScript 检查及真实 Chrome 回归测试。任何无证据状态升级、官方来源冒名、来源 SHA 不匹配、缺少双语字段等，应拒绝发布。

## 从 4 份试点扩展到 300–500 份的方法

**阶段 A：4 → 30。** 对 Top 30 完成至少 Curated 的带来源档案，优先补齐真正影响使用的安装前提、替代选择和具体实验评估标准。此阶段可以不运行第三方代码。

**阶段 B：30 → 100。** 增加更多生态与真实业务需求覆盖；抽样人工交叉检查来源质量、过期文档和分类偏差。建立每次复审日志与版本快照，而不只自动刷新 Stars。

**阶段 C：100 → 300–500。** 为高价值项目逐个设计独立隔离实验、记录可复制命令与原始结果。先保证证据完整，再做精品专题和比较排名。**不以达成数量为自动通过条件。**

## 图像和视频政策

优先链接项目官方演示，不盗用未经许可的第三方截图或视频。未来使用媒体时需记录官方来源、发布日期或检索日期、素材使用权说明、归属和内容版本。自制工作流图可用于解释结构，但不得伪装成第三方项目运行截图。

## 既有局限

- 自动化无法仅靠读取 README 判断商业授权：Remotion 等项目的使用模式可能有额外许可证条款，必须核查原文。
- 仓库 README Git Blob SHA 不固定外链文档版本，后续需要定期复核外链与文档变化。
- 首批 4 项仅为初步编辑研究，**没有安装、跑分、第三方安全审计或真实客户/交易连接**。
