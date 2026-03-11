#!/usr/bin/env python3
"""
Split koko-script files by track into male/female folder structure.
Output: {level}/{lang}/male/{TRACK}.txt
"""

import re
import os

# Track prefixes to track name mapping
TRACK_PREFIXES = {
    "PI": "PI",
    "TR": "TR",
    "KD": "KD",
    "KP": "KP",
    "CR": "CR",
    "CL": "CL",      # en: Campus Life
    "ST": "ST",      # ja: Street
    "FAM": "FAM",    # es: Family
    "AV": "AV",      # fr: Aventure
}

# Story header pattern: # PI-1: ..., # TR-2: ..., etc.
STORY_HEADER = re.compile(r"^(?:\d+#[A-Z]{2}\|)?# ([A-Z]{2,4})-\d+\s*:\s*(.+)$")

# Track header pattern: # 💖 PERSONAL INTEREST ... or # ✈️ TRAVELING ...
TRACK_HEADER = re.compile(r"^(?:\d+#[A-Z]{2}\|)?# [^\w]*[A-Z]")

# Level header pattern: # A0 ... or # A1 ...
LEVEL_HEADER = re.compile(r"^(?:\d+#[A-Z]{2}\|)?# A[01] ")


def get_track(story_id: str) -> str:
    """Extract track from story ID like PI-1 → PI"""
    return story_id.rsplit("-", 1)[0]


def split_file(input_path: str, output_dir: str):
    """Split a single file into track files."""
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    
    # Find all story start positions
    stories = []  # (track, start_line_idx)
    for i, line in enumerate(lines):
        m = STORY_HEADER.match(line)
        if m:
            story_id = m.group(1)
            track = get_track(story_id)
            stories.append((track, i))
    
    if not stories:
        print(f"  ⚠️  No stories found in {input_path}")
        return {}
    
    # Group lines by track
    tracks = {}  # track -> [lines]
    for idx, (track, start) in enumerate(stories):
        # End is next story start (or find track header before it) or EOF
        if idx + 1 < len(stories):
            end = stories[idx + 1][1]
            # Walk backwards from next story to find track header
            # and include it only for the first story of that track
        else:
            end = len(lines)
        
        if track not in tracks:
            tracks[track] = []
            # Look backwards from this story for track header (💖, ✈️, etc.)
            for j in range(start - 1, max(start - 5, -1), -1):
                if j >= 0 and TRACK_HEADER.match(lines[j]) and not LEVEL_HEADER.match(lines[j]):
                    tracks[track].append(lines[j])
                    tracks[track].append("")
                    break
        
        # Add all lines from this story
        story_lines = lines[start:end]
        # Remove trailing empty lines
        while story_lines and story_lines[-1].strip() == "":
            story_lines.pop()
        tracks[track].extend(story_lines)
        tracks[track].append("")  # blank line between stories
    
    # Write track files
    os.makedirs(output_dir, exist_ok=True)
    result = {}
    for track, track_lines in tracks.items():
        # Remove trailing empty lines
        while track_lines and track_lines[-1].strip() == "":
            track_lines.pop()
        
        filepath = os.path.join(output_dir, f"{track}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(track_lines) + "\n")
        
        story_count = sum(1 for l in track_lines if STORY_HEADER.match(l))
        result[track] = story_count
        print(f"    {track}.txt ({story_count} stories)")
    
    return result


def get_input_path(base: str, level: str, lang: str, gender: str = None) -> str:
    """Get the input file path, handling special cases for es/fr."""
    if gender == "female":
        return os.path.join(base, level, lang, "female.txt")
    return os.path.join(base, level, f"{lang}.txt")


def main():
    base = os.path.expanduser("~/koko-script")
    langs = ["ko", "ja", "en", "es", "fr", "zh"]
    levels = ["a0", "a1"]
    
    print("Splitting scripts by track...\n")
    
    for lang in langs:
        print(f"[{lang.upper()}]")
        for level in levels:
            # Male version (main file)
            input_path = get_input_path(base, level, lang)
            if os.path.exists(input_path):
                output_dir = os.path.join(base, level, lang, "male")
                print(f"  {level}/male:")
                split_file(input_path, output_dir)
            
            # Female version (es/fr only, a0 only for now)
            if lang in ("es", "fr"):
                female_path = get_input_path(base, level, lang, "female")
                if os.path.exists(female_path):
                    output_dir = os.path.join(base, level, lang, "female")
                    print(f"  {level}/female:")
                    split_file(female_path, output_dir)
        
        # Create empty female folder if not exists
        for level in levels:
            female_dir = os.path.join(base, level, lang, "female")
            if not os.path.exists(female_dir):
                os.makedirs(female_dir, exist_ok=True)
                print(f"  {level}/female: (empty - to be created)")
        
        print()
    
    print("🎉 Done!")


if __name__ == "__main__":
    main()
