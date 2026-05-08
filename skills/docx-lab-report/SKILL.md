---
name: docx-lab-report
description: Use when creating or updating Chinese or bilingual lab reports in .docx format from a Word template and experiment materials, especially when Codex must preserve report formatting, infer heading styles, summarize files, handle personal-info fields, or generate a report only after outline approval.
---

# DOCX Lab Report

## Core Rule

Generate a `.docx` lab report only after the user approves the report outline. Do not invent experiment results, metrics, screenshots, personal information, or dates.

## Workflow

1. Identify the `.docx` template and experiment materials.
2. Profile the template:

   ```bash
   python3 <skill>/scripts/profile_docx_template.py TEMPLATE.docx --out format-profile.json
   ```

3. Review `format-profile.json`, then create `format-requirements.json` and ask the user to explicitly confirm:
   - heading depth
   - numbering pattern for each heading level
   - Chinese font and size for every heading level
   - Chinese font and size for body text
   - Chinese font and size for table and figure captions

   Do not write the final `.docx` until these requirements are confirmed.
4. Inventory materials:

   ```bash
   python3 <skill>/scripts/inventory_materials.py MATERIALS... --out material-summary.md
   ```

5. Read `material-summary.md` and `missing-info.md`. Treat important claims as grounded only when backed by material files or explicit user input.
6. Review `figure-summary.md` and `table-summary.md` when they exist. Every figure and table used in the final report must have an adjacent description of what it shows, key observations, and how it supports the experiment analysis.
7. Detect personal-info fields from `format-profile.json`. If any exist, list all fields once and ask whether to fill them. Let the user leave fields blank. Save confirmed values to `personal-info.json`.
8. Draft `report-outline.md` from the template structure and materials.
9. Stop and ask the user to approve or revise the outline.
10. After approval, create `report-content.md`. Put figures where they should appear by using Markdown image lines, for example `![图1 数据分布](figures/example.png)`.
11. Write the `.docx` by filling matching template sections in place:

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

If template section matching is unsafe, use append fallback only after telling the user that the report may not be filled into the exact template positions. The outline file is an approval gate and is not appended to the final report.

## Content Boundaries

You may organize and rewrite:

- experiment purpose
- experiment principle
- experiment steps
- environment setup
- code explanation

You must ground these in result files, screenshots, logs, or explicit user confirmation:

- experiment results
- performance numbers
- screenshots and image descriptions
- comparisons and conclusions

If results are missing, leave placeholders or ask for more material. Never create plausible-looking data.

## Figure And Table Descriptions

When materials include figures, screenshots, tables, CSV files, or spreadsheets, do not only insert them or mention filenames. For each figure or table used in the report, write nearby text that states:

- what the figure/table shows
- the key observations or values that are visible or extracted
- which experiment section or conclusion it supports
- any limits, missing raw data, or claims that cannot be made from it

If the image content cannot be inspected reliably, mark the description as `待确认` or ask the user. Do not invent visual trends, table values, or rankings.

## Personal Information

When personal fields are detected, ask once:

```text
检测到这些个人信息字段：
- 实验名称
- 姓名
- 学号
- 班级
- 实验日期

是否需要填写？如果需要，请按“字段名：内容”的形式提供；不需要填写的字段可以留空。
```

Do not guess missing fields. Preserve the template's original placeholder, cell, underline, tab stop, or spacing when a field is left blank.

## Format Requirements

Template profiling provides suggestions only. The user must explicitly confirm the final format before final writing. If the user wants defaults, record that explicit choice in `format-requirements.json`; do not silently infer it.

Default format, when the user confirms defaults:

- body text: 小四, Chinese 宋体, English and Arabic numerals Times New Roman
- maximum heading depth: 4
- all heading fonts: 黑体
- level 1 heading size: 四号
- levels 2-4 heading size: 小四
- level 1 numbering: `一、` `二、`
- level 2 numbering: `（一）` `（二）`
- level 3 numbering: `1.` `2.`
- level 4 numbering: `（1）` `（2）`
- figure and table text size: 五号

If a normal body paragraph in the template's body area uses a Chinese font different from default 宋体, list it as a body-font candidate and ask whether to adopt it. Adopt it only after user confirmation, then apply that body font consistently to all generated body text.

## Required Review Files

Before writing the final `.docx`, produce and review:

- `format-profile.json`
- `format-requirements.json`
- `material-summary.md`
- `missing-info.md`
- `figure-summary.md` when figures are present
- `table-summary.md` when tabular result files are present
- `report-outline.md`

Use `references/docx-workflow.md` for detailed format inference, material classification, write strategy, and final checks.
