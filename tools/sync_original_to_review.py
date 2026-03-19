import os
import re
import sys

BASE    = "/Users/jaeseunglee/koko-script"
DRY_RUN = "--apply" not in sys.argv

CHARACTERS = {
    "male":   ["domin", "hyunjun", "hangyeol", "taeo", "siyun"],
    "female": ["minji", "jia", "haneul", "yuna", "seoyeon"],
}
LEVELS = ["a0", "a1"]
TRACKS = ["CR", "KD", "KP", "PI", "TR"]

EPISODE_RE = re.compile(r'^#{1,3}\s+((?:CR|KD|KP|PI|TR)-\d+)', re.IGNORECASE)
SIM_RE     = re.compile(r'^#{1,3}\s+(sim\d+)\b',               re.IGNORECASE)
DIALOGUE_RE= re.compile(r'^(User|AI):')


def parse_original_dialogues(path):
    result  = {}
    cur_ep  = None
    cur_sim = None

    with open(path, encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            m = EPISODE_RE.match(s)
            if m:
                cur_ep  = m.group(1).upper()
                cur_sim = None
                continue
            m = SIM_RE.match(s)
            if m:
                cur_sim = m.group(1).lower()
                continue
            if cur_ep and cur_sim and DIALOGUE_RE.match(s):
                result.setdefault((cur_ep, cur_sim), []).append(s)

    return result


def sync_review(review_path, orig_dialogues, label):
    with open(review_path, encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    changes   = 0
    warnings  = 0
    cur_ep    = None
    cur_sim   = None
    ptr       = {}

    for raw in lines:
        s = raw.strip()

        m = EPISODE_RE.match(s)
        if m:
            cur_ep  = m.group(1).upper()
            cur_sim = None
            new_lines.append(raw)
            continue

        m = SIM_RE.match(s)
        if m:
            cur_sim = m.group(1).lower()
            new_lines.append(raw)
            continue

        if cur_ep and cur_sim and DIALOGUE_RE.match(s):
            key      = (cur_ep, cur_sim)
            src_list = orig_dialogues.get(key, [])

            if not src_list:
                print(f"  [WARN] {label}: {cur_ep}/{cur_sim} 원본에 없음 → 리뷰 유지: {s[:60]}")
                warnings += 1
                new_lines.append(raw)
                continue

            idx = ptr.get(key, 0)
            if idx >= len(src_list):
                print(f"  [DROP] {label}: {cur_ep}/{cur_sim} 원본 대사 소진 → 리뷰 라인 삭제: {s[:60]}")
                changes += 1
                continue

            replacement = src_list[idx]
            ptr[key] = idx + 1

            if replacement != s:
                if DRY_RUN and changes < 5:
                    print(f"    CHANGE [{cur_ep}/{cur_sim}]")
                    print(f"      리뷰: {s}")
                    print(f"      원본: {replacement}")
                changes += 1

            new_lines.append(replacement + "\n")
            continue

        new_lines.append(raw)

    for (ep, sim), idx in ptr.items():
        src_list = orig_dialogues.get((ep, sim), [])
        if idx < len(src_list):
            remaining = len(src_list) - idx
            print(f"  [WARN] {label}: {ep}/{sim} 원본에만 있는 대사 {remaining}개 → 수동 확인 필요")
            warnings += 1

    return "".join(new_lines), changes, warnings


def main():
    total_files    = 0
    total_changes  = 0
    total_warnings = 0
    skipped        = 0

    for gender, chars in CHARACTERS.items():
        for char in chars:
            for level in LEVELS:
                for track in TRACKS:
                    review_path = os.path.join(BASE, "review", char, f"{level}_{track}.txt")
                    orig_path   = os.path.join(BASE, level, "ko", gender, char, f"{track}.txt")

                    if not os.path.exists(review_path):
                        print(f"[SKIP] 리뷰 없음: {char}/{level}_{track}")
                        skipped += 1
                        continue
                    if not os.path.exists(orig_path):
                        print(f"[SKIP] 원본 없음: {char}/{level}/{track}")
                        skipped += 1
                        continue

                    label         = f"{char}/{level}/{track}"
                    orig_dialogues= parse_original_dialogues(orig_path)
                    new_content, changes, warns = sync_review(review_path, orig_dialogues, label)

                    total_files    += 1
                    total_changes  += changes
                    total_warnings += warns

                    if changes > 0 or warns > 0:
                        mode = "DRY" if DRY_RUN else "APPLY"
                        print(f"[{mode}] {label}: {changes}줄 변경, {warns}개 경고")

                    if not DRY_RUN and changes > 0:
                        with open(review_path, "w", encoding="utf-8") as f:
                            f.write(new_content)

    print()
    print("=" * 50)
    print(f"{'[DRY RUN] ' if DRY_RUN else '[APPLIED] '}완료")
    print(f"  처리 파일: {total_files}")
    print(f"  변경 줄:   {total_changes}")
    print(f"  경고:      {total_warnings}")
    print(f"  스킵:      {skipped}")
    if DRY_RUN:
        print()
        print("  실제 반영: python tools/sync_original_to_review.py --apply")
    print("=" * 50)


if __name__ == "__main__":
    main()
