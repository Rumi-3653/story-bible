# story-bible — 角色 × 場景 × 世界觀設定聖經

> 給 AI 影像／短片／配音創作者的「設定卡正本」：一個角色一張三層卡，生圖、編劇、配音各取所需，改了就回存，下次召回不跑設定。
>
> English summary below. ↓

連載 IP 的角色設定通常散在四處：生圖的視覺錨在素材庫、劇本的角色 json 在專案資料夾、聲線參數寫死在配音腳本、語氣人設在節目企劃書——**互不相通，全靠人腦記**。換一集、換一個平台，臉就跑了、聲音就變了、性格就 OOC 了。

story-bible 的做法：每個角色、場景、世界觀各一張 Markdown 卡，當作**唯一正本**；下游工具只拿它需要的那一層。

| 卡 | 內容 | 給誰用 |
|---|---|---|
| **角色卡·視覺層** | 外貌（只寫恆定可視特徵）、角色鎖逐字句、English 鏡像、鎖臉參考圖、最佳平台 | 生圖、分鏡、img2video |
| **角色卡·敘事層** | 性格（行為模式）、背景故事、關係網（dict）、敘事功能、弧線、主導/底噪情緒 | 編劇、審稿抓 OOC |
| **角色卡·聲演層** | 語氣人設、語癖、對白樣本、engine/voice/rate/pitch、唸法校正表、混音預設 | 配音、TTS |
| **場景卡** | 核心元素、光線色票、聲音環境、情緒功能、守恆閥（開了幾個謎、關了幾個） | 生圖、混音、分鏡 |
| **世界觀卡** | 造世第一因、稀缺與代價、禁令、冰山留白、核心命題、經典錨、美術基調、🔒封存區 | 編劇、系列規格 |

## 快速開始

**當 Claude Code skill 用**（也適用其他讀 `SKILL.md` 的 agent）：

```bash
git clone https://github.com/Rumi-3653/story-bible ~/.claude/skills/story-bible
```

然後直接說「幫我建一個角色」「新 IP 開檔」「@小滿 的設定」「把這個角色存起來」。agent 會讀 `references/欄位指南.md`、照模板訪談式建卡、存進 `library/<IP名>/`。

**不用 AI 也行**：把 `templates/` 的空白卡複製進 `library/<IP名>/` 手填即可，填法參考 `examples/還傘/`。

## 工具：體檢與匯出（Python 3.8+，只用標準庫）

```bash
python scripts/bible.py check                 # 體檢 library/ 下所有卡
python scripts/bible.py check examples        # 也可以指定資料夾或單張卡
python scripts/bible.py export examples/還傘/characters/小滿.md -o out/小滿.json
python scripts/test_bible.py                  # 自我測試,印 ok 即通過
```

- **check** 的「錯誤」會讓 exit code 變 1：rate/pitch 負值沒用等號寫法（`--rate -24%` 會被 argparse 誤判，要寫 `--rate=-24%`）、參考圖或試聽檔路徑不存在。「提醒」是軟性的：某層未填、關係網不是 dict、弧線沒寫成「從…走到…」、版本紀錄沒日期。
- **export** 把角色卡轉成 [emotion-shot-pipeline](https://github.com/Rumi-3653/emotion-shot-pipeline) 的 `characters/<名>.json`（8 必填欄＋appearance_note），缺欄就報錯不寫檔。範例卡匯出的 8 個必填欄與該 repo 的 `demo_還傘` json 逐字相同。

## 資料夾

```
story-bible/
├── SKILL.md              agent 讀的工作流與鐵則
├── templates/            角色卡、場景卡、世界觀卡空白模板
├── references/欄位指南.md 每個欄位誰吃它、怎麼填、怎麼匯出到下游
├── scripts/              bible.py(check / export)＋自我測試
├── examples/             範例 IP《還傘》:兩張角色卡＋場景卡＋世界觀卡＋索引
└── library/              你的設定卡(.gitignore 預設排除,不會被推上來)
```

**私人卡怎麼版控**：`library/` 常放未發表的 IP、劇透和私人角色，所以預設不進 repo。作者的做法是在 `library/` 裡另外 `git init` 一個**私有 repo**，框架更新推公開 repo、改卡推私有 repo，路徑完全不用動。不在意的話，刪掉 `.gitignore` 的 `/library/` 那行就能一起版控。

## 範例：《還傘》

凌晨兩點的便利商店，大夜班店員小滿把用了三年的傘借給被大雨困住的老伯；傘遲遲沒回來，直到又一個雨夜，傘柄綁著兩顆橘子和一張紙條回到檯面上。

這部 8 鏡 60 秒的短片就是 emotion-shot-pipeline 的 `demo_還傘`。`examples/還傘/` 示範了：寫實題材的世界觀卡怎麼寫（「規則」是城市預設的人際冷漠）、冰山留白（紙條內容全片不入鏡）、appearance 與 props 狀態分家、唸法校正表（「還傘」的「還」TTS 常誤唸成 hái）。視覺鎖句與聲線參數是**示範值，未經平台實測**。

## 鐵則（摘要，完整版見 SKILL.md）

1. **角色鎖逐字不可改**——實測鎖出來的句子，引用時一字不差。
2. **appearance 只寫恆定可視特徵**——逐鏡會變的道具狀態寫進 props，不然會汙染生圖 prompt。
3. **聲線鎖**——同角色全程同 engine＋voice＋rate/pitch。
4. **語音克隆只限本人或合法授權的聲音**，不可克隆他人。
5. **劇透封存**——卡只寫已揭露的層，結局錨只放路徑。
6. **正本唯一**——下游改了沒回存，下次召回就是舊資料。這是整套系統唯一會壞掉的方式。

## 下游串接

| 下游 | 狀態 |
|---|---|
| [emotion-shot-pipeline](https://github.com/Rumi-3653/emotion-shot-pipeline)（劇本→逐鏡 prompt＋配樂） | 公開；`bible.py export` 直接產 characters json |
| nine-grid-storyboard、ai-voiceover、ai-media-generator 的 asset-library | 作者自用或第三方工具，不在本 repo；`references/欄位指南.md` §四 有欄位對照，換成你自己的工具即可 |

## 授權

[MIT](LICENSE)

---

## English summary

**story-bible** is a Markdown-based "series bible" for AI image / video / voice creators, packaged as a Claude Code skill (works with any agent that reads `SKILL.md`). Each character gets one canonical card with three layers — **visual** (constant appearance traits, verbatim prompt-lock sentences, face-reference images, best platform), **narrative** (behavioral personality, backstory, relations as a dict, arc, dominant/undertone emotion) and **voice** (persona, verbal tics, sample lines, TTS engine/voice/rate/pitch, pronunciation fixes). Scene cards and world cards cover lighting, palette, soundscape, rules of the world, scarcity and cost, taboos, and sealed spoilers.

Downstream tools pull only the layer they need, and any change made downstream gets written back to the card — so a character's face, voice and personality stay consistent across episodes and platforms.

- **Install**: `git clone https://github.com/Rumi-3653/story-bible ~/.claude/skills/story-bible`, then ask your agent to "create a character" / "open a new IP".
- **Tools** (Python 3.8+, stdlib only): `python scripts/bible.py check` lints cards (errors: missing reference files, negative `--rate`/`--pitch` written without `=`; warnings: empty layers, non-dict relations, arc not phrased as "from… to…"); `python scripts/bible.py export <card.md>` emits a [emotion-shot-pipeline](https://github.com/Rumi-3653/emotion-shot-pipeline) character JSON.
- **Example**: `examples/還傘/` (*Returning the Umbrella*) — a fully filled 60-second short: two character cards, one scene card, one world card.
- **Your cards** live in `library/`, which is git-ignored by default; the author keeps it as a separate private repo nested inside.
- Card field names are in Traditional Chinese; `references/欄位指南.md` explains every field.
- License: MIT.
