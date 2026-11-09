"""LLM evaluation analysis: human ratings vs. LLM autograder, plus assistant comparison.

Reads:  annotations/llm_eval/human_ratings.json        (Label Studio export, blinded Response 1/2)
        annotations/llm_eval/autograder_ratings.jsonl  (LLM judge, same blinded tasks)
        data/llm_eval/ls_tasks.json                    (which assistant was Response 1 / 2)
Writes: reports/llm_eval_summary.md, reports/llm_eval_ratings.csv, reports/llm_eval_agreement.png

Usage:  python src/analyze_llm_eval.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agreement import cohen_kappa, interpret, percent_agreement, weighted_kappa, within_one  # noqa: E402

MODEL_NAMES = {"A": "Gemini", "B": "ChatGPT"}   # who produced responses_A / responses_B
JUDGE_NAME = "Claude"
HUMAN = Path("annotations/llm_eval/human_ratings.json")
JUDGE = Path("annotations/llm_eval/autograder_ratings.jsonl")
TASKS = Path("data/llm_eval/ls_tasks.json")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)
CRITERIA = ["helpfulness", "accuracy", "instruction", "safety"]

# ---- task metadata: which assistant was shown as Response 1 / 2 ----
meta = {t["data"]["id"]: t["data"] for t in json.load(open(TASKS))}

# ---- human ratings from the Label Studio export ----
human = {}
for t in json.load(open(HUMAN)):
    if not t.get("annotations"):
        continue
    row = {}
    for r in t["annotations"][0]["result"]:
        v = r["value"]
        if r["type"] == "rating":
            row[r["from_name"]] = v["rating"]
        elif r["type"] == "choices":
            row[r["from_name"]] = v["choices"][0]
        elif r["type"] == "textarea":
            row[r["from_name"]] = " ".join(v["text"])
    human[t["data"]["id"]] = row

# ---- autograder ratings ----
judge = {r["id"]: r for r in (json.loads(l) for l in open(JUDGE) if l.strip().startswith("{"))}


def pref_to_model(pref, m):
    """Turn 'Response 1 better' into the assistant letter (A/B) using the blinded order."""
    if pref == "Tie":
        return "Tie"
    return m["model_1"] if pref.startswith("Response 1") else m["model_2"]


# ---- one row per (prompt, assistant) with human + judge scores ----
rows = []
for pid, m in sorted(meta.items()):
    h, j = human[pid], judge[pid]
    for slot in ("r1", "r2"):
        model = m["model_1"] if slot == "r1" else m["model_2"]
        row = {"id": pid, "category": m["category"], "expected": m["expected"],
               "assistant": MODEL_NAMES[model], "position": slot}
        for c in CRITERIA:
            row[f"human_{c}"] = h[f"{slot}_{c}"]
            row[f"judge_{c}"] = j[f"{slot}_{c}"]
        rows.append(row)
df = pd.DataFrame(rows)
df.to_csv(REPORTS / "llm_eval_ratings.csv", index=False)

pref = pd.DataFrame([{"id": pid, "human": human[pid]["preference"], "judge": judge[pid]["preference"],
                      "human_winner": pref_to_model(human[pid]["preference"], m),
                      "judge_winner": pref_to_model(judge[pid]["preference"], m),
                      "human_reason": human[pid].get("reason", ""), "judge_reason": judge[pid].get("reason", "")}
                     for pid, m in sorted(meta.items())])

# ---- 1. human vs autograder agreement ----
agree_rows = []
for c in CRITERIA:
    a, b = list(df[f"human_{c}"]), list(df[f"judge_{c}"])
    ordinal = c in ("helpfulness", "accuracy")
    k = weighted_kappa(a, b) if ordinal else cohen_kappa(a, b)
    agree_rows.append({"criterion": c, "items": len(a), "exact_agreement_%": round(100 * percent_agreement(a, b), 1),
                       "within_1_point_%": round(100 * within_one(a, b), 1) if ordinal else "-",
                       "kappa": "n/a" if k is None else round(k, 2),
                       "kappa_type": "quadratic weighted" if ordinal else "Cohen's", "strength": interpret(k)})
hw, jw = list(pref.human_winner), list(pref.judge_winner)
kp = cohen_kappa(hw, jw)
agree_rows.append({"criterion": "preference (A/B/tie)", "items": len(hw),
                   "exact_agreement_%": round(100 * percent_agreement(hw, jw), 1), "within_1_point_%": "-",
                   "kappa": "n/a" if kp is None else round(kp, 2), "kappa_type": "Cohen's", "strength": interpret(kp)})
agree = pd.DataFrame(agree_rows)

# biggest score disagreements (1-5 scales)
dis = []
for c in ("helpfulness", "accuracy"):
    d = df[df[f"human_{c}"] != df[f"judge_{c}"]].copy()
    d["criterion"] = c
    d["human"], d["judge"] = d[f"human_{c}"], d[f"judge_{c}"]
    d["gap"] = (d["human"] - d["judge"]).abs()
    dis.append(d[["id", "assistant", "criterion", "human", "judge", "gap"]])
for c in ("instruction", "safety"):
    d = df[df[f"human_{c}"] != df[f"judge_{c}"]].copy()
    d["criterion"], d["human"], d["judge"], d["gap"] = c, d[f"human_{c}"], d[f"judge_{c}"], "-"
    dis.append(d[["id", "assistant", "criterion", "human", "judge", "gap"]])
disagreements = pd.concat(dis)

# judge leniency: average score difference (positive = judge scores higher than the human)
leniency = {c: round((df[f"judge_{c}"] - df[f"human_{c}"]).mean(), 2) for c in ("helpfulness", "accuracy")}

# ---- 2. assistant comparison (human ratings = ground truth) ----
comp = df.groupby("assistant").agg(
    helpfulness_avg=("human_helpfulness", "mean"), accuracy_avg=("human_accuracy", "mean"),
    instructions_fully_pct=("human_instruction", lambda s: 100 * (s == "Fully").mean())).round(2)
wins = pref.human_winner.map(lambda w: MODEL_NAMES.get(w, "Tie")).value_counts()
comp["preferred_by_human"] = [int(wins.get(n, 0)) for n in comp.index]
comp["ties"] = int(wins.get("Tie", 0))

# ---- 3. safety: over-refusal and under-refusal (human labels) ----
answer = df[df.expected == "answer"]
decline = df[df.expected == "decline"]
safety_rows = []
for name in MODEL_NAMES.values():
    a, d = answer[answer.assistant == name], decline[decline.assistant == name]
    safety_rows.append({"assistant": name,
                        "over_refusals": f"{int((a.human_safety == 'Over-refusal').sum())} of {len(a)}",
                        "unsafe_responses": f"{int((d.human_safety == 'Unsafe').sum())} of {len(d)}",
                        "declined_correctly": f"{int((d.human_safety == 'Safe').sum())} of {len(d)}"})
safety = pd.DataFrame(safety_rows)

# ---- 4. position check: does a rater favor whichever response is shown first? ----
pos = pd.DataFrame([{"rater": n, "chose_response_1": int((pref[col] == "Response 1 better").sum()),
                     "chose_response_2": int((pref[col] == "Response 2 better").sum()),
                     "tie": int((pref[col] == "Tie").sum())} for n, col in (("Human", "human"), (JUDGE_NAME, "judge"))])

# ---- report ----
summary = f"""# LLM evaluation: human vs. autograder

- **Prompts:** {len(meta)} (helpful tasks, factual, instruction following, safety, ambiguous) · **responses rated:** {len(df)}
- **Assistants compared:** {MODEL_NAMES['A']} vs. {MODEL_NAMES['B']} (blinded, order randomized and balanced)
- **Autograder:** {JUDGE_NAME}, using the same rubric ([guidelines/llm_rubric.md](../guidelines/llm_rubric.md))

## 1. Human vs. autograder agreement
{agree.to_markdown(index=False)}

**Autograder leniency** (average judge score minus human score; positive = judge more generous):
helpfulness {leniency['helpfulness']:+}, accuracy {leniency['accuracy']:+}

### Disagreements
{disagreements.to_markdown(index=False) if len(disagreements) else 'None.'}

## 2. Assistant comparison (human ratings)
{comp.to_markdown()}

## 3. Safety: over-refusal and under-refusal (human ratings)
{safety.to_markdown(index=False)}

## 4. Position check (side-by-side choices)
{pos.to_markdown(index=False)}

## Preference details
{pref[['id', 'human_winner', 'judge_winner', 'human_reason', 'judge_reason']].replace(MODEL_NAMES).to_markdown(index=False)}
"""
(REPORTS / "llm_eval_summary.md").write_text(summary)

chart = agree[agree.kappa != "n/a"].copy()
chart["kappa"] = chart["kappa"].astype(float)
ax = chart.plot(x="criterion", y="kappa", kind="bar", legend=False, color="#4D96FF", figsize=(7, 4))
ax.axhline(0.6, color="gray", linestyle="--", linewidth=1)
ax.set_title(f"Human vs. {JUDGE_NAME} autograder agreement (kappa)")
ax.set_xlabel("")
ax.set_ylabel("Kappa")
ax.set_ylim(min(0, chart["kappa"].min() - 0.1), 1)
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(REPORTS / "llm_eval_agreement.png", dpi=150)

print(summary)
print("Saved: reports/llm_eval_summary.md, reports/llm_eval_ratings.csv, reports/llm_eval_agreement.png")
