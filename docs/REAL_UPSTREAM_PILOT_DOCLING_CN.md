# YIFALIN Pilot Lab 03｜Docling 官方 SDK 真实 PDF 解析实验

> 实验独立于此前的 24 项第一方合成契约和 LangGraph 1.2.18 真实沙盒。本文依据截至 2026-10-29 的 Docling 官方 **v2.144.0** 源代码、发行版本、`NativePdfPipeline` 和仓库根 LICENSE。实际通过数量以 GitHub Actions 对应 SHA 的 CI 日志、JSON 工件为准。

## 一、本轮测试的能力和严格边界

- 上游：[docling-project/docling](https://github.com/docling-project/docling)，[v2.144.0 Release](https://github.com/docling-project/docling/releases/tag/v2.144.0)，发布于 2026-10-28。
- 真正调用：`DocumentConverter`、`NativePdfFormatOption`、`NativePdfPipelineOptions`，使用 **Docling 原生 PDF 解析管线**，读取产生的 `DoclingDocument.texts[*].prov[*].page_no` 和 `export_to_markdown()`。
- 输入：纯标准库临时生成的 **三页合成 PDF**，由 Courier 字体、ASCII 文本、正确的 PDF 交叉引用表构成。内容包含合成研究变量 NOFI、风险概念 VaR、合成 45 分钟课程说明以及表格布局下的 Var95/Exposure 数值。所有内容原创，未使用你的 CQF/论文 PDF、私有交易记录、网盘或用户隐私。
- **不下载模型，不执行 OCR、视觉布局识别、公式解析或表格结构模型。** 上游 NativePdfPipeline 官方注释明确其不推断阅读顺序、标题及结构化表格；我们不把文字单元格命中率宣传为表格识别精度。
- 工作流在临时 GitHub Actions Ubuntu Runner 使用 Python 3.12 和仅限二进制 wheel 的 `docling==2.144.0`；不需要 API 密钥、外部文档 URL 或生产系统权限。安装软件包仍需连接公共包索引；测试时设置模型离线开关。
- 并未复制上游源码或创建 Fork；当前仍保持全部生产和安全放行门禁。

## 二、12 个真实上游执行断言

| ID | 真实观测目标 | 验收标准 |
|---|---|---|
| DOC01 | 标准合成 PDF | 纯标准库生成合法 PDF 文件 |
| DOC02 | 页面数量 | Docling Document 含三页 |
| DOC03 | 研究页面 | 第 1 页研究标题可读 |
| DOC04 | 来源定位 | NOFI 只归属于第 1 页 |
| DOC05 | 课程页面 | 第 2 页可提取 45 分钟课程时长 |
| DOC06 | 金融术语 | VaR 课程目标归于第 2 页 |
| DOC07 | 表格形状下的文字 | 第 3 页能提取指标和数值的纯文本 |
| DOC08 | 缺失证据 | 不会凭空出现原文不存在的 UNSOURCED_TOKEN |
| DOC09 | 不可信指令 | PDF 中的恶意文本只作为文档内容；未执行下单 |
| DOC10 | 不冒充表格结构 | `document.tables` 真实数量是 0 |
| DOC11 | Markdown 导出 | 导出的 Docling Markdown 包含 NOFI 和 45 分钟 |
| DOC12 | 溯源完整性 | 所有文本来源页码均在 1–3 范围内 |

此外，独立 Python unittest 会读取 JSON 工件、检查安全与能力声明、验证 PDF 生成逻辑，并**再次调用真实 Docling** 复验结果。

## 三、运行与证据

在已授权的本地实验环境中：

```powershell
python -m pip install --only-binary=:all: --no-cache-dir docling==2.144.0
python scripts/real_docling_pilot.py
python -m unittest scripts.test_real_docling_contract -v
```

正式 CI 工作流：[Verify real Docling PDF (isolated)](../.github/workflows/real-upstream-docling.yml)，成功后上传逐项 JSON 和 `pip freeze --all` 生成的依赖版本清单。只有 exact-HEAD CI 全绿和产物存在才能说“真实 Docling API 12/12 通过”。

不安装第三方包的基础 Atlas CI 会明确 **skip** 这些 Docling SDK 用例，避免误将缺少 SDK 视为通过；独立真实 CI 必须真正运行该测试套件。

## 四、下一步门禁

- **真实 PDF 的授权样本集：** 单独生成更接近课程课件的排版、符号、公式、表格、跨页文本和图表，并加人工标注真值；和上述简单 PDF 分开汇报指标。
- **默认复杂 PDF Pipeline：** 可能要下载布局、表格或 OCR 模型，必须先审查模型权重、许可证、包依赖和下载行为，隔离后才能测试。
- **量化验收指标：** 字符准确率、页码准确率、表格单元格匹配、公式召回、章节链接完整性、耗时/内存、失败分布，以及中文/英文文档差异。
- **生产门禁：** 导入课程/用户上传资料必须具备处理权利、身份与访问控制、数据保留/删除策略、敏感内容隔离、审计、回滚，避免未经许可的课程内容通过 Atlas 公开分发。
- 此实验不改变原 Top30 项目 `Fork HOLD`、`not-tested` 或许可证完整审查状态；通过简易 PDF 不代表 OCR、复杂表格、语义结构等已验证。

> **真实 NativePdfPipeline 已能提取原生 PDF 文字及页码，也不代表已达到金融文档生产标准。**
