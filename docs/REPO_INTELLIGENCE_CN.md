# YIFALIN · Repository Intelligence V1.2

本专题仅对编辑精选 Github 仓库进行元数据补充，批量抓取的 OpenClaw Skills 不因此获得质量或安全背书。

| 字段 | 含义 | 使用边界 |
|---|---|---|
| stars, forks | GitHub 关注度 | 社区热度不是稳定性、安全或研究质量证明 |
| last_push | 最近 Git Push | 不等于最近 Release，也不代表持续维护 |
| archived | 是否归档 | 已归档时应优先考虑替代方案 |
| license_spdx | GitHub 检出的许可证标识 | 无法替代阅读 LICENSE、依赖许可证和模型许可 |
| security_review | 本站独立标记 | 当前均未经代码安全审计，不能自动标记为通过 |

通过 GitHub Actions 每周同步；出现任何采集失败时，脚本不会用不完整快照覆盖既有数据。
