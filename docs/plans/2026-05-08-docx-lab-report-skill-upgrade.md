# DOCX Lab Report Skill Upgrade Plan

**Goal:** Upgrade `docx-lab-report` from append-only report generation to reusable lab-report template filling.

**Architecture:** Keep the report-specific workflow, but make the writer operate on template sections in place. Use template profiling for suggestions, require explicit user confirmation for format requirements, simplify material inventory, and support generic personal-info and inline figure insertion.

**Tech Stack:** Python standard library, `python-docx` for DOCX section editing and image insertion, ZIP validation for package integrity.

---

### Task 1: Generalize Skill Instructions

**Files:**
- Modify: `skills/docx-lab-report/SKILL.md`
- Modify: `skills/docx-lab-report/references/docx-workflow.md`

**Steps:**
- Remove task-specific examples such as `--experiment-name "支持向量机（SVM）"`.
- Require a user-confirmed `format-requirements.json`.
- Replace `--experiment-name` with `--personal-info personal-info.json`.
- State that final writing must fill template sections in place.
- State that images should be inserted near relevant paragraphs or section content.

### Task 2: Simplify Material Inventory

**Files:**
- Modify: `skills/docx-lab-report/scripts/inventory_materials.py`

**Steps:**
- Reduce categories to `template`, `guidance`, `source-code`, `results`, `figures`, and `other`.
- Use filename only as weak evidence.
- For text-like files, inspect content preview.
- For PDFs, use `pdftotext` when available to inspect the first pages.
- For DOCX, extract text from `word/document.xml`.
- Stop using broad mechanical conditions like `if "实验" in name`.

### Task 3: Rewrite DOCX Writer

**Files:**
- Modify: `skills/docx-lab-report/scripts/write_docx_report.py`

**Steps:**
- Replace append-only behavior with section filling.
- Parse Markdown content into top-level sections, subsections, paragraphs, and inline image directives.
- Locate matching top-level headings in the template.
- Remove blank or placeholder paragraphs under each matched heading until the next top-level heading.
- Insert the matching section content after the template heading.
- Support `--personal-info personal-info.json`.
- Support `--format-requirements format-requirements.json`.
- Support Markdown image lines: `![caption](path/to/image.png)`.
- Keep `--mode append` fallback for templates without matching headings.

### Task 4: Validate With ML Example

**Files:**
- Use existing `ML/` artifacts but do not commit them.

**Steps:**
- Create generic `ML/personal-info.json`.
- Update `ML/report-content.md` with inline image directives.
- Generate a new report from the template.
- Verify:
  - document package is valid with `unzip -t`
  - no approved outline text appears in the final DOCX
  - template headings are filled in place
  - experiment name is filled from JSON
  - images exist in `word/media/`

### Task 5: Commit

**Files:**
- Commit only skill files and this plan.

**Steps:**
- Run skill validator and Python compile checks.
- Inspect `git status`.
- Commit with `Upgrade docx lab report template filling`.
