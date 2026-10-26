# V1.4.4 · 发布验证与线上巡检

## 已实现

- 发布前执行数据/脚本检查；`scripts/build_site.py` 仅打包页面、data、docs、README 和 LICENSE。
- 测试代码、node_modules、Git 数据、工作流配置不再随 Pages 根目录一起发布。
- 生成 `deployment.json`：记录源提交、站点版本、目录/精选/研究队列数量与快照时间。源提交表示构建来源，不表示第三方项目已完成审计。
- 证据过期、目录数量超过 5,000 或与来源记录不一致时阻止打包。
- 每次 Pages 成功发布后，通过真实 Chromium 验证发布 SHA、双语数据、筛选、收藏、对比、移动宽度和主目录。
- 每日额外执行一次相同巡检，支持手动运行。失败表现为 GitHub Actions 红色检查及日志，未配置对外消息、邮件或付费监控。
- 元数据和资源索引两条自动写入流程共享串行队列，减少同时更新 main 的冲突。

## 验证

```bash
python -m unittest discover -s scripts -p 'test_*.py'
npm run test:e2e
npm run test:staged
ATLAS_BASE_URL=https://xuanyiting68-hash.github.io/awesome-ai-capability-atlas-yifalin/ npm run test:smoke
```

- 本地 30 项 Python 测试通过。
- V1.4.3 的 17 场景真实浏览器测试已通过，并保留为 PR 回归检查。
- 本地已对实际 `_site` 发布产物运行部署冒烟测试，通过；没有将临时测试服务称为线上部署。
- PR 合并后，线上结果以 `Monitor published atlas` 实际运行记录为准。

## 已知限制及下一轮

- 监控能发现加载和交互回归，不能证明第三方链接、授权、依赖或实际能力有效。
- 许可证原文和依赖审查、锁定 SHA 的隔离复现仍未完成，30 项保持 HOLD。
- 下一轮应为六大业务方案补齐可下载的实验规格、基线、成本预算与验收数据；通过审查后才运行第三方组件。
