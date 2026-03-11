#!/usr/bin/env python3
"""
Convert koko-script format (LINENUM#HASH|content) to clean Markdown for native feedback.
Adds a feedback comment box after each AI/User line.
"""

import re
import os
import sys

LANG_NAMES = {
    "ja": "Japanese",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese",
    "ko": "Korean",
}

FEEDBACK_PLACEHOLDER = "\n> 💬 **Feedback:** _(Add your comment here)_\n"


def strip_line_prefix(line: str) -> str:
    """Remove LINENUM#HASH| prefix if present."""
    # Matches patterns like: 123#AB| or just plain text
    match = re.match(r"^\d+#[A-Z]{2}\|(.*)$", line)
    if match:
        return match.group(1)
    return line


def is_dialogue_line(text: str) -> bool:
    """Return True if this line is an AI or User dialogue line."""
    return text.startswith("AI:") or text.startswith("User:")


def convert_file(input_path: str, output_path: str, lang: str, level: str):
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    lang_name = LANG_NAMES.get(lang, lang.upper())
    lines_out = []

    # Header
    lines_out.append(f"# {lang_name} {level.upper()} — Native Speaker Review\n\n")
    lines_out.append(
        f"> **Instructions for reviewers:** Please leave feedback after each dialogue line.\n"
        f"> Focus on: naturalness, vocabulary level, cultural accuracy, and any awkward phrasing.\n"
        f"> Mark lines that feel unnatural with ❌, good lines with ✅.\n\n"
    )
    lines_out.append("---\n\n")

    prev_was_dialogue = False

    for raw in raw_lines:
        raw = raw.rstrip("\n")
        text = strip_line_prefix(raw)

        if is_dialogue_line(text):
            # Add blank line before if previous was also dialogue (for readability)
            lines_out.append(f"{text}\n")
            lines_out.append(FEEDBACK_PLACEHOLDER)
            lines_out.append("\n")
            prev_was_dialogue = True
        else:
            lines_out.append(f"{text}\n")
            prev_was_dialogue = False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines_out)

    print(f"✅ {input_path} → {output_path}")


def main():
    base = os.path.expanduser("~/koko-script")
    review_base = os.path.join(base, "review")

    targets = [
        ("a0", "ja"), ("a0", "en"), ("a0", "es"), ("a0", "fr"), ("a0", "zh"),
        ("a1", "ja"), ("a1", "en"), ("a1", "es"), ("a1", "fr"), ("a1", "zh"),
    ]

    for level, lang in targets:
        input_path = os.path.join(base, level, f"{lang}.txt")
        output_path = os.path.join(review_base, level, f"{lang}.md")
        if not os.path.exists(input_path):
            print(f"⚠️  Skipping (not found): {input_path}")
            continue
        convert_file(input_path, output_path, lang, level)

    print(f"\n🎉 Done! Review files saved to: {review_base}/")


if __name__ == "__main__":
    main()
