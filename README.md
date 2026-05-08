# Codex Document Skills By Lv

这个仓库用于存放可复用的 Codex skills。目前包含一个面向中文或中英双语实验报告的 Word 文档生成 skill。

## Skills

### DOCX Lab Report

路径：`skills/docx-lab-report`

用途：

- 从 `.docx` 实验报告模板生成新的 Word 实验报告
- 保留模板中的标题、页面、字体、页眉页脚等格式线索
- 汇总实验指导书、代码、日志、CSV、截图和结果图
- 在生成最终 `.docx` 前要求确认报告大纲
- 对最终 Word 文件执行 DOCX ZIP/XML 级别验证

详细说明见 [skills/docx-lab-report/README.md](skills/docx-lab-report/README.md)。

## Installation

把 skill 目录复制到 Codex 的 skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
rsync -a --exclude __pycache__ skills/docx-lab-report "${CODEX_HOME:-$HOME/.codex}/skills/"
```

如果没有 `rsync`，也可以用 `cp`：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/docx-lab-report "${CODEX_HOME:-$HOME/.codex}/skills/"
```

安装后，在 Codex 中使用：

```text
Use $docx-lab-report to profile my DOCX template, summarize experiment materials, confirm an outline, and generate a formatted lab report.
```

## Repository Layout

```text
skills/
  docx-lab-report/
    SKILL.md
    README.md
    agents/
    references/
    scripts/
```

`SKILL.md` 是 Codex 加载的主要说明文件；`README.md` 面向使用者；`scripts/` 中是可直接运行的辅助工具。

## Notes

- 这个仓库不包含实验材料或个人信息。
- 示例材料、生成的报告、中间文件和本地缓存不要提交到仓库。

## License

MIT License. See [LICENSE](LICENSE).
