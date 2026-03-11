#!/usr/bin/env python3
"""
Convert koko-script format (LINENUM#HASH|content) to clean plain text for native review.
Merges A0 + A1 into a single file per language under review/.
"""

import re
import os

LANG_NAMES = {
    "ja": "Japanese",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese",
    "ko": "Korean",
}

# Internal metadata lines not useful for native reviewers
STRIP_PATTERNS = [
    re.compile(r"^- (대분류|중분류|난이도|분류|카테고리|서브카테고리):"),
    re.compile(r"^- \d+턴 \(\d+세트"),
]


def strip_line_prefix(line: str) -> str:
    """Remove LINENUM#HASH| prefix if present."""
    match = re.match(r"^\d+#[A-Z]{2}\|(.*)$", line)
    if match:
        return match.group(1)
    return line


def should_strip(text: str) -> bool:
    for pat in STRIP_PATTERNS:
        if pat.match(text):
            return True
    return False


def file_to_lines(input_path: str) -> list:
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    out = []
    for raw in raw_lines:
        text = strip_line_prefix(raw.rstrip("\n"))
        if should_strip(text):
            continue
        out.append(text)
    return out


def merge_and_save(lang: str, base: str, output_dir: str):
    lang_name = LANG_NAMES.get(lang, lang.upper())
    a0_path = os.path.join(base, "a0", f"{lang}.txt")
    a1_path = os.path.join(base, "a1", f"{lang}.txt")

    lines = []
    lines.append(f"# {lang_name} Script — A0 + A1")
    lines.append("")
    lines.append("=" * 60)
    lines.append("")

    if os.path.exists(a0_path):
        lines.append("# ── A0 ──────────────────────────────────────────────")
        lines.append("")
        lines.extend(file_to_lines(a0_path))
        lines.append("")
    else:
        print(f"  ⚠️  A0 not found: {a0_path}")

    if os.path.exists(a1_path):
        lines.append("# ── A1 ──────────────────────────────────────────────")
        lines.append("")
        lines.extend(file_to_lines(a1_path))
        lines.append("")
    else:
        print(f"  ⚠️  A1 not found: {a1_path}")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{lang}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  ✅  {lang_name}: {output_path}")


def main():
    base = os.path.expanduser("~/koko-script")
    output_dir = os.path.join(base, "review")
    langs = ["ja", "en", "es", "fr", "zh"]

    print("Converting scripts to plain text review files...\n")
    for lang in langs:
        merge_and_save(lang, base, output_dir)

    print(f"\n🎉 Done! Files saved to: {output_dir}/")


if __name__ == "__main__":
    main()
