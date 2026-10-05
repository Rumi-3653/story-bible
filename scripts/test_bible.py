"""python scripts/test_bible.py — 印 ok = 範例卡全綠、匯出欄位對、壞卡抓得到。"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bible  # noqa: E402

EX = bible.ROOT / "examples"

errs, warns = bible.check_paths([EX])
assert not errs, errs
assert len(list(bible.collect([EX]))) == 4

d = bible.export_card(EX / "還傘" / "characters" / "小滿.md")
assert set(bible.REQUIRED) <= set(d), d.keys()
assert d["name"] == "小滿" and d["age"] == 23
assert list(d["relations"]) == ["老伯"]
assert d["appearance"].startswith("23歲台灣女生") and "appearance_note" in d

with tempfile.TemporaryDirectory() as t:
    bad = Path(t) / "壞卡.md"
    bad.write_text(
        "# 角色卡：壞卡\n\n- **base**：`--rate -24%`\n\n"
        "| 路徑 | 用途 |\n|---|---|\n| `refs/不存在.png` | 主參考 |\n",
        encoding="utf-8")
    errs, warns = bible.check_paths([bad])
    assert len(errs) == 2, errs
    assert any("外貌未填" in w for w in warns), warns
    try:
        bible.export_card(bad)
        raise AssertionError("缺欄位的卡不該匯出成功")
    except ValueError as e:
        assert "appearance" in str(e)

print("ok")
