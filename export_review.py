import os
import re

base = "/Users/jaeseunglee/koko-script"
out_dir = os.path.join(base, "review")
os.makedirs(out_dir, exist_ok=True)

theme_order = ["PI", "CR", "KD", "KP", "TR"]

for level in ["a0", "a1"]:
    for gender in ["male", "female"]:
        char_dir = os.path.join(base, level, "ko", gender)
        if not os.path.isdir(char_dir):
            continue
        for char in sorted(os.listdir(char_dir)):
            if char.startswith('.'):
                continue
            lines_out = []
            for theme in theme_order:
                fpath = os.path.join(char_dir, char, f"{theme}.txt")
                if not os.path.exists(fpath):
                    continue
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.readlines()
                
                theme_added = False
                for line in content:
                    stripped = line.strip()
                    # Episode header (# PI-1: ...)
                    if re.match(r'^#{1,3}\s+(PI|CR|KD|KP|TR)-\d+', stripped):
                        if not theme_added:
                            if lines_out:
                                lines_out.append("")
                            lines_out.append(f"{'='*40}")
                            lines_out.append(f" {theme}")
                            lines_out.append(f"{'='*40}")
                            theme_added = True
                        lines_out.append("")
                        # Clean header
                        clean = re.sub(r'^#{1,3}\s+', '', stripped)
                        lines_out.append(f"## {clean}")
                        lines_out.append("")
                    # Sim header
                    elif re.match(r'^#{1,3}\s+sim\d+', stripped):
                        clean = re.sub(r'^#{1,3}\s+', '', stripped)
                        lines_out.append(f"### {clean}")
                        lines_out.append("")
                    # Dialogue lines
                    elif stripped.startswith("AI:") or stripped.startswith("User:"):
                        lines_out.append(stripped)
            
            if lines_out:
                # Determine display name
                out_name = f"{level}_{char}.txt"
                with open(os.path.join(out_dir, out_name), "w", encoding="utf-8") as f:
                    f.write("\n".join(lines_out) + "\n")

print("Done!")
# List created files
for fn in sorted(os.listdir(out_dir)):
    if fn.endswith('.txt'):
        fpath = os.path.join(out_dir, fn)
        size = os.path.getsize(fpath)
        print(f"  {fn} ({size:,} bytes)")
