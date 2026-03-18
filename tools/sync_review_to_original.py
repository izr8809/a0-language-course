"""
sync_review_to_original.py

리뷰 파일(review/{char}/{level}_{track}.txt)의 대사를
원본 파일(a{level}/ko/{gender}/{char}/{track}.txt)에 반영한다.

규칙:
- 리뷰 파일의 대사(User: / AI: 로 시작하는 줄)를 정답으로 사용
- 원본 파일의 메타데이터, Goal, Outro, 세트헤더, 장소 등은 그대로 유지
- 에피소드(# XX-N) + sim(## simN) 단위로 매칭 후 대사 순서대로 교체
- 대사 수 불일치 시 WARNING 출력하고 스킵

Usage:
    python tools/sync_review_to_original.py           # dry run (변경 미리보기)
    python tools/sync_review_to_original.py --apply   # 실제 파일 수정
"""

import os
import re
import sys

BASE = "/Users/jaeseunglee/koko-script"
DRY_RUN = "--apply" not in sys.argv

CHARACTERS = {
    "male":   ["domin", "hyunjun", "hangyeol", "taeo", "siyun"],
    "female": ["minji", "jia", "haneul", "yuna", "seoyeon"],
}
LEVELS  = ["a0", "a1"]
TRACKS  = ["CR", "KD", "KP", "PI", "TR"]


# ── 파싱 헬퍼 ────────────────────────────────────────────────

EPISODE_RE = re.compile(r'^#{1,3}\s+((?:CR|KD|KP|PI|TR)-\d+)', re.IGNORECASE)
SIM_RE      = re.compile(r'^#{1,3}\s+(sim\d+)\b',               re.IGNORECASE)
DIALOGUE_RE = re.compile(r'^(User|AI):')


def parse_review(path):
    """
    리뷰 파일 → { episode_key: { sim_key: [대사줄, ...] } }
    예) {"CR-1": {"sim1": ["AI: 안녕하세요!", "User: 네!"], ...}, ...}
    """
    result = {}
    cur_ep  = None
    cur_sim = None

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            stripped = line.strip()

            m = EPISODE_RE.match(stripped)
            if m:
                cur_ep  = m.group(1).upper()
                cur_sim = None
                result.setdefault(cur_ep, {})
                continue

            m = SIM_RE.match(stripped)
            if m:
                cur_sim = m.group(1).lower()
                if cur_ep:
                    result[cur_ep].setdefault(cur_sim, [])
                continue

            if cur_ep and cur_sim and DIALOGUE_RE.match(stripped):
                result[cur_ep][cur_sim].append(stripped)

    return result


def sync_original(orig_path, review_data, label):
    """
    원본 파일을 읽어서 대사 줄만 리뷰 데이터로 교체.
    대사 수 불일치 시 WARNING.
    반환값: (새 내용 문자열, 변경된 줄 수, 경고 수)
    """
    with open(orig_path, encoding="utf-8") as f:
        orig_lines = f.readlines()

    new_lines = []
    changes   = 0
    warnings  = 0

    cur_ep  = None
    cur_sim = None

    # 현재 sim에서 소비할 대사 포인터
    review_ptr  = {}   # (ep, sim) → index

    for raw in orig_lines:
        line     = raw.rstrip("\n")
        stripped = line.strip()

        # 에피소드 헤더
        m = EPISODE_RE.match(stripped)
        if m:
            cur_ep  = m.group(1).upper()
            cur_sim = None
            new_lines.append(raw)
            continue

        # sim 헤더
        m = SIM_RE.match(stripped)
        if m:
            cur_sim = m.group(1).lower()
            new_lines.append(raw)
            continue

        # 대사 줄
        if cur_ep and cur_sim and DIALOGUE_RE.match(stripped):
            key = (cur_ep, cur_sim)
            ep_data  = review_data.get(cur_ep, {})
            sim_data = ep_data.get(cur_sim, [])

            if not sim_data:
                # 리뷰에 해당 ep/sim 없음 → 원본 유지
                print(f"  [WARN] {label}: {cur_ep}/{cur_sim} 리뷰에 없음 → 원본 유지: {stripped[:60]}")
                warnings += 1
                new_lines.append(raw)
                continue

            idx = review_ptr.get(key, 0)
            if idx >= len(sim_data):
                print(f"  [DROP] {label}: {cur_ep}/{cur_sim} 리뷰에 없는 대사 삭제: {stripped[:60]}")
                changes += 1
                continue

            replacement = sim_data[idx]
            review_ptr[key] = idx + 1

            if replacement != stripped:
                if DRY_RUN and changes < 5:
                    # 처음 5개만 미리보기 출력
                    print(f"    CHANGE [{cur_ep}/{cur_sim}]")
                    print(f"      원본: {stripped}")
                    print(f"      리뷰: {replacement}")
                changes += 1

            # 들여쓰기 보존
            indent = len(raw) - len(raw.lstrip())
            new_lines.append(" " * indent + replacement + "\n")
            continue

        new_lines.append(raw)

    for (ep, sim), idx in review_ptr.items():
        sim_data = review_data.get(ep, {}).get(sim, [])
        if idx < len(sim_data):
            remaining = sim_data[idx:]
            print(f"  [WARN] {label}: {ep}/{sim} 리뷰에만 있는 대사 {len(remaining)}개 (원본에 없음) → 수동 확인 필요")
            warnings += 1

    return "".join(new_lines), changes, warnings


# ── 메인 ─────────────────────────────────────────────────────

def main():
    total_files   = 0
    total_changes = 0
    total_warnings= 0
    skipped       = 0

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

                    label        = f"{char}/{level}/{track}"
                    review_data  = parse_review(review_path)
                    new_content, changes, warns = sync_original(orig_path, review_data, label)

                    total_files   += 1
                    total_changes += changes
                    total_warnings+= warns

                    if changes > 0 or warns > 0:
                        mode = "DRY" if DRY_RUN else "APPLY"
                        print(f"[{mode}] {label}: {changes}줄 변경, {warns}개 경고")

                    if not DRY_RUN and changes > 0:
                        with open(orig_path, "w", encoding="utf-8") as f:
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
        print("  실제 반영하려면: python tools/sync_review_to_original.py --apply")
    print("=" * 50)


if __name__ == "__main__":
    main()
