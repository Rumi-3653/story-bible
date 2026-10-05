#!/usr/bin/env python3
"""story-bible 設定卡工具(只用標準庫,Python 3.8+)。

  python scripts/bible.py check [卡或資料夾 ...]      體檢,預設掃 library/;有錯誤 exit 1
  python scripts/bible.py export <角色卡.md> [-o 檔]   角色卡 → emotion-shot-pipeline characters json

欄位語意見 references/欄位指南.md。
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["name", "age", "relations", "background", "personality",
            "appearance", "narrative_function", "arc"]

FIELD = re.compile(r"^-\s+\*\*(.+?)\*\*[^：:\n]*[：:]\s*(.*)$")   # - **欄位**(可夾說明)：值
SUB = re.compile(r"^[-*]\s+(.+?)\s*[：:]\s*(.+)$")                 # 縮排子項 - 對象：描述
NOTE = re.compile(r"^>\s*appearance_note\s*[：:]\s*(.*)$")
NEG_FLAG = re.compile(r"--(rate|pitch|volume)\s+-\d")
MEDIA = re.compile(r"`([^`]+\.(?:png|jpe?g|webp|gif|mp3|wav|m4a|flac|ogg))`", re.I)
DATED_LOG = re.compile(r"版本紀錄[\s\S]*?\d{4}-\d{2}-\d{2}")


def filled(v):
    """範本提示語(整格包在全形括號裡、或「從……走到……」骨架)視為未填。"""
    rest = re.sub(r"（[^）]*）", "", v or "").replace("…", "").strip()
    return rest not in ("", "從走到", "待補")


def clean(v):
    return (v or "").replace("（預設，可改）", "").strip()


class Card:
    def __init__(self, path):
        self.path = Path(path)
        self.text = self.path.read_text(encoding="utf-8")
        lines = self.text.splitlines()
        self.title = next((l for l in lines if l.startswith("# ")), "")
        self.fields, self.subs = {}, {}
        self.appearance, self.note = "", ""
        field = section = None
        for line in lines:
            if line.startswith("#"):
                section, field = line.lstrip("#").strip(), None
                continue
            m = NOTE.match(line.strip())
            if m:
                self.note = m.group(1).strip()
                continue
            if section and section.startswith("外貌") and line.strip() and not line.startswith(">"):
                self.appearance = (self.appearance + "\n" + line.strip()).strip()
                continue
            m = FIELD.match(line)
            if m:
                field = m.group(1).strip()
                self.fields.setdefault(field, m.group(2).strip())
                self.subs.setdefault(field, [])
            elif field and line[:1] in (" ", "\t") and line.strip():
                self.subs[field].append(line.strip())
            elif line.strip():
                field = None

    @property
    def kind(self):
        for k in ("角色卡", "場景卡", "世界觀"):
            if self.title.startswith("# " + k):
                return k
        return None

    def get(self, name):
        """單行值;值空著但下面有縮排條列(性格常這樣寫)就把條列併起來。"""
        v = self.fields.get(name, "")
        if filled(v):
            return clean(v)
        items = (re.sub(r"^(?:[-*]|\d+\.)\s+", "", s) for s in self.subs.get(name, []))
        return clean("\n".join(i for i in items if filled(i)))


def media_errors(card):
    """反引號裡含路徑分隔符的圖/音檔路徑必須存在;純檔名視為行文提及,不檢查。"""
    errs = []
    bases = [card.path.parent, card.path.parent.parent, ROOT]
    for p in MEDIA.findall(card.text):
        if "/" not in p and "\\" not in p:
            continue
        cands = [Path(p)] if Path(p).is_absolute() else [b / p for b in bases]
        if not any(glob.glob(str(c)) if "*" in p else c.exists() for c in cands):
            errs.append(f"參考圖/試聽檔不存在:{p}")
    return errs


def lint(card):
    errs, warns = [], []
    if NEG_FLAG.search(card.text):
        errs.append("rate/pitch/volume 負值要用等號寫法,如 --rate=-24%(空格會被 argparse 當成另一個旗標)")
    errs += media_errors(card)
    if not DATED_LOG.search(card.text):
        warns.append("版本紀錄還沒有日期行(YYYY-MM-DD)")
    if card.kind == "角色卡":
        if not filled(card.appearance):
            warns.append("視覺層:外貌未填(沒有它就不能生圖)")
        for f in ("性格", "背景故事", "弧線"):
            if not card.get(f):
                warns.append(f"敘事層:{f}未填")
        if not (card.get("語氣人設") or card.get("voice")):
            warns.append("聲演層:語氣人設與 voice 都未填")
        if not any(SUB.match(s) for s in card.subs.get("關係網", [])):
            warns.append("關係網要寫成 dict:縮排子項「- 對象：描述」")
        arc = card.get("弧線")
        if arc and not ("從" in arc and "到" in arc):
            warns.append("弧線建議寫成「從…走到…」的完整句")
    return errs, warns


def collect(targets):
    for t in targets:
        t = Path(t)
        for p in sorted(t.rglob("*.md")) if t.is_dir() else [t]:
            if p.name.startswith("_") or p.name.lower() == "readme.md":
                continue
            card = Card(p)
            if card.kind and "<" not in card.title:   # 跳過空白範本
                yield card


def check_paths(targets):
    errs, warns = [], []
    for card in collect(targets):
        e, w = lint(card)
        errs += [f"{card.path}: 錯誤: {m}" for m in e]
        warns += [f"{card.path}: 提醒: {m}" for m in w]
    return errs, warns


def export_card(path):
    card = Card(path)
    if card.kind != "角色卡":
        raise ValueError(f"{path} 不是角色卡(標題要以「# 角色卡」開頭)")
    age = card.get("年齡")
    m = re.search(r"\d+", age)
    rel_lines = card.subs.get("關係網", [])
    out = {
        "name": card.path.stem,
        "age": int(m.group()) if m else age,
        "relations": {k.strip(): v.strip() for k, v in
                      (SUB.match(s).groups() for s in rel_lines if SUB.match(s))},
        "background": card.get("背景故事"),
        "personality": card.get("性格"),
        "appearance": clean(card.appearance) if filled(card.appearance) else "",
        "narrative_function": card.get("敘事功能"),
        "arc": card.get("弧線"),
    }
    if card.note and filled(card.note):
        out["appearance_note"] = card.note
    missing = [k for k in REQUIRED if out[k] in ("", {}, None)]
    if missing:
        raise ValueError(f"{path} 缺必填欄位:{'、'.join(missing)}")
    return out


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="story-bible 設定卡體檢/匯出")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="體檢設定卡")
    c.add_argument("paths", nargs="*", help="卡或資料夾,預設 library/")
    e = sub.add_parser("export", help="角色卡 → emotion-shot-pipeline characters json")
    e.add_argument("card")
    e.add_argument("-o", "--out", help="輸出檔;省略則印到螢幕")
    a = ap.parse_args(argv)

    if a.cmd == "check":
        targets = a.paths or [ROOT / "library"]
        missing = [t for t in targets if not Path(t).exists()]
        if missing:
            print(f"找不到:{', '.join(map(str, missing))}"
                  "(還沒建卡的話,先試 python scripts/bible.py check examples)", file=sys.stderr)
            return 2
        errs, warns = check_paths(targets)
        for line in errs + warns:
            print(line)
        n = sum(1 for _ in collect(targets))
        print(f"{n} 張卡,{len(errs)} 個錯誤,{len(warns)} 個提醒")
        return 1 if errs else 0

    try:
        data = export_card(a.card)
    except ValueError as err:
        print(err, file=sys.stderr)
        return 1
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"已寫出 {a.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
