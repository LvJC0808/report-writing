# DOCX Lab Report Safety Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a self-contained DOCX safety layer to `docx-lab-report` so generated lab reports are validated as Office ZIP/XML packages before delivery.

**Architecture:** Keep the lab-report workflow in `SKILL.md`, keep detailed heuristics in `references/docx-workflow.md`, and put deterministic checks in Python scripts. The writer emits a sidecar summary, the profiler exposes page/package facts, and a new validator checks package integrity, relationships, outline leakage, media, and missing placeholders.

**Tech Stack:** Python standard library, `python-docx`, Codex skill format, `zipfile`, `xml.etree.ElementTree`.

---

### Task 1: Add DOCX Report Validator

**Files:**
- Create: `skills/docx-lab-report/scripts/validate_docx_report.py`

**Step 1: Implement validator**

Create a Python CLI that accepts:

```bash
python3 skills/docx-lab-report/scripts/validate_docx_report.py OUTPUT.docx \
  --template TEMPLATE.docx \
  --outline report-outline.md \
  --summary report-write-summary.json
```

It should:

- fail if output is not a readable ZIP file
- fail if `[Content_Types].xml`, `_rels/.rels`, or `word/document.xml` is missing
- parse XML safely with `xml.etree.ElementTree`
- collect document text from `word/document.xml`
- fail if document text contains `[缺少图片：`
- fail if a non-trivial outline text block appears in the final report
- verify image relationships in `word/_rels/document.xml.rels` point to existing package files
- fail if the sidecar summary says append fallback was used unless `--allow-append` is passed
- print a concise human-readable summary and optionally write JSON via `--json-out`

**Step 2: Run invalid-file check**

Run:

```bash
python3 skills/docx-lab-report/scripts/validate_docx_report.py /tmp/not-a-report.docx
```

Expected: non-zero exit with a readable "file does not exist" or invalid package error.

**Step 3: Compile validator**

Run:

```bash
python3 -m py_compile skills/docx-lab-report/scripts/validate_docx_report.py
```

Expected: exit 0.

### Task 2: Strengthen Template Profiling

**Files:**
- Modify: `skills/docx-lab-report/scripts/profile_docx_template.py`

**Step 1: Add package facts**

Enhance `build_profile()` to include:

- `package.parts`: selected package names for `word/*.xml`, `word/_rels/*.rels`, and `word/media/*`
- `package.has_headers`
- `package.has_footers`
- `package.has_numbering`
- `package.media_files`
- `package.document_relationship_targets`

**Step 2: Add page content width**

Use `w:pgSz` and `w:pgMar` from `parse_page_settings()` to compute `content_width_dxa` when values are numeric.

**Step 3: Verify profiler output**

Run:

```bash
python3 skills/docx-lab-report/scripts/profile_docx_template.py ML/实验报告.docx --out /tmp/format-profile.json
python3 -m json.tool /tmp/format-profile.json | sed -n '1,120p'
```

Expected: JSON includes `package` and `page_settings.content_width_dxa` when the sample template is available.

### Task 3: Emit Writer Summary And Safer Image Width

**Files:**
- Modify: `skills/docx-lab-report/scripts/write_docx_report.py`

**Step 1: Add page-width helper**

Read template page width and margins from the loaded `Document` sections. Compute a safe image width as the smaller of 5.6 inches and the section content width.

**Step 2: Track write facts**

Track:

- output path
- template path
- mode requested
- mode used
- matched section count
- inserted image paths
- missing image paths
- whether append fallback was used

**Step 3: Write sidecar summary**

Add `--summary-out`, defaulting to `<output-stem>.write-summary.json`, and write the tracked facts as JSON after saving.

**Step 4: Verify refusal gate remains**

Run:

```bash
python3 skills/docx-lab-report/scripts/write_docx_report.py \
  --template ML/实验报告.docx \
  --outline ML/report-outline.md \
  --content ML/report-content.md \
  --out /tmp/report.docx
```

Expected: non-zero exit requiring `--outline-approved`.

### Task 4: Update Skill Documentation

**Files:**
- Modify: `skills/docx-lab-report/SKILL.md`
- Modify: `skills/docx-lab-report/references/docx-workflow.md`

**Step 1: Update required workflow**

Add the validation command after the writer command:

```bash
python3 <skill>/scripts/validate_docx_report.py OUTPUT.docx \
  --template TEMPLATE.docx \
  --outline report-outline.md \
  --summary OUTPUT.write-summary.json
```

State that final delivery requires a fresh successful validation run.

**Step 2: Update reference checklist**

Add DOCX package checks, image relationship checks, missing-placeholder checks, append fallback disclosure, and sidecar summary review to the final checklist.

### Task 5: Run Full Verification

**Files:**
- Validate: `skills/docx-lab-report/`

**Step 1: Validate skill format**

Run:

```bash
python3 /home/lewis/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/docx-lab-report
```

Expected: `Skill is valid!`

**Step 2: Compile scripts**

Run:

```bash
python3 -m py_compile \
  skills/docx-lab-report/scripts/profile_docx_template.py \
  skills/docx-lab-report/scripts/inventory_materials.py \
  skills/docx-lab-report/scripts/write_docx_report.py \
  skills/docx-lab-report/scripts/validate_docx_report.py
```

Expected: exit 0.

**Step 3: Run representative commands**

Run the invalid validator check and writer refusal check from earlier tasks.

Expected: both fail for the expected reason.

### Task 6: Sync And Commit

**Files:**
- Sync: `/home/lewis/.codex/skills/docx-lab-report/`
- Commit: only intended skill and plan files

**Step 1: Sync installed skill**

Run:

```bash
rsync -a --exclude __pycache__ skills/docx-lab-report/ /home/lewis/.codex/skills/docx-lab-report/
```

Expected: installed copy updated.

**Step 2: Validate installed copy**

Run:

```bash
python3 /home/lewis/.codex/skills/.system/skill-creator/scripts/quick_validate.py /home/lewis/.codex/skills/docx-lab-report
```

Expected: `Skill is valid!`

**Step 3: Commit**

Run:

```bash
git add docs/plans/2026-05-08-docx-lab-report-safety-implementation.md skills/docx-lab-report
git commit -m "Add docx lab report safety validation"
```

Expected: commit succeeds, with `ML/` still untracked.
