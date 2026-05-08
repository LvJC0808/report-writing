# DOCX Lab Report Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a repository-tracked Codex skill that helps generate `.docx` lab reports from a Word template and experiment materials.

**Architecture:** Create `skills/docx-lab-report/` with a concise `SKILL.md`, deterministic helper scripts, and generated agent metadata. The skill guides Codex through template profiling, material summarization, missing-info detection, outline approval, and final `.docx` generation.

**Tech Stack:** Codex skill folder format, Python standard library for OOXML ZIP/XML inspection, optional `python-docx` when available for document creation.

---

### Task 1: Initialize Skill Skeleton

**Files:**
- Create: `skills/docx-lab-report/SKILL.md`
- Create: `skills/docx-lab-report/agents/openai.yaml`
- Create: `skills/docx-lab-report/scripts/`
- Create: `skills/docx-lab-report/references/`

**Step 1: Run skill initializer**

Run:

```bash
/home/lewis/.codex/skills/.system/skill-creator/scripts/init_skill.py docx-lab-report --path skills --resources scripts,references --interface display_name="DOCX Lab Report" --interface short_description="Generate DOCX lab reports from templates and experiment materials." --interface default_prompt="Use this skill to profile a DOCX lab report template, summarize experiment materials, confirm an outline, and generate a formatted report."
```

Expected: `skills/docx-lab-report/` exists with required files.

**Step 2: Inspect generated skeleton**

Run:

```bash
find skills/docx-lab-report -maxdepth 3 -type f | sort
```

Expected: `SKILL.md`, `agents/openai.yaml`, and resource folders are present.

### Task 2: Add DOCX Template Profiler

**Files:**
- Create: `skills/docx-lab-report/scripts/profile_docx_template.py`

**Step 1: Implement profiler**

Create a Python script that:

- Accepts `template.docx` and `--out format-profile.json`
- Reads `.docx` as a ZIP file
- Parses `word/document.xml`, `word/styles.xml`, `word/numbering.xml`, `word/settings.xml`
- Extracts paragraph text samples, style IDs, run fonts, run sizes, bold flags, alignment, numbering IDs, page settings, tables, image count, and likely personal-info fields
- Emits JSON with `confirmed`, `inferred`, `unknown`, `defaults`, and `personal_info_fields`
- Uses the agreed fallback title/numbering defaults when template evidence is missing

**Step 2: Verify profiler on sample template**

Run:

```bash
python3 skills/docx-lab-report/scripts/profile_docx_template.py report_template.docx --out /tmp/format-profile.json
```

Expected: exit 0 and JSON file created.

**Step 3: Inspect output**

Run:

```bash
python3 -m json.tool /tmp/format-profile.json | sed -n '1,120p'
```

Expected: readable profile with template path, defaults, paragraph samples, and personal-info fields.

### Task 3: Add Material Inventory Script

**Files:**
- Create: `skills/docx-lab-report/scripts/inventory_materials.py`

**Step 1: Implement inventory script**

Create a Python script that:

- Accepts material files/directories and `--out material-summary.md`
- Classifies guidance docs, code, README, logs, result data, images, spreadsheets, and report drafts by filename and extension
- Extracts concise text previews for text-like files
- Records binary files without reading contents
- Emits `material-summary.md` and a sibling `missing-info.md`
- Flags missing result data, screenshots, code, guidance docs, and personal information as applicable

**Step 2: Verify inventory script**

Run:

```bash
python3 skills/docx-lab-report/scripts/inventory_materials.py . --out /tmp/material-summary.md
```

Expected: exit 0 and both `/tmp/material-summary.md` and `/tmp/missing-info.md` created.

### Task 4: Add DOCX Writer Utility

**Files:**
- Create: `skills/docx-lab-report/scripts/write_docx_report.py`

**Step 1: Implement writer**

Create a Python script that:

- Accepts `--template`, `--outline`, `--content`, `--profile`, and `--out`
- Defaults to copying the template and inserting generated content at the end when safe
- Falls back to a minimal new `.docx` when `python-docx` is available and template-copy editing is not selected
- Preserves template by never overwriting input
- Refuses to run unless `--outline-approved` is supplied
- Leaves placeholders intact for missing result data and unfilled personal info

**Step 2: Verify refusal gate**

Run:

```bash
python3 skills/docx-lab-report/scripts/write_docx_report.py --template report_template.docx --outline /tmp/material-summary.md --content /tmp/material-summary.md --out /tmp/report.docx
```

Expected: non-zero exit with a message requiring `--outline-approved`.

### Task 5: Write Skill Instructions

**Files:**
- Modify: `skills/docx-lab-report/SKILL.md`
- Create: `skills/docx-lab-report/references/docx-workflow.md`

**Step 1: Write concise SKILL.md**

Include:

- Trigger-focused frontmatter
- Mandatory workflow
- Personal-info interaction rule
- Fact-generation boundary
- Outline approval gate
- Script usage commands
- Failure handling

**Step 2: Move detailed DOCX heuristics into reference**

Put longer details in `references/docx-workflow.md`:

- Format inference priorities
- Material classification
- Personal-info field handling
- DOCX write strategy
- Review checklist

### Task 6: Validate Skill

**Files:**
- Validate: `skills/docx-lab-report/`

**Step 1: Run skill validator**

Run:

```bash
/home/lewis/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/docx-lab-report
```

Expected: validation passes.

**Step 2: Run Python syntax checks**

Run:

```bash
python3 -m py_compile skills/docx-lab-report/scripts/profile_docx_template.py skills/docx-lab-report/scripts/inventory_materials.py skills/docx-lab-report/scripts/write_docx_report.py
```

Expected: exit 0.

**Step 3: Run representative script checks**

Run the commands from Tasks 2, 3, and 4 again.

Expected: profiler and inventory succeed; writer refuses without approval.

### Task 7: Commit Implementation

**Files:**
- Commit all new skill files and implementation plan

**Step 1: Inspect diff**

Run:

```bash
git diff --cached --stat
git diff --stat
```

Expected: only intended skill and plan files changed.

**Step 2: Commit**

Run:

```bash
git add docs/plans/2026-05-08-docx-lab-report-skill-implementation.md skills/docx-lab-report
git commit -m "Add docx lab report skill"
```

Expected: commit succeeds.
