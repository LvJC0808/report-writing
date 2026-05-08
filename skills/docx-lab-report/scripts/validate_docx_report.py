#!/usr/bin/env python3
"""Validate a generated DOCX lab report before delivery."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

REQUIRED_PARTS = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}
IMAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"


@dataclass
class ValidationResult:
    path: str
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def fail(self, message: str) -> None:
        self.passed = False
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def parse_xml(package: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        data = package.read(name)
    except KeyError:
        return None
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        return None


def document_text(document_xml: ET.Element) -> str:
    parts = []
    for node in document_xml.iter():
        if node.tag in {f"{{{NS['w']}}}t", f"{{{NS['w']}}}delText"} and node.text:
            parts.append(node.text)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def normalize_text(text: str) -> str:
    text = re.sub(r"[#*_`>\-\[\]()]|!\[[^\]]*\]\([^)]+\)", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def outline_leak_candidates(outline: Path | None) -> list[str]:
    if not outline or not outline.exists():
        return []
    lines = []
    for raw_line in outline.read_text(encoding="utf-8").splitlines():
        line = normalize_text(raw_line)
        if len(line) >= 50:
            lines.append(line)
    return lines[:40]


def relationship_targets(package: zipfile.ZipFile, rels_name: str) -> list[tuple[str, str]]:
    rels_xml = parse_xml(package, rels_name)
    if rels_xml is None:
        return []
    targets = []
    base_dir = posixpath.dirname(posixpath.dirname(rels_name))
    for rel in rels_xml.findall("rel:Relationship", NS):
        rel_type = rel.attrib.get("Type", "")
        target = rel.attrib.get("Target", "")
        if rel_type != IMAGE_REL_TYPE or not target or target.startswith(("http://", "https://")):
            continue
        normalized = posixpath.normpath(posixpath.join(base_dir, target))
        targets.append((target, normalized))
    return targets


def load_summary(path: Path | None, result: ValidationResult) -> dict:
    if path is None:
        return {}
    if not path.exists():
        result.fail(f"write summary does not exist: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.fail(f"write summary is not valid JSON: {path}: {exc}")
        return {}


def validate_docx(
    output: Path,
    template: Path | None = None,
    outline: Path | None = None,
    summary_path: Path | None = None,
    allow_append: bool = False,
    required_text: list[str] | None = None,
) -> ValidationResult:
    result = ValidationResult(path=str(output))
    if not output.exists():
        result.fail(f"output does not exist: {output}")
        return result
    if template is not None and template.exists() and output.resolve() == template.resolve():
        result.fail("output path is the same as the template path")
        return result

    try:
        with zipfile.ZipFile(output) as package:
            bad_member = package.testzip()
            names = set(package.namelist())
            result.facts["part_count"] = len(names)
            result.facts["media_files"] = sorted(name for name in names if name.startswith("word/media/"))
            if bad_member:
                result.fail(f"corrupt ZIP member: {bad_member}")
            for part in sorted(REQUIRED_PARTS - names):
                result.fail(f"missing required DOCX part: {part}")

            document_xml = parse_xml(package, "word/document.xml")
            if document_xml is None:
                result.fail("word/document.xml is missing or not well-formed XML")
                text = ""
            else:
                text = document_text(document_xml)
                result.facts["document_text_chars"] = len(text)
                if "[缺少图片：" in text:
                    result.fail("document contains missing-image placeholder text")
                for snippet in required_text or []:
                    normalized = normalize_text(snippet)
                    if normalized and normalized not in text:
                        result.fail(f"required text not found: {normalized[:80]}")
                leaked = [candidate for candidate in outline_leak_candidates(outline) if candidate in text]
                if leaked:
                    result.fail(f"outline text appears copied into final report: {leaked[0][:100]}")

            image_targets = relationship_targets(package, "word/_rels/document.xml.rels")
            missing_targets = [target for _, target in image_targets if target not in names]
            result.facts["image_relationships"] = [target for _, target in image_targets]
            if missing_targets:
                result.fail(f"image relationship target missing from package: {missing_targets[0]}")
    except zipfile.BadZipFile:
        result.fail(f"output is not a valid ZIP/DOCX package: {output}")
        return result

    summary = load_summary(summary_path, result)
    if summary:
        result.facts["write_summary"] = summary
        if summary.get("mode_used") == "append" and not allow_append:
            result.fail("writer used append mode; rerun with --allow-append only after user disclosure")
        elif summary.get("append_fallback_used") and not allow_append:
            result.fail("writer used append fallback; rerun with --allow-append only after user disclosure")
        missing_images = summary.get("missing_images") or []
        if missing_images:
            result.fail(f"writer reported missing images: {missing_images[0]}")

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Generated DOCX report")
    parser.add_argument("--template", type=Path, help="Source DOCX template")
    parser.add_argument("--outline", type=Path, help="Approved outline markdown")
    parser.add_argument("--summary", type=Path, help="Writer summary JSON")
    parser.add_argument("--json-out", type=Path, help="Write validation result JSON")
    parser.add_argument("--allow-append", action="store_true", help="Allow reports produced with append fallback")
    parser.add_argument("--required-text", action="append", default=[], help="Text snippet that must appear in the report")
    args = parser.parse_args(argv)

    result = validate_docx(
        output=args.output,
        template=args.template,
        outline=args.outline,
        summary_path=args.summary,
        allow_append=args.allow_append,
        required_text=args.required_text,
    )
    payload = {
        "path": result.path,
        "passed": result.passed,
        "errors": result.errors,
        "warnings": result.warnings,
        "facts": result.facts,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    status = "PASSED" if result.passed else "FAILED"
    print(f"validation {status}: {args.output}")
    for error in result.errors:
        print(f"error: {error}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
