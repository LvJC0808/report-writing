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

Record low-confidence items under `unknown` or ask the user before writing.

## Material Classification

Use materials as evidence, not as decoration:

- guidance documents: purpose, principle, tasks, grading requirements
- code: algorithm, key functions, environment, run method
- README: setup and command sequence
- logs: actual execution behavior and errors
- CSV/spreadsheets: result tables and metrics
- screenshots/images: result figures and visible evidence
- report drafts: wording source, not a trusted factual source by itself

When there is a conflict between a draft and raw material, prefer raw material or ask the user.

## Outline Gate

The outline should show:

- heading hierarchy and numbering plan
- which materials support each section
- missing results or missing figures
- personal fields that will be filled or preserved

Do not call the writer script without explicit user approval of the outline.

## Personal Info Handling

Detect likely fields: experiment name, name, student ID, class, date, course, teacher.

Ask once with all detected fields. Accept partial answers. Blank fields remain placeholders.

When writing:

- prefer table cells, existing runs, tab stops, and underlines over space padding
- preserve the original run style if replacing text
- use visual-width spacing only when the original template is clearly space-aligned

## DOCX Write Strategy

Default to copying the template and inserting report content into the copied file. This best preserves:

- page settings and margins
- headers, footers, and page numbers
- existing styles and numbering definitions
- embedded media and relationships

Use rebuild mode only when the template cannot be safely edited. Rebuild mode may lose exact page fidelity.

Never overwrite the source template. Never write final output before outline approval.

## Final Checklist

Before returning the finished report, verify:

- title levels match the approved outline
- numbering is continuous and uses the selected patterns
- result claims are backed by user materials
- missing data remains marked as placeholder
- personal fields are either filled from user input or left unchanged
- template file was not overwritten
- final `.docx` opens as a valid ZIP package
