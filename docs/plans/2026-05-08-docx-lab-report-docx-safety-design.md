# DOCX Lab Report DOCX Safety Design

## Goal

Upgrade `docx-lab-report` from a report-generation workflow into a lab-report workflow with an explicit DOCX safety layer. The skill should still be specific to Chinese or bilingual lab reports, but it should treat the final `.docx` as an Office ZIP/XML package that must be validated before delivery.

## Source Boundary

The local reference at `/home/lewis/mx/dcmtskl/document-skills/docx` is proprietary. This design does not copy its text, code, templates, or scripts. It only adopts general engineering principles that are not specific to that implementation:

- a DOCX file is a ZIP package containing XML and media parts
- generated files need package-level validation
- template edits should preserve existing document structure when possible
- fallbacks should be explicit and reviewable
- image and table insertion needs checks beyond "file was saved"

## Recommended Approach

Use a layered design:

- **Lab report workflow layer:** profile template, inventory materials, require format confirmation, require outline approval, write report, and review figure/table descriptions.
- **DOCX safety layer:** validate the generated package, inspect key XML and media relationships, catch missing images and accidental outline insertion, and report whether template sections were filled in place or append fallback was used.

This keeps the skill focused. It avoids becoming a general Word automation toolkit for tracked changes, comments, or arbitrary document editing.

## Component Changes

### Skill Instructions

Keep `SKILL.md` short and operational:

- require the final validation command after writing the report
- state that no completion claim is allowed until validation passes
- require explicit disclosure when append fallback is used
- keep detailed DOCX rules in `references/docx-workflow.md`

### Workflow Reference

Expand `references/docx-workflow.md` with practical DOCX checks:

- final `.docx` must open as a ZIP package
- `word/document.xml` must exist and contain generated content
- output must not overwrite the source template
- images referenced by the report must exist in `word/media/`
- included figures and tables must have adjacent prose
- fallback append mode must be reported to the user

### Template Profiler

Enhance `profile_docx_template.py` to expose the page and package facts that the writer and validator need:

- page width, height, margins, and computed content width in DXA
- media files and relationship targets
- whether headers, footers, numbering, styles, and tables are present

### Writer

Enhance `write_docx_report.py` without turning it into a general DOCX editor:

- use template page width and margins to choose a safe image width
- write a sidecar JSON summary describing output path, mode, matched section count, inserted images, missing images, and fallback use
- preserve the existing outline approval gate
- keep refusing to overwrite the source template or an existing output file

### Validator

Add a self-contained `validate_docx_report.py` using only the Python standard library:

- verify the output is a valid ZIP package
- verify required DOCX parts exist
- verify media relationship targets resolve to package files
- verify missing-image placeholders are absent
- verify a provided outline file was not accidentally copied into the final report
- optionally verify required text snippets are present
- emit JSON and a readable pass/fail summary

## Success Criteria

- The skill validation command passes.
- All Python scripts compile.
- The writer still refuses to run without `--outline-approved`.
- The new validator reports a controlled failure for a deliberately invalid `.docx`.
- The new validator can inspect a real generated report and return a clear pass/fail result.
- The installed skill copy under `/home/lewis/.codex/skills/docx-lab-report` is updated after repo changes.
