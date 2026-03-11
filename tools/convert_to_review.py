#!/usr/bin/env python3
"""
Convert track-split koko-script files to dialogue-only review .txt files.
Reads from: {level}/{lang}/male/*.txt
Output: review/{lang}-{level}.txt
"""

import re
import os
import glob

DIALOGUE = re.compile(r"^(AI|User):")
STORY_HEADER = re.compile(r"^(?:\d+#[A-Z]{2}\|)?# [A-Z]{2,4}-\d+\s*:")


def strip_line_prefix(line: str) -> str:
    match = re.match(r"^\d+#[A-Z]{2}\|(.*)$", line)
    return match.group(1) if match else line


def extract_dialogue(input_path: str) -> list:
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    out = []
    prev_was_dialogue = False
    for raw in raw_lines:
        text = strip_line_prefix(raw.rstrip("\n"))
        if STORY_HEADER.match(raw.rstrip("\n")) or STORY_HEADER.match(text):
            if out and out[-1] != "":
                out.append("")
            title = text.lstrip("# ").strip()
            out.append(f"[ {title} ]")
            out.append("")
            prev_was_dialogue = False
        elif DIALOGUE.match(text):
            role = text.split(":")[0]
            if prev_was_dialogue and role == "AI":
                out.append("")
            out.append(text)
            prev_was_dialogue = True
        else:
            prev_was_dialogue = False

    return out


def save_level(lang: str, level: str, base: str, output_dir: str):
    # Use male as default; fall back to female if no male exists
    male_dir = os.path.join(base, level, lang, "male")
    female_dir = os.path.join(base, level, lang, "female")
    
    if os.path.exists(male_dir) and glob.glob(os.path.join(male_dir, "*.txt")):
        source_dir = male_dir
    elif os.path.exists(female_dir) and glob.glob(os.path.join(female_dir, "*.txt")):
        source_dir = female_dir
    else:
        print(f"  ⚠️  No files: {level}/{lang}/")
        return

    track_files = sorted(glob.glob(os.path.join(source_dir, "*.txt")))
    
    all_lines = []
    for tf in track_files:
        lines = extract_dialogue(tf)
        all_lines.extend(lines)
        if all_lines and all_lines[-1] != "":
            all_lines.append("")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{lang}-{level}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))

    dialogue_count = sum(1 for l in all_lines if DIALOGUE.match(l))
    gender = "male" if "male" in source_dir else "female"
    print(f"  ✅  {lang} {level.upper()} ({gender}): {output_path} ({dialogue_count} lines)")


def main():
    base = os.path.expanduser("~/koko-script")
    output_dir = os.path.join(base, "review")
    langs = ["ja", "en", "es", "fr", "zh"]
    levels = ["a0", "a1"]

    print("Converting track files to dialogue-only review files...\n")
    for lang in langs:
        for level in levels:
            save_level(lang, level, base, output_dir)

    print(f"\n🎉 Done! Files saved to: {output_dir}/")


if __name__ == "__main__":
    main()
