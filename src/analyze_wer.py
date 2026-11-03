"""Compare human transcripts (ground truth) with Whisper ASR transcripts.

Reads:  annotations/audio/commands/commands_round1.json   (human, from Label Studio)
        annotations/audio/asr/cmd_XX.txt                   (machine, from Whisper)
Writes: reports/audio_wer_summary.md, reports/audio_wer.csv, reports/audio_wer.png

Usage:  python src/analyze_wer.py
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wer import FILLERS, normalize, wer_details, _ONES, _TENS  # noqa: E402

HUMAN = Path("annotations/audio/commands/commands_round1.json")
ASR_DIR = Path("annotations/audio/asr")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

WAKE_WORDS = {"hey", "siri", "alexa"}
FUNCTION_WORDS = {"a", "an", "the", "your", "my", "some", "to", "for", "at", "in", "on", "of",
                  "me", "it", "this", "that", "is", "be", "like"}
NUMBER_WORDS = set(_ONES) | set(t for t in _TENS if t) | {"hundred", "oh", "am", "pm"}
INTENT_KEYWORDS = {
    "Set Alarm": {"alarm", "wake"}, "Set Timer": {"timer"}, "Create Reminder": {"remind", "reminder"},
    "Play Music": {"play"}, "Send Message": {"text", "message", "send"},
    "Weather": {"weather", "forecast", "rain"}, "Navigation": {"navigate", "directions"},
}


def category(word):
    if word in FILLERS:
        return "filler"
    if word in WAKE_WORDS:
        return "wake word"
    if word in NUMBER_WORDS:
        return "number/time"
    if word in FUNCTION_WORDS:
        return "function word"
    return "content word"


def clip_name(task):
    return re.sub(r"^[0-9a-f]{8}-", "", Path(task["data"]["audio"]).name)


rows, error_rows = [], []
for task in json.loads(HUMAN.read_text()):
    if not task.get("annotations"):
        continue
    clip = Path(clip_name(task)).stem
    human, intent = "", ""
    for r in task["annotations"][0]["result"]:
        if r["from_name"] == "transcript":
            human = " ".join(r["value"]["text"])
        elif r["from_name"] == "intent":
            intent = r["value"]["choices"][0]
    asr_file = ASR_DIR / f"{clip}.txt"
    if not asr_file.exists():
        print(f"⚠️  missing machine transcript: {asr_file}")
        continue
    machine = asr_file.read_text().strip()

    full = wer_details(human, machine)
    nofill = wer_details(human, machine, ignore_fillers=True)
    cats = [category(ref or hyp) for _, ref, hyp in full["errors"]]
    critical = [e for e, c in zip(full["errors"], cats) if c in ("wake word", "number/time", "content word")]

    keywords = INTENT_KEYWORDS.get(intent, set())
    machine_words = set(normalize(machine).split())
    if keywords and not (keywords & machine_words):
        impact = "intent keyword lost (intent at risk)"
    elif critical:
        impact = "intent kept, details changed"
    else:
        impact = "no impact"

    rows.append({"clip": clip, "intent": intent, "human": normalize(human), "machine": normalize(machine),
                 "ref_words": full["ref_words"], "S": full["substitutions"], "D": full["deletions"],
                 "I": full["insertions"], "WER_%": round(100 * full["wer"], 1),
                 "WER_no_fillers_%": round(100 * nofill["wer"], 1), "impact": impact})
    for (etype, ref, hyp), c in zip(full["errors"], cats):
        error_rows.append({"clip": clip, "type": etype, "human_word": ref, "machine_word": hyp, "category": c})

df = pd.DataFrame(rows).sort_values("clip")
err = pd.DataFrame(error_rows, columns=["clip", "type", "human_word", "machine_word", "category"])
df.to_csv(REPORTS / "audio_wer.csv", index=False)

# corpus-level WER = all errors / all reference words (standard way to report overall WER)
total_words = df.ref_words.sum()
overall = 100 * (df.S + df.D + df.I).sum() / total_words
overall_nf = 100 * sum(wer_details(h, m, ignore_fillers=True)["wer"] * len(
    [w for w in h.split() if w not in FILLERS]) for h, m in zip(df.human, df.machine)) / max(
    1, sum(len([w for w in h.split() if w not in FILLERS]) for h in df.human))

summary = f"""# ASR evaluation: human vs. Whisper (base.en)

Human transcripts from Label Studio are the reference (ground truth). Both texts are normalized
with the same rules (lowercase, numbers as words, no punctuation) before comparison.

## Overall
- Clips: **{len(df)}** · reference words: **{total_words}**
- **Overall WER: {overall:.1f}%** · excluding fillers: **{overall_nf:.1f}%**
- Errors: **{int(df.S.sum())}** substitutions, **{int(df.D.sum())}** deletions, **{int(df.I.sum())}** insertions

## Per clip
{df[['clip', 'intent', 'ref_words', 'S', 'D', 'I', 'WER_%', 'WER_no_fillers_%', 'impact']].to_markdown(index=False)}

## Errors by category
{(err.category.value_counts().rename_axis('category').reset_index(name='errors').to_markdown(index=False)) if len(err) else 'No errors.'}

## All errors
{err.to_markdown(index=False) if len(err) else 'No errors.'}

## Side by side
{df[['clip', 'human', 'machine']].to_markdown(index=False)}
"""
(REPORTS / "audio_wer_summary.md").write_text(summary)

ax = df.set_index("clip")[["WER_%", "WER_no_fillers_%"]].plot(kind="bar", figsize=(7, 4))
ax.set_title("ASR word error rate per clip (Whisper base.en)")
ax.set_xlabel("")
ax.set_ylabel("WER (%)")
ax.legend(["WER", "WER excluding fillers"])
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(REPORTS / "audio_wer.png", dpi=150)

print(summary)
print("Saved: reports/audio_wer_summary.md, reports/audio_wer.csv, reports/audio_wer.png")
