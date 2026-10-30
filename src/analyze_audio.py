"""Summarize audio annotations: voice commands (intent, wake word, transcript)
and conversations (speaker diarization + per-segment transcripts).

Usage:  python src/analyze_audio.py
"""
import json
import re
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CMD_FILE = Path("annotations/audio/commands/commands_round1.json")
CONV_FILE = Path("annotations/audio/conversations/conversations_round1.json")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

FILLERS = {"um", "uh", "hmm", "er", "ah"}
WAKE_PHRASES = {"Hey Siri": "hey siri", "Alexa": "alexa"}


def clip_name(task):
    """Label Studio prefixes uploads with a random id, e.g. 1a2b3c4d-cmd_01.wav"""
    name = Path(task["data"]["audio"]).name
    return re.sub(r"^[0-9a-f]{8}-", "", name)


def words(text):
    return re.findall(r"[a-z']+", text.lower())


# ---------------- Voice commands ----------------
cmd_rows, cmd_issues = [], []
for task in json.loads(CMD_FILE.read_text()):
    if not task.get("annotations"):
        continue
    res = task["annotations"][0]["result"]
    clip = clip_name(task)
    transcript, intent, wake = "", "MISSING", "MISSING"
    for r in res:
        if r["from_name"] == "transcript":
            transcript = " ".join(r["value"]["text"])
        elif r["from_name"] == "intent":
            intent = r["value"]["choices"][0]
        elif r["from_name"] == "wake_word":
            wake = r["value"]["choices"][0]
    w = words(transcript)
    cmd_rows.append({"clip": clip, "intent": intent, "wake_word": wake,
                     "words": len(w), "fillers": sum(x in FILLERS for x in w),
                     "transcript": transcript})

    # Automated logic checks against the guidelines
    if not transcript.strip():
        cmd_issues.append((clip, "missing transcript"))
    if re.search(r"[A-Z]", transcript):
        cmd_issues.append((clip, "uppercase letters (guideline: lowercase)"))
    if re.search(r"\d", transcript):
        cmd_issues.append((clip, "digits (guideline: numbers as words)"))
    if re.search(r"[.,!;:]", transcript):
        cmd_issues.append((clip, "punctuation other than ? (guideline)"))
    starts = transcript.lower().strip()
    for label, phrase in WAKE_PHRASES.items():
        if starts.startswith(phrase) and wake != label:
            cmd_issues.append((clip, f"transcript starts with '{phrase}' but wake word = {wake}"))
    if wake in WAKE_PHRASES and WAKE_PHRASES[wake] not in starts:
        cmd_issues.append((clip, f"wake word = {wake} but not found in transcript"))

cmd = pd.DataFrame(cmd_rows).sort_values("clip")
cmd.to_csv(REPORTS / "audio_commands.csv", index=False)

# ---------------- Conversations ----------------
seg_rows, conv_issues = [], []
for task in json.loads(CONV_FILE.read_text()):
    if not task.get("annotations"):
        continue
    res = task["annotations"][0]["result"]
    clip = clip_name(task)
    texts = {r["id"]: " ".join(r["value"].get("text", []))
             for r in res if r["type"] == "textarea"}
    for r in res:
        if r["type"] == "labels":
            v = r["value"]
            seg_rows.append({"clip": clip, "id": r["id"], "speaker": v["labels"][0],
                             "start": round(v["start"], 2), "end": round(v["end"], 2),
                             "duration": round(v["end"] - v["start"], 2),
                             "transcript": texts.get(r["id"], "")})

seg = pd.DataFrame(seg_rows).sort_values(["clip", "start"])

conv_summary = []
for clip, g in seg.groupby("clip"):
    g = g.sort_values("start")
    # overlap: total time where 2+ segments are active
    events = sorted([(s, 1) for s in g.start] + [(e, -1) for e in g.end])
    active, last, overlap = 0, None, 0.0
    for t, d in events:
        if active >= 2 and last is not None:
            overlap += t - last
        active += d
        last = t
    turns = (g.speaker != g.speaker.shift()).sum()
    conv_summary.append({"clip": clip, "segments": len(g), "speakers": g.speaker.nunique(),
                         "turns": int(turns), "speech_sec": round(g.duration.sum(), 1),
                         "overlap_sec": round(overlap, 1)})
    for _, s in g.iterrows():
        if not s.transcript.strip():
            conv_issues.append((clip, f"{s.speaker} segment {s.start}-{s.end}s has no transcript"))
        if s.duration < 0.3:
            conv_issues.append((clip, f"{s.speaker} segment {s.start}-{s.end}s is very short (<0.3s)"))
    first = g.iloc[0].speaker
    if first != "Speaker 1":
        conv_issues.append((clip, f"first segment is {first} (guideline: first speaker = Speaker 1)"))

conv = pd.DataFrame(conv_summary)
seg.drop(columns="id").to_csv(REPORTS / "audio_conversation_segments.csv", index=False)
speaker_time = seg.pivot_table(index="clip", columns="speaker", values="duration",
                               aggfunc="sum", fill_value=0).round(1)

# ---------------- Report ----------------
def issues_md(items):
    return "\n".join(f"- `{c}`: {m}" for c, m in items) if items else "- None found ✅"

summary = f"""# Audio annotation summary (round 1)

## Voice commands
- Clips: **{len(cmd)}** · with wake word: **{(cmd.wake_word.isin(WAKE_PHRASES)).sum()}** · fillers found: **{int(cmd.fillers.sum())}**

{cmd[['clip', 'intent', 'wake_word', 'words', 'fillers']].to_markdown(index=False)}

**Intent distribution:** {', '.join(f'{k} ({v})' for k, v in cmd.intent.value_counts().items())}

## Conversations (speaker diarization)
{conv.to_markdown(index=False)}

**Speaking time per speaker (seconds):**

{speaker_time.to_markdown()}

## Automated quality checks
**Voice commands**
{issues_md(cmd_issues)}

**Conversations**
{issues_md(conv_issues)}
"""
(REPORTS / "audio_round1_summary.md").write_text(summary)

ax = speaker_time.plot(kind="bar", figsize=(7, 4))
ax.set_title("Speaking time per speaker (round 1)")
ax.set_xlabel("")
ax.set_ylabel("Seconds")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(REPORTS / "audio_speaking_time.png", dpi=150)

print(summary)
print("Saved: reports/audio_round1_summary.md, audio_commands.csv, "
      "audio_conversation_segments.csv, audio_speaking_time.png")
