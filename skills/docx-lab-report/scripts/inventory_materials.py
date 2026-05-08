#!/usr/bin/env python3
"""Create a concise material inventory for a lab report task."""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".tsv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".py",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".js",
    ".ts",
    ".go",
    ".rs",
    ".m",
    ".r",
    ".sh",
    ".bat",
    ".log",
    ".out",
}

CODE_EXTENSIONS = {".py", ".java", ".c", ".cpp", ".h", ".hpp", ".js", ".ts", ".go", ".rs", ".m", ".r", ".sh"}
RESULT_EXTENSIONS = {".csv", ".tsv", ".xls", ".xlsx", ".ods", ".log", ".out"}
FIGURE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
DOC_EXTENSIONS = {".doc", ".docx", ".pdf", ".ppt", ".pptx"}
IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
IGNORE_FILES = {
    "format-profile.json",
    "format-requirements.json",
    "material-summary.md",
    "missing-info.md",
    "figure-summary.md",
    "table-summary.md",
    "personal-info.json",
    "report-outline.md",
    "report-content.md",
}
PREVIEW_LIMIT = 3000

GUIDANCE_SIGNALS = ("实验目的", "实验步骤", "实验要求", "实验准备", "问题背景", "提交要求", "实验内容")
TEMPLATE_SIGNALS = ("实验报告", "姓名", "学号", "实验名称")
RESULT_SIGNALS = ("accuracy", "precision", "recall", "f1", "roc_auc", "结果", "指标", "score", "metric")


@dataclass
class Material:
    path: Path
    category: str
    size: int
    preview: str = ""


def read_text_preview(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf_preview(path)
    if suffix == ".docx":
        return read_docx_preview(path)
    if suffix not in TEXT_EXTENSIONS:
        return ""
    try:
        data = path.read_bytes()[:PREVIEW_LIMIT]
    except OSError:
        return ""
    for encoding in ("utf-8", "gb18030", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return ""
    return clean_preview(text)


def read_pdf_preview(path: Path) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "5", "-layout", str(path), "-"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    return clean_preview(result.stdout[:PREVIEW_LIMIT])


def read_docx_preview(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as package:
            data = package.read("word/document.xml")
    except (OSError, KeyError, zipfile.BadZipFile):
        return ""
    root = ET.fromstring(data)
    texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
    return clean_preview("".join(texts)[:PREVIEW_LIMIT])


def clean_preview(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def contains_any(text: str, signals: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(signal.lower() in lowered for signal in signals)


def classify(path: Path, preview: str) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()

    if suffix in FIGURE_EXTENSIONS:
        return "figures"
    if suffix in CODE_EXTENSIONS:
        return "source-code"
    if suffix in DOC_EXTENSIONS:
        if contains_any(preview, TEMPLATE_SIGNALS) or "template" in name or "模板" in name:
            return "template"
        if contains_any(preview, GUIDANCE_SIGNALS):
            return "guidance"
        return "other"
    if suffix in RESULT_EXTENSIONS or contains_any(preview, RESULT_SIGNALS):
        return "results"

    if contains_any(preview, GUIDANCE_SIGNALS):
        return "guidance"
    if "readme" in name or "说明" in name:
        return "guidance"
    return "other"


def iter_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for input_path in inputs:
        if not input_path.exists():
            print(f"warning: missing input {input_path}", file=sys.stderr)
            continue
        if input_path.is_file():
            files.append(input_path)
            continue
        for root, dirs, filenames in os.walk(input_path):
            dirs[:] = [name for name in dirs if name not in IGNORE_DIRS]
            for filename in filenames:
                if filename in IGNORE_FILES or filename.endswith(":Zone.Identifier"):
                    continue
                files.append(Path(root) / filename)
    return sorted(set(files), key=lambda item: str(item))


def collect(inputs: list[Path]) -> list[Material]:
    materials = []
    for path in iter_files(inputs):
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        preview = read_text_preview(path)
        materials.append(Material(path=path, category=classify(path, preview), size=size, preview=preview))
    return materials


def write_summary(materials: list[Material], out: Path) -> None:
    lines = [
        "# Material Summary",
        "",
        "This file inventories available materials. Categories are intentionally broad; correct them manually when context says otherwise.",
        "",
    ]
    for category in ("template", "guidance", "source-code", "results", "figures", "other"):
        grouped = [material for material in materials if material.category == category]
        if not grouped:
            continue
        lines.extend([f"## {category}", ""])
        for material in grouped:
            lines.append(f"- `{material.path}` ({material.size} bytes)")
            if material.preview:
                lines.extend(["", "```text", material.preview[:1200], "```", ""])
        lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def missing_items(materials: list[Material]) -> list[str]:
    categories = {material.category for material in materials}
    missing = []
    if "template" not in categories:
        missing.append("未明确识别报告模板。")
    if "guidance" not in categories:
        missing.append("未明确识别实验指导书或实验要求。")
    if "source-code" not in categories:
        missing.append("未明确识别代码文件。")
    if "results" not in categories:
        missing.append("未明确识别实验结果、运行输出或结果数据；不得编造结果。")
    if "figures" not in categories:
        missing.append("未明确识别截图或结果图；如报告需要图示，应补充图片或保留占位。")
    missing.append("个人信息不猜测；检测到模板字段后必须询问用户是否填写。")
    return missing


def write_missing(materials: list[Material], out: Path) -> None:
    lines = ["# Missing Info", ""]
    for item in missing_items(materials):
        lines.append(f"- {item}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figure_summary(materials: list[Material], out: Path) -> None:
    figures = [material for material in materials if material.category == "figures"]
    if not figures:
        remove_stale_optional_output(out)
        return
    lines = [
        "# Figure Summary",
        "",
        "Review these figure descriptions before drafting the report. Replace `待确认` with inspected observations or user-confirmed descriptions.",
        "",
    ]
    for index, material in enumerate(figures, 1):
        stem = material.path.stem.replace("_", " ").replace("-", " ")
        lines.extend(
            [
                f"## 图{index}: {material.path.name}",
                "",
                f"- Path: `{material.path}`",
                f"- Filename signal: {stem}",
                "- Shows: 待确认",
                "- Key observations: 待确认",
                "- Supports section/conclusion: 待确认",
                "- Limits: Do not infer exact values unless visible in the image or backed by result data.",
                "",
            ]
        )
    out.write_text("\n".join(lines), encoding="utf-8")


def remove_stale_optional_output(out: Path) -> None:
    try:
        out.unlink()
    except FileNotFoundError:
        return
    except OSError:
        return


def csv_preview(path: Path) -> tuple[list[str], list[list[str]]]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            rows = []
            for row in reader:
                rows.append(row)
                if len(rows) >= 6:
                    break
    except UnicodeDecodeError:
        try:
            with path.open(newline="", encoding="gb18030") as handle:
                reader = csv.reader(handle, delimiter=delimiter)
                rows = []
                for row in reader:
                    rows.append(row)
                    if len(rows) >= 6:
                        break
        except OSError:
            return [], []
    except OSError:
        return [], []
    if not rows:
        return [], []
    return rows[0], rows[1:]


def write_table_summary(materials: list[Material], out: Path) -> None:
    tables = [
        material
        for material in materials
        if material.category == "results" and material.path.suffix.lower() in {".csv", ".tsv", ".xls", ".xlsx", ".ods"}
    ]
    if not tables:
        remove_stale_optional_output(out)
        return
    lines = [
        "# Table Summary",
        "",
        "Review these table descriptions before drafting the report. Cite extracted columns, rows, or values; do not invent rankings or metrics.",
        "",
    ]
    for index, material in enumerate(tables, 1):
        headers, rows = csv_preview(material.path) if material.path.suffix.lower() in {".csv", ".tsv"} else ([], [])
        lines.extend(
            [
                f"## 表{index}: {material.path.name}",
                "",
                f"- Path: `{material.path}`",
                f"- Columns: {', '.join(headers) if headers else '待确认'}",
                "- Key values/rows:",
            ]
        )
        if rows:
            for row in rows[:3]:
                lines.append(f"  - {', '.join(row[:8])}")
        else:
            lines.append("  - 待确认")
        lines.extend(
            [
                "- Description to include near table: 待确认",
                "- Supports section/conclusion: 待确认",
                "- Limits: Only claim values present in this file or confirmed by the user.",
                "",
            ]
        )
    out.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Material files or directories")
    parser.add_argument("--out", type=Path, default=Path("material-summary.md"))
    args = parser.parse_args(argv)

    materials = collect(args.inputs)
    write_summary(materials, args.out)
    missing_out = args.out.with_name("missing-info.md")
    write_missing(materials, missing_out)
    figure_out = args.out.with_name("figure-summary.md")
    table_out = args.out.with_name("table-summary.md")
    write_figure_summary(materials, figure_out)
    write_table_summary(materials, table_out)
    print(f"wrote {args.out}")
    print(f"wrote {missing_out}")
    if figure_out.exists():
        print(f"wrote {figure_out}")
    if table_out.exists():
        print(f"wrote {table_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
