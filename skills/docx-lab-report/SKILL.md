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

3. Review `format-profile.json`. If the profile has unknown format items or weak inferences, ask the user to confirm or accept defaults.
4. Inventory materials:

   ```bash
   python3 <skill>/scripts/inventory_materials.py MATERIALS... --out material-summary.md
   ```

5. Read `material-summary.md` and `missing-info.md`. Treat important claims as grounded only when backed by material files or explicit user input.
6. Detect personal-info fields from `format-profile.json`. If any exist, list all fields once and ask whether to fill them. Let the user leave fields blank.
7. Draft `report-outline.md` from the template structure and materials.
8. Stop and ask the user to approve or revise the outline.
9. After approval, create the report content and write the `.docx`:

   ```bash
   python3 <skill>/scripts/write_docx_report.py \
     --template TEMPLATE.docx \
     --outline report-outline.md \
     --content report-content.md \
     --out OUTPUT.docx \
     --outline-approved
   ```

If template-copy writing is unsafe, use the script's `--mode rebuild` fallback only after telling the user that page-level fidelity may be lower.

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

## Default Format Rules

Use these only when the template lacks enough evidence:

- four heading levels
- all heading fonts: 黑体
- level 1 heading size: 四号
- levels 2-4 heading size: 小四号
- level 1 numbering: `一、` `二、`
- level 2 numbering: `（一）` `（二）`
- level 3 numbering: `1.` `2.`
- level 4 numbering: `（1）` `（2）`
- figure and table text size: 五号

## Required Review Files

Before writing the final `.docx`, produce and review:

- `format-profile.json`
- `material-summary.md`
- `missing-info.md`
- `report-outline.md`

Use `references/docx-workflow.md` for detailed format inference, material classification, write strategy, and final checks.
