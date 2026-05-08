# DOCX Lab Report Workflow Reference

## Template Profiling

Prefer explicit template instructions over inferred style evidence. Search the template text for wording about `格式`, `字体`, `字号`, `标题`, `正文`, `表格`, `插图`, and `报告要求`.

If explicit instructions are absent, infer from:

- paragraph style IDs and style names
- numbering definitions in `word/numbering.xml`
- short bold paragraphs or numbered paragraphs as heading candidates
- repeated body paragraph fonts and sizes
- table paragraph runs for table text style
- page settings, margins, headers, and footers

Record low-confidence items under `unknown`. Use the profile only to propose `format-requirements.json`; the user must confirm final heading levels, heading fonts and sizes, body font and size, and caption/table font and size.

Default format, if the user explicitly accepts defaults:

- body: 小四; Chinese 宋体; English and Arabic numerals Times New Roman
- heading depth: at most 4
- headings: 黑体
- heading 1: 四号
- headings 2-4: 小四
- numbering: `一、`, `（一）`, `1.`, `（1）`
- figure and table text: 五号

If the body area contains ordinary body paragraphs whose Chinese font differs from default 宋体, do not auto-switch. Report the font as a candidate and ask the user whether to use it. If confirmed, make it the single body font for all generated body text.

## Material Classification

Use materials as evidence, not as decoration:

- `template`: report template files
- `guidance`: experiment instructions, requirements, task descriptions, grading requirements
- `source-code`: code, notebooks, scripts, build/run files
- `results`: CSV/spreadsheets/logs/model outputs
- `figures`: screenshots, plots, diagrams, result images
- `other`: supporting files that need user interpretation

Do not rely on a single filename substring as decisive evidence. For PDF/DOCX guidance files, inspect extracted text for signals such as `实验目的`, `实验步骤`, `实验要求`, `实验准备`, `问题背景`, and `提交要求`.

When there is a conflict between a draft and raw material, prefer raw material or ask the user.

## Outline Gate

The outline should show:

- heading hierarchy and numbering plan
- which materials support each section
- missing results or missing figures
- figure and table descriptions that need confirmation
- personal fields that will be filled or preserved
- confirmed format requirements
- intended figure placement by section

Do not call the writer script without explicit user approval of the outline.

## Figure And Table Handling

Generate `figure-summary.md` for image materials and `table-summary.md` for CSV/spreadsheet materials before drafting the outline.

For every figure/table used in the report, include nearby prose that explains:

- what it shows
- key visible observations or extracted values
- what part of the experiment it supports
- what cannot be concluded without additional data

Image descriptions must be based on inspected image content, surrounding filenames, generated plot titles, or user confirmation. If the image cannot be inspected, mark the description as `待确认`. Table descriptions must cite extracted rows, columns, or values from the data file.

## Personal Info Handling

Detect likely fields: experiment name, name, student ID, class, date, course, teacher.

Ask once with all detected fields. Accept partial answers. Blank fields remain placeholders.

When writing:

- save confirmed values to `personal-info.json`
- prefer table cells, existing runs, tab stops, and underlines over space padding
- preserve the original run style if replacing text
- use visual-width spacing only when the original template is clearly space-aligned

## DOCX Write Strategy

Default to copying the template and filling matching sections in place. This best preserves:

- page settings and margins
- headers, footers, and page numbers
- existing styles and numbering definitions
- embedded media and relationships

The writer should:

- locate top-level template headings
- remove blank or placeholder paragraphs under each matched heading
- insert matching content under that heading
- preserve the template heading paragraphs
- apply confirmed fonts and sizes to new headings/body text
- insert images close to the relevant paragraphs, not as a generic appendix

Use append fallback only when matching headings cannot be found.

Never overwrite the source template. Never write final output before outline approval.

## Final Checklist

Before returning the finished report, verify:

- title levels match the approved outline
- numbering is continuous and uses the selected patterns
- content appears below the matching template sections, not duplicated at the end
- figures appear in the relevant sections
- every included figure/table has adjacent descriptive prose
- result claims are backed by user materials
- missing data remains marked as placeholder
- personal fields are either filled from user input or left unchanged
- template file was not overwritten
- final `.docx` opens as a valid ZIP package
