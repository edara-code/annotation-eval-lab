"""Summarize a Label Studio bounding-box export: counts, attributes, quality checks.

Usage:  python src/analyze_annotations.py annotations/image/round1.json
"""
import json
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # save charts to files without opening a window
import matplotlib.pyplot as plt

export_file = Path(sys.argv[1] if len(sys.argv) > 1 else "annotations/image/round1.json")
reports = Path("reports")
reports.mkdir(exist_ok=True)

# ---- 1. Read the Label Studio export into one row per box ----
tasks = json.loads(export_file.read_text())
rows = []
for task in tasks:
    image = Path(task["data"]["image"]).name
    if not task.get("annotations"):
        continue
    result = task["annotations"][0]["result"]  # first annotation of each image

    # Attributes (Occlusion/Truncation) are stored separately, linked by the box "id"
    attrs = {}
    for r in result:
        if r["type"] == "choices":
            attrs.setdefault(r["id"], {})[r["from_name"]] = r["value"]["choices"][0]

    for r in result:
        if r["type"] == "rectanglelabels":
            v = r["value"]
            rows.append({
                "image": image,
                "label": v["rectanglelabels"][0],
                "box_area_pct": round(v["width"] * v["height"] / 100, 2),  # % of image
                "occlusion": attrs.get(r["id"], {}).get("occlusion", "MISSING"),
                "truncation": attrs.get(r["id"], {}).get("truncation", "MISSING"),
            })

df = pd.DataFrame(rows)
df.to_csv(reports / "round1_boxes.csv", index=False)

# ---- 2. Summary numbers ----
n_images = len(tasks)
per_class = df["label"].value_counts()
occ = (df["occlusion"] == "Yes").groupby(df["label"]).mean().mul(100).round(1)
trunc = (df["truncation"] == "Yes").groupby(df["label"]).mean().mul(100).round(1)
missing = int(((df["occlusion"] == "MISSING") | (df["truncation"] == "MISSING")).sum())
tiny = int((df["box_area_pct"] < 0.05).sum())  # boxes under 0.05% of the image

table = pd.DataFrame({"boxes": per_class, "occluded_%": occ, "truncated_%": trunc}).fillna(0)

summary = f"""# Round 1 annotation summary

- Images annotated: **{n_images}**
- Total boxes: **{len(df)}**
- Average boxes per image: **{len(df) / n_images:.1f}**

## Per class
{table.to_markdown()}

## Quality checks
- Boxes missing an attribute: **{missing}**
- Very small boxes (< 0.05% of image, check against the 10x10 px rule): **{tiny}**
"""
(reports / "round1_summary.md").write_text(summary)

# ---- 3. Chart ----
ax = table[["boxes"]].plot(kind="bar", legend=False, color="#4D96FF", figsize=(6, 4))
ax.set_title("Boxes per class (round 1)")
ax.set_xlabel("")
ax.set_ylabel("Number of boxes")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(reports / "round1_boxes_per_class.png", dpi=150)

print(summary)
print("Saved: reports/round1_summary.md, reports/round1_boxes.csv, reports/round1_boxes_per_class.png")