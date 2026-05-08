#!/usr/bin/env python3
"""Create a material inventory and missing-info report for a lab report task."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


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
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
SPREADSHEET_EXTENSIONS = {".xls", ".xlsx", ".ods"}
DOC_EXTENSIONS = {".doc", ".docx", ".pdf", ".ppt", ".pptx"}
IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
IGNORE_FILES = {
    "format-profile.json",
    "material-summary.md",
    "missing-info.md",
    "report-outline.md",
    "report-content.md",
}
PREVIEW_LIMIT = 3000


@dataclass
class Material:
    path: Path
    category: str
    size: int
    preview: str = ""


def classify(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    stem = path.stem.lower()

    if suffix in IMAGE_EXTENSIONS:
        return "image-or-screenshot"
    if suffix in SPREADSHEET_EXTENSIONS or suffix in {".csv", ".tsv"}:
        return "result-data"
    if suffix in {".log", ".out"} or any(token in name for token in ("log", "output", "运行", "结果")):
        return "run-log-or-output"
    if suffix in {".py", ".java", ".c", ".cpp", ".h", ".hpp", ".js", ".ts", ".go", ".rs", ".m", ".r", ".sh"}:
        return "code"
    if "readme" in stem or "说明" in stem:
        return "readme-or-run-instructions"
    if suffix in DOC_EXTENSIONS and any(token in name for token in ("指导", "要求", "实验书", "instruction", "guide")):
        return "experiment-guidance"
    if suffix in DOC_EXTENSIONS and any(token in name for token in ("报告", "report", "草稿")):
        return "report-draft-or-template"
    if suffix in DOC_EXTENSIONS and "实验" in name:
        return "experiment-guidance"
    if suffix in DOC_EXTENSIONS:
        return "document"
    if suffix in TEXT_EXTENSIONS:
        return "text"
    return "binary-or-unknown"


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
                if filename in IGNORE_FILES:
                    continue
                path = Path(root) / filename
                if path.name.endswith(":Zone.Identifier"):
                    continue
                files.append(path)
    return sorted(set(files), key=lambda item: str(item))


def read_preview(path: Path) -> str:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
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
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def collect(inputs: list[Path]) -> list[Material]:
    materials = []
    for path in iter_files(inputs):
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        materials.append(
            Material(
                path=path,
                category=classify(path),
                size=size,
                preview=read_preview(path),
            )
        )
    return materials


def write_summary(materials: list[Material], out: Path) -> None:
    lines = [
        "# Material Summary",
        "",
        "This file inventories the experiment materials available for the report. It is not a final report draft.",
        "",
        "## Files",
        "",
    ]
    for material in materials:
        lines.append(f"- `{material.path}`")
        lines.append(f"  - Category: {material.category}")
        lines.append(f"  - Size: {material.size} bytes")
        if material.preview:
            preview = material.preview[:1200]
            lines.append("  - Preview:")
            lines.append("")
            lines.append("```text")
            lines.append(preview)
            lines.append("```")
        lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def missing_items(materials: list[Material]) -> list[str]:
    categories = {material.category for material in materials}
    missing = []
    if "experiment-guidance" not in categories:
        missing.append("实验指导书或实验要求文件未明确识别。")
    if "code" not in categories:
        missing.append("代码文件未明确识别。")
    if not ({"result-data", "run-log-or-output"} & categories):
        missing.append("实验结果、运行输出或结果数据未明确识别；不得编造结果。")
    if "image-or-screenshot" not in categories:
        missing.append("截图或结果图片未明确识别；如报告需要图示，应补充图片或保留占位。")
    missing.append("个人信息默认不猜测；检测到模板字段后必须询问用户是否填写。")
    return missing


def write_missing(materials: list[Material], out: Path) -> None:
    lines = ["# Missing Info", ""]
    for item in missing_items(materials):
        lines.append(f"- {item}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Material files or directories")
    parser.add_argument("--out", type=Path, default=Path("material-summary.md"))
    args = parser.parse_args(argv)

    materials = collect(args.inputs)
    write_summary(materials, args.out)
    missing_out = args.out.with_name("missing-info.md")
    write_missing(materials, missing_out)
    print(f"wrote {args.out}")
    print(f"wrote {missing_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
