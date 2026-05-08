#!/usr/bin/env python3
"""Write a DOCX report only after the report outline has been approved."""

from __future__ import annotations

import argparse
import html
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


BODY_CLOSE = b"</w:body>"
SECT_PR = b"<w:sectPr"


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def paragraphs_from_markdown(text: str) -> list[tuple[str, str]]:
    paragraphs: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            paragraphs.append(("title", line[2:].strip()))
        elif line.startswith("## "):
            paragraphs.append(("heading1", line[3:].strip()))
        elif line.startswith("### "):
            paragraphs.append(("heading2", line[4:].strip()))
        elif line.startswith("- "):
            paragraphs.append(("body", line[2:].strip()))
        elif line.startswith("```"):
            continue
        else:
            paragraphs.append(("body", line))
    return paragraphs


def ooxml_paragraph(style: str, text: str) -> str:
    escaped = html.escape(text, quote=False)
    if style == "title":
        return (
            "<w:p><w:pPr><w:jc w:val=\"center\"/></w:pPr>"
            "<w:r><w:rPr><w:b/><w:sz w:val=\"32\"/><w:szCs w:val=\"32\"/></w:rPr>"
            f"<w:t>{escaped}</w:t></w:r></w:p>"
        )
    if style == "heading1":
        return (
            "<w:p><w:r><w:rPr><w:b/><w:rFonts w:eastAsia=\"黑体\"/>"
            "<w:sz w:val=\"28\"/><w:szCs w:val=\"28\"/></w:rPr>"
            f"<w:t>{escaped}</w:t></w:r></w:p>"
        )
    if style == "heading2":
        return (
            "<w:p><w:r><w:rPr><w:b/><w:rFonts w:eastAsia=\"黑体\"/>"
            "<w:sz w:val=\"24\"/><w:szCs w:val=\"24\"/></w:rPr>"
            f"<w:t>{escaped}</w:t></w:r></w:p>"
        )
    return (
        "<w:p><w:r><w:rPr><w:rFonts w:eastAsia=\"宋体\"/>"
        "<w:sz w:val=\"24\"/><w:szCs w:val=\"24\"/></w:rPr>"
        f"<w:t>{escaped}</w:t></w:r></w:p>"
    )


def build_append_xml(outline: str, content: str, include_outline: bool = False) -> bytes:
    merged = []
    if include_outline:
        merged.extend([("heading1", "经确认的大纲"), *paragraphs_from_markdown(outline)])
    merged.extend(paragraphs_from_markdown(content))
    xml = "".join(ooxml_paragraph(style, text) for style, text in merged if text)
    return xml.encode("utf-8")


def fill_experiment_name(document_xml: bytes, experiment_name: str | None) -> bytes:
    if not experiment_name:
        return document_xml
    import re

    text = document_xml.decode("utf-8")
    escaped = html.escape(experiment_name, quote=False)
    pattern = re.compile(
        r"(<w:p\b(?:(?!</w:p>).)*?<w:t(?:\s[^>]*)?>\s*实验</w:t>"
        r"(?:(?!</w:p>).)*?<w:t(?:\s[^>]*)?>名称</w:t>"
        r"(?:(?!</w:p>).)*?<w:t[^>]*xml:space=\"preserve\">)"
        r"[\s\u00a0]*"
        r"(</w:t>)",
        flags=re.DOTALL,
    )
    updated, count = pattern.subn(rf"\1{escaped}\2", text, count=1)
    if count == 0:
        print("warning: could not locate experiment-name placeholder", file=sys.stderr)
        return document_xml
    return updated.encode("utf-8")


def append_to_template(
    template: Path,
    out: Path,
    outline: str,
    content: str,
    include_outline: bool = False,
    experiment_name: str | None = None,
) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {out}")
    if template.resolve() == out.resolve():
        raise ValueError("output path must differ from template path")

    insertion = build_append_xml(outline, content, include_outline=include_outline)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp_path = Path(tmp.name)

    try:
        with zipfile.ZipFile(template) as src, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename == "word/document.xml":
                    data = fill_experiment_name(data, experiment_name)
                    marker = data.rfind(SECT_PR)
                    if marker == -1:
                        marker = data.rfind(BODY_CLOSE)
                    if marker == -1:
                        raise ValueError("word/document.xml does not contain an insertion point")
                    data = data[:marker] + insertion + data[marker:]
                dst.writestr(item, data)
        shutil.move(str(tmp_path), out)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def rebuild_with_python_docx(out: Path, outline: str, content: str) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {out}")
    try:
        from docx import Document  # type: ignore
    except ImportError as exc:
        raise RuntimeError("rebuild mode requires python-docx to be installed") from exc

    document = Document()
    for style, text in [*paragraphs_from_markdown(outline), *paragraphs_from_markdown(content)]:
        if style == "title":
            document.add_heading(text, level=0)
        elif style == "heading1":
            document.add_heading(text, level=1)
        elif style == "heading2":
            document.add_heading(text, level=2)
        else:
            document.add_paragraph(text)
    out.parent.mkdir(parents=True, exist_ok=True)
    document.save(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, help="Template .docx for copy-append mode")
    parser.add_argument("--outline", type=Path, required=True, help="Approved report outline markdown")
    parser.add_argument("--content", type=Path, required=True, help="Report content markdown")
    parser.add_argument("--profile", type=Path, help="Optional format-profile.json")
    parser.add_argument("--out", type=Path, required=True, help="Output .docx path")
    parser.add_argument("--mode", choices=("copy-append", "rebuild"), default="copy-append")
    parser.add_argument("--outline-approved", action="store_true", help="Required approval gate")
    parser.add_argument("--include-outline", action="store_true", help="Also append the approved outline")
    parser.add_argument("--experiment-name", help="Fill the template's experiment-name field when present")
    args = parser.parse_args(argv)

    if not args.outline_approved:
        print("error: refusing to write DOCX until --outline-approved is supplied", file=sys.stderr)
        return 2

    try:
        outline = read_text(args.outline)
        content = read_text(args.content)
        if args.mode == "copy-append":
            if args.template is None:
                raise ValueError("--template is required in copy-append mode")
            append_to_template(
                args.template,
                args.out,
                outline,
                content,
                include_outline=args.include_outline,
                experiment_name=args.experiment_name,
            )
        else:
            rebuild_with_python_docx(args.out, outline, content)
    except Exception as exc:  # noqa: BLE001 - command-line tool should report cleanly.
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
