# DOCX Lab Report Skill

`docx-lab-report` 是一个 Codex skill，用于根据 Word 实验报告模板和实验材料生成中文或中英双语 `.docx` 实验报告。

它的核心目标不是“一键编造报告”，而是：

- 复用用户提供的 `.docx` 模板格式
- 从实验材料中提取可验证事实
- 在最终写入 Word 前先确认报告大纲
- 对最终 `.docx` 做 package-level 验证
- 避免编造实验结果、指标、截图说明、个人信息和日期

## What It Handles

适用场景：

- 有 `.docx` 实验报告模板
- 有实验指导书、代码、运行日志、CSV 结果、截图或结果图
- 需要保留学校或课程模板格式
- 需要生成中文或中英双语实验报告
- 需要在 Word 文件交付前验证图片、表格、正文和包结构

不适合：

- 没有实验材料却要求生成确定性实验结果
- 任意通用 Word 编辑任务，例如合同批注、修订跟踪、评论处理
- PDF、Excel 或 Google Docs 的通用处理任务

## Installation

复制整个 skill 目录到 Codex skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
rsync -a --exclude __pycache__ skills/docx-lab-report "${CODEX_HOME:-$HOME/.codex}/skills/"
```

如果没有 `rsync`，也可以用 `cp`：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/docx-lab-report "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## Dependencies

基础脚本使用 Python 3 标准库。

生成 `.docx` 需要：

```bash
pip install python-docx
```

可选依赖：

- `pdftotext`：用于从 PDF 实验指导书提取预览文本

## Recommended Workflow

以下命令中的 `<skill>` 表示 `skills/docx-lab-report` 或安装后的 skill 路径。

### 1. Profile The Template

```bash
python3 <skill>/scripts/profile_docx_template.py TEMPLATE.docx --out format-profile.json
```

输出 `format-profile.json`，包括：

- 页面设置和内容宽度
- 标题候选
- 字体字号候选
- 编号信息
- 表格和图片数量
- DOCX package 结构
- 可能的个人信息字段

`format-profile.json` 只是建议，最终格式仍需要用户确认。

### 2. Confirm Format Requirements

根据模板 profile 创建 `format-requirements.json`，并让用户确认：

- 标题层级
- 各级标题编号
- 标题字体和字号
- 正文字体和字号
- 图表题注字体和字号

如果用户接受默认格式，应把这个选择明确记录到 `format-requirements.json`。

### 3. Inventory Materials

```bash
python3 <skill>/scripts/inventory_materials.py MATERIALS... --out material-summary.md
```

脚本会生成：

- `material-summary.md`
- `missing-info.md`
- `figure-summary.md`，当存在图片或截图时
- `table-summary.md`，当存在 CSV 或电子表格结果时

材料分类包括：

- `template`
- `guidance`
- `source-code`
- `results`
- `figures`
- `other`

### 4. Handle Personal Information

如果模板中检测到姓名、学号、班级、日期、课程、教师等字段，应一次性询问用户是否填写。

保存确认后的内容：

```json
{
  "姓名": "张三",
  "学号": "2024000000",
  "班级": "",
  "实验日期": ""
}
```

未填写字段应保留模板原样，不能猜测。

### 5. Draft And Approve Outline

生成 `report-outline.md`，并让用户确认后才能写最终 `.docx`。

大纲应说明：

- 标题层级和编号
- 每节使用哪些材料
- 缺少哪些结果或图片
- 图表说明是否需要用户确认
- 个人信息如何处理
- 最终格式要求

### 6. Write Report Content

用户确认大纲后，创建 `report-content.md`。

图片使用 Markdown 图片语法放到对应章节：

```markdown
![图1 数据分布](figures/target_distribution.png)
```

每个图或表附近必须有文字说明：

- 它展示什么
- 可见或提取到的关键观察
- 支撑哪个实验结论
- 哪些结论不能从当前材料推出

### 7. Generate DOCX

```bash
python3 <skill>/scripts/write_docx_report.py \
  --template TEMPLATE.docx \
  --outline report-outline.md \
  --content report-content.md \
  --out OUTPUT.docx \
  --format-requirements format-requirements.json \
  --personal-info personal-info.json \
  --outline-approved
```

默认行为是匹配模板中的顶层章节，并在原章节位置写入内容。

脚本会额外生成：

```text
OUTPUT.write-summary.json
```

该 summary 记录：

- 使用的写入模式
- 匹配到的模板章节数量
- 插入的图片
- 缺失的图片
- 是否使用 append fallback

### 8. Validate DOCX

```bash
python3 <skill>/scripts/validate_docx_report.py OUTPUT.docx \
  --template TEMPLATE.docx \
  --outline report-outline.md \
  --summary OUTPUT.write-summary.json
```

验证内容包括：

- 输出文件是否是有效 DOCX ZIP 包
- 是否包含关键 parts，例如 `word/document.xml`
- 图片 relationship 是否能解析到实际媒体文件
- 是否存在 `[缺少图片：...]` 占位
- outline 是否被误复制进最终正文
- 是否使用了 append 模式

如果使用 append 模式，必须先告知用户内容可能没有写入模板的精确章节位置。用户接受后再运行：

```bash
python3 <skill>/scripts/validate_docx_report.py OUTPUT.docx \
  --template TEMPLATE.docx \
  --outline report-outline.md \
  --summary OUTPUT.write-summary.json \
  --allow-append
```

## Script Reference

### `profile_docx_template.py`

分析 `.docx` 模板格式和包结构：

```bash
python3 scripts/profile_docx_template.py TEMPLATE.docx --out format-profile.json
```

### `inventory_materials.py`

汇总实验材料并生成缺失项、图片摘要、表格摘要：

```bash
python3 scripts/inventory_materials.py MATERIALS... --out material-summary.md
```

### `write_docx_report.py`

按已批准的大纲和正文写入最终 Word 报告：

```bash
python3 scripts/write_docx_report.py \
  --template TEMPLATE.docx \
  --outline report-outline.md \
  --content report-content.md \
  --out OUTPUT.docx \
  --format-requirements format-requirements.json \
  --personal-info personal-info.json \
  --outline-approved
```

### `validate_docx_report.py`

验证最终 DOCX：

```bash
python3 scripts/validate_docx_report.py OUTPUT.docx \
  --template TEMPLATE.docx \
  --outline report-outline.md \
  --summary OUTPUT.write-summary.json
```

## Safety Rules

- 不要在用户确认大纲前生成最终 `.docx`。
- 不要编造实验结果、指标、截图内容、个人信息或日期。
- 不要覆盖原始模板文件。
- 不要把 `report-outline.md` 当作正文写入最终报告。
- 图片和表格不能只插入文件名，必须有相邻说明文字。
- 最终交付前必须运行 `validate_docx_report.py`。

## Generated Files

典型中间文件：

```text
format-profile.json
format-requirements.json
material-summary.md
missing-info.md
figure-summary.md
table-summary.md
personal-info.json
report-outline.md
report-content.md
OUTPUT.write-summary.json
```

这些文件通常属于具体报告任务，不建议提交到复用 skill 仓库。

## License

MIT License. See [../../LICENSE](../../LICENSE).
