#!/usr/bin/env python3
"""Profile a DOCX lab-report template into a reviewable JSON format profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

DEFAULT_RULES = {
    "heading_levels": 4,
    "body": {
        "font_east_asia": "宋体",
        "font_ascii": "Times New Roman",
        "size": "小四",
    },
    "heading1": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": "四号",
        "numbering": "一、 二、 三、",
        "bold": True,
    },
    "heading2": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": "小四",
        "numbering": "（一） （二） （三）",
        "bold": True,
    },
    "heading3": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": "小四",
        "numbering": "1. 2. 3.",
        "bold": True,
    },
    "heading4": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": "小四",
        "numbering": "（1） （2） （3）",
        "bold": True,
    },
    "caption": {
        "font_east_asia": "宋体",
        "font_ascii": "Times New Roman",
        "size": "五号",
    },
    "table_text": {
        "font_east_asia": "宋体",
        "font_ascii": "Times New Roman",
        "size": "五号",
    },
}

PERSONAL_INFO_PATTERNS = {
    "experiment_name": r"(实验名称|实验题目|题目|项目名称)",
    "name": r"(姓名|学生姓名|Name)",
    "student_id": r"(学号|学生编号|Student\s*ID|ID[:：\s_])",
    "class": r"(班级|专业班级|Class)",
    "date": r"(实验日期|日期|Date|时间)",
    "course": r"(课程名称|课程[:：\s_]|Course)",
    "teacher": r"(指导教师|任课教师|教师[:：\s_]|Teacher|Instructor)",
}

HEADING_PATTERNS = [
    re.compile(r"^[一二三四五六七八九十]+、"),
    re.compile(r"^（[一二三四五六七八九十]+）"),
    re.compile(r"^\d+\."),
    re.compile(r"^（\d+）"),
]


def qn(local: str) -> str:
    return f"{{{NS['w']}}}{local}"


def read_xml(package: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        data = package.read(name)
    except KeyError:
        return None
    return ET.fromstring(data)


def attr_value(element: ET.Element | None, attr: str = "val") -> str | None:
    if element is None:
        return None
    return element.attrib.get(qn(attr))


def paragraph_text(paragraph: ET.Element) -> str:
    parts = []
    for text in paragraph.findall(".//w:t", NS):
        if text.text:
            parts.append(text.text)
    return "".join(parts).strip()


def run_profile(run: ET.Element) -> dict[str, Any]:
    rpr = run.find("w:rPr", NS)
    if rpr is None:
        return {}
    fonts = rpr.find("w:rFonts", NS)
    size = attr_value(rpr.find("w:sz", NS))
    profile: dict[str, Any] = {}
    if fonts is not None:
        profile["fonts"] = {
            key: fonts.attrib.get(qn(key))
            for key in ("ascii", "hAnsi", "eastAsia", "cs")
            if fonts.attrib.get(qn(key))
        }
    if size:
        profile["half_point_size"] = size
        try:
            profile["point_size"] = int(size) / 2
        except ValueError:
            pass
    if rpr.find("w:b", NS) is not None:
        profile["bold"] = True
    return profile


def paragraph_profile(paragraph: ET.Element) -> dict[str, Any]:
    text = paragraph_text(paragraph)
    ppr = paragraph.find("w:pPr", NS)
    profile: dict[str, Any] = {"text": text}
    if ppr is not None:
        style_id = attr_value(ppr.find("w:pStyle", NS))
        if style_id:
            profile["style_id"] = style_id
        jc = attr_value(ppr.find("w:jc", NS))
        if jc:
            profile["alignment"] = jc
        num_pr = ppr.find("w:numPr", NS)
        if num_pr is not None:
            profile["numbering"] = {
                "level": attr_value(num_pr.find("w:ilvl", NS)),
                "num_id": attr_value(num_pr.find("w:numId", NS)),
            }
        spacing = ppr.find("w:spacing", NS)
        if spacing is not None:
            profile["spacing"] = {
                key: spacing.attrib.get(qn(key))
                for key in ("before", "after", "line", "lineRule")
                if spacing.attrib.get(qn(key))
            }
        ind = ppr.find("w:ind", NS)
        if ind is not None:
            profile["indent"] = {
                key: ind.attrib.get(qn(key))
                for key in ("left", "right", "firstLine", "hanging", "firstLineChars")
                if ind.attrib.get(qn(key))
            }
    runs = [run_profile(run) for run in paragraph.findall("w:r", NS)]
    profile["runs"] = [item for item in runs if item][:4]
    return profile


def parse_styles(styles_xml: ET.Element | None) -> dict[str, Any]:
    if styles_xml is None:
        return {}
    styles: dict[str, Any] = {}
    for style in styles_xml.findall("w:style", NS):
        style_id = style.attrib.get(qn("styleId"))
        if not style_id:
            continue
        rpr = style.find("w:rPr", NS)
        ppr = style.find("w:pPr", NS)
        fonts = rpr.find("w:rFonts", NS) if rpr is not None else None
        style_info: dict[str, Any] = {
            "type": style.attrib.get(qn("type")),
            "name": attr_value(style.find("w:name", NS)),
            "based_on": attr_value(style.find("w:basedOn", NS)),
        }
        if fonts is not None:
            style_info["fonts"] = {
                key: fonts.attrib.get(qn(key))
                for key in ("ascii", "hAnsi", "eastAsia", "cs")
                if fonts.attrib.get(qn(key))
            }
        if rpr is not None:
            size = attr_value(rpr.find("w:sz", NS))
            if size:
                style_info["half_point_size"] = size
                try:
                    style_info["point_size"] = int(size) / 2
                except ValueError:
                    pass
            if rpr.find("w:b", NS) is not None:
                style_info["bold"] = True
        if ppr is not None:
            jc = attr_value(ppr.find("w:jc", NS))
            if jc:
                style_info["alignment"] = jc
        styles[style_id] = {k: v for k, v in style_info.items() if v is not None}
    return styles


def parse_numbering(numbering_xml: ET.Element | None) -> dict[str, Any]:
    if numbering_xml is None:
        return {}
    abstract: dict[str, Any] = {}
    for abstract_num in numbering_xml.findall("w:abstractNum", NS):
        abstract_id = abstract_num.attrib.get(qn("abstractNumId"))
        if abstract_id is None:
            continue
        levels = []
        for lvl in abstract_num.findall("w:lvl", NS):
            levels.append(
                {
                    "level": lvl.attrib.get(qn("ilvl")),
                    "format": attr_value(lvl.find("w:numFmt", NS)),
                    "text": attr_value(lvl.find("w:lvlText", NS)),
                    "start": attr_value(lvl.find("w:start", NS)),
                }
            )
        abstract[abstract_id] = levels
    nums = {}
    for num in numbering_xml.findall("w:num", NS):
        num_id = num.attrib.get(qn("numId"))
        if num_id is not None:
            nums[num_id] = attr_value(num.find("w:abstractNumId", NS))
    return {"abstract": abstract, "nums": nums}


def parse_page_settings(document_xml: ET.Element | None) -> dict[str, Any]:
    if document_xml is None:
        return {}
    sect = document_xml.find(".//w:sectPr", NS)
    if sect is None:
        return {}
    page: dict[str, Any] = {}
    size = sect.find("w:pgSz", NS)
    margin = sect.find("w:pgMar", NS)
    if size is not None:
        page["size"] = {
            key: size.attrib.get(qn(key))
            for key in ("w", "h", "orient")
            if size.attrib.get(qn(key))
        }
    if margin is not None:
        page["margin"] = {
            key: margin.attrib.get(qn(key))
            for key in ("top", "right", "bottom", "left", "header", "footer")
            if margin.attrib.get(qn(key))
        }
    return page


def detect_personal_fields(texts: list[str]) -> list[dict[str, str]]:
    fields = []
    for text in texts:
        normalized = re.sub(r"\s+", " ", text)
        for field, pattern in PERSONAL_INFO_PATTERNS.items():
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                fields.append({"field": field, "sample": normalized[:160]})
    deduped = {}
    for item in fields:
        deduped.setdefault((item["field"], item["sample"]), item)
    return list(deduped.values())


def likely_heading(paragraph: dict[str, Any]) -> bool:
    text = paragraph["text"]
    if not text or len(text) > 80:
        return False
    style = str(paragraph.get("style_id", "")).lower()
    if "heading" in style or style in {"1", "2", "3", "4"}:
        return True
    if any(pattern.search(text) for pattern in HEADING_PATTERNS):
        return True
    for run in paragraph.get("runs", []):
        if run.get("bold") and run.get("point_size", 0) >= 12:
            return True
    return False


def summarize_body_styles(paragraphs: list[dict[str, Any]]) -> dict[str, Any]:
    styles = Counter()
    sizes = Counter()
    fonts = Counter()
    for paragraph in paragraphs:
        if not paragraph["text"] or likely_heading(paragraph):
            continue
        if paragraph.get("style_id"):
            styles[paragraph["style_id"]] += 1
        for run in paragraph.get("runs", []):
            if run.get("point_size"):
                sizes[str(run["point_size"])] += 1
            for value in run.get("fonts", {}).values():
                fonts[value] += 1
    return {
        "common_style_ids": styles.most_common(5),
        "common_point_sizes": sizes.most_common(5),
        "common_fonts": fonts.most_common(5),
    }


def build_profile(template: Path) -> dict[str, Any]:
    if not template.exists():
        raise FileNotFoundError(template)
    if template.suffix.lower() != ".docx":
        raise ValueError(f"Expected a .docx file, got: {template}")

    with zipfile.ZipFile(template) as package:
        names = set(package.namelist())
        document_xml = read_xml(package, "word/document.xml")
        styles_xml = read_xml(package, "word/styles.xml")
        numbering_xml = read_xml(package, "word/numbering.xml")

    if document_xml is None:
        raise ValueError("DOCX package does not contain word/document.xml")

    paragraphs = [
        paragraph_profile(paragraph)
        for paragraph in document_xml.findall(".//w:p", NS)
        if paragraph_text(paragraph)
    ]
    texts = [paragraph["text"] for paragraph in paragraphs]
    heading_candidates = [p for p in paragraphs if likely_heading(p)]
    format_instruction_candidates = [
        text
        for text in texts
        if any(keyword in text for keyword in ("格式", "字号", "字体", "标题", "正文", "报告要求"))
    ][:20]
    table_count = len(document_xml.findall(".//w:tbl", NS))
    image_count = len([name for name in names if name.startswith("word/media/")])

    confirmed: dict[str, Any] = {
        "page_settings": parse_page_settings(document_xml),
        "table_count": table_count,
        "image_count": image_count,
    }
    inferred: dict[str, Any] = {
        "heading_candidates": heading_candidates[:30],
        "body_style_summary": summarize_body_styles(paragraphs),
        "format_instruction_candidates": format_instruction_candidates,
    }
    unknown = []
    if not heading_candidates:
        unknown.append("heading_style")
    if not format_instruction_candidates:
        unknown.append("explicit_format_instructions")
    if not parse_numbering(numbering_xml):
        unknown.append("numbering_rules")

    return {
        "template": str(template),
        "confirmed": confirmed,
        "inferred": inferred,
        "styles": parse_styles(styles_xml),
        "numbering": parse_numbering(numbering_xml),
        "personal_info_fields": detect_personal_fields(texts),
        "defaults": DEFAULT_RULES,
        "unknown": unknown,
        "paragraph_sample_count": len(paragraphs),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path, help="Path to a .docx report template")
    parser.add_argument("--out", type=Path, default=Path("format-profile.json"))
    args = parser.parse_args(argv)

    try:
        profile = build_profile(args.template)
    except Exception as exc:  # noqa: BLE001 - command-line tool should report cleanly.
        print(f"error: {exc}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
