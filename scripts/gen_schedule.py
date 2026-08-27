# -*- coding: utf-8 -*-
"""
从 Obsidian 道德经目录生成 shipinhao-automation/schedule.csv 的新条目。
默认从第 16 章开始，每天 6:30 和 21:00 各发一章。
"""
import csv
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

OBSIDIAN_DIR = Path("D:/myObsidian/03-books/02-Areas/道德经/chapters")
CSV_PATH = Path("C:/Users/28658/WorkBuddy/2026-07-31-13-17-15/shipinhao-automation/schedule.csv")
TOPICS = "#帛书版道德经 #正能量 #经典阅读 #国学"


def parse_chapter(md_path: Path):
    """从 md 文件提取 (chapter_no, title, description)。"""
    txt = md_path.read_text(encoding="utf-8")
    # chapter_no
    m = re.search(r"chapter_no:\s*(\d+)", txt)
    chapter_no = int(m.group(1)) if m else None
    # title（从 filename 提取 "第N章_xxx"）
    fname = md_path.stem  # e.g. "第16章_使我挈有知"
    m = re.match(r"第(\d+)章_(.+)", fname)
    if m:
        title = f"第{int(m.group(1)):02d}章 {m.group(2)}"
    else:
        title = fname
    # description = 原文摘录 + 白话对照
    sections = {}
    current = None
    for line in txt.split("\n"):
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current and line.strip():
            sections[current].append(line.strip())
    原文 = "\n".join(sections.get("原文摘录", []))
    白话 = "\n".join(sections.get("白话对照", []))
    description = 原文 + "\n\n" + 白话
    return chapter_no, title, description


def gen_schedule(start_chapter: int = 16, end_chapter: int = 30, start_date=None):
    """生成发布时间表：每天 6:30 + 21:00。"""
    if start_date is None:
        # 默认从 CSV 最后一条 done 的 scheduled_at 之后一天开始
        if CSV_PATH.exists():
            with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            done_rows = [r for r in rows if r.get("status") == "done" and r.get("scheduled_at")]
            if done_rows:
                last = max(done_rows, key=lambda r: r["scheduled_at"])
                last_dt = datetime.strptime(last["scheduled_at"], "%Y-%m-%d %H:%M")
                # +1 天开始，避免和 last 冲突
                start_date = last_dt + timedelta(days=1)
                print(f"CSV 最后 scheduled: {last['video_file']} @ {last_dt}, 从 +1 天 {start_date.date()} 开始")
        if start_date is None:
            start_date = datetime.now()
    items = []
    current_date = start_date.date()
    chap = start_chapter
    while chap <= end_chapter:
        # 早 6:30
        items.append((chap, current_date, 6, 30))
        chap += 1
        if chap > end_chapter:
            break
        # 晚 21:00
        items.append((chap, current_date, 21, 0))
        chap += 1
        current_date += timedelta(days=1)
    return items


def append_csv(items):
    """追加 CSV 行。"""
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["video_file", "title", "description", "topics",
                  "scheduled_at", "duration_sec", "status",
                  "published_at", "note"]
    existing = []
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
            existing = list(csv.DictReader(f))
    existing_files = {r["video_file"] for r in existing}

    new_rows = []
    for chap, date, h, m in items:
        fname = f"{chap}.mp4"
        if fname in existing_files:
            print(f"  跳过 {fname}（已在 CSV）")
            continue
        stem = f"第{chap:02d}章_" + _find_md_for_chapter(chap)
        md = OBSIDIAN_DIR / (stem + ".md")
        if not md.exists():
            print(f"  ⚠️  找不到 {md}")
            continue
        ch_no, title, desc = parse_chapter(md)
        scheduled = f"{date.strftime('%Y-%m-%d')} {h:02d}:{m:02d}"
        new_rows.append({
            "video_file": fname,
            "title": title,
            "description": desc,
            "topics": TOPICS,
            "scheduled_at": scheduled,
            "duration_sec": "",
            "status": "pending",
            "published_at": "",
            "note": "",
        })
        print(f"  + {fname} → {title} → {scheduled}")

    if not new_rows:
        print("无新行")
        return
    with open(CSV_PATH, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerows(new_rows)
    print(f"✅ 追加 {len(new_rows)} 行到 {CSV_PATH}")


def _find_md_for_chapter(chap_no):
    """从目录里找匹配第 N 章的 md 文件名。"""
    for f in OBSIDIAN_DIR.iterdir():
        m = re.match(rf"第{chap_no:02d}章_(.+)", f.stem)
        if m:
            return f.stem.replace(f"第{chap_no:02d}章_", "")
    return f"unknown{chap_no}.md"


if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 19  # 默认只生成 16-19（今天+明天）
    items = gen_schedule(start_chapter=start, end_chapter=end)
    print(f"生成 {len(items)} 条发布计划（{start} ~ {end} 章）")
    append_csv(items)