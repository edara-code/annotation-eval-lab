# Annotation Eval Lab

**How do you know an AI system is right?** This lab works through that question end to end: write clear guidelines, collect human labels, measure their quality, and check whether automated graders and machine outputs agree with human judgment.

It covers three kinds of AI evaluation work, each with its own guidelines, custom Label Studio interface, Python analysis, and unit-tested metrics.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Label Studio](https://img.shields.io/badge/Label_Studio-FF7557?style=flat-square)
![Tests](https://img.shields.io/badge/metric_tests-16_passing-2ea44f?style=flat-square)

---

## Results at a glance

| Project | What was evaluated | Headline result |
|---|---|---|
| [1. Image annotation](#project-1-vehicle-bounding-box-annotation-image) | 43 vehicle boxes across 12 street images | **100% attribute completeness**; strong class imbalance (cars = 70% of boxes) |
| [2. Speech & ASR](#project-2-voice-assistant-speech-annotation-audio) | Voice commands, diarization, Whisper vs. human transcripts | **WER 7.4%** (3.8% excluding fillers); **all 6 intents preserved** |
| [3. LLM evaluation](#project-3-llm-response-evaluation-human-vs-autograder) | 40 responses from Gemini and ChatGPT, rated by a human and a Claude autograder | **95% agreement on safety but kappa = 0.00**: high agreement hid an autograder that never flagged unsafe answers |

**The main lesson:** a metric is only useful if you can trust it. Raw agreement, averages, and small samples can all look good while hiding real problems. Each project here reports the measure that exposes those problems, not just the one that looks best.

---

## Evaluation approach

Every project follows the same loop:

1. **Define quality:** written guidelines and rubrics with edge cases ([guidelines/](guidelines/))
2. **Collect labels:** custom Label Studio interfaces with instructions built in ([label_studio/](label_studio/))
3. **Check the labels:** automated quality checks for completeness and consistency
4. **Measure:** metrics with known-answer unit tests ([tests/](tests/)), so the numbers themselves are verified
5. **Report findings:** what the numbers mean, where they mislead, and what to do next ([reports/](reports/))

---

## Project 1: Vehicle bounding-box annotation (image)

**Goal:** Label vehicles in street images with bounding boxes and per-object attributes, then audit the labels for completeness and consistency.

| | |
|---|---|
| **Classes** | Car, Bus, Truck, Motorcycle |
| **Attributes (per box)** | Occlusion (Yes/No), Truncation (Yes/No), both required |
| **Data** | 12 street images ([DATASETS.md](DATASETS.md)) |
| **Guidelines** | [guidelines/image_bbox.md](guidelines/image_bbox.md) |
| **Labeling interface** | [label_studio/vehicles_config.xml](label_studio/vehicles_config.xml) |
| **Analysis** | [src/analyze_annotations.py](src/analyze_annotations.py) → [reports/round1_summary.md](reports/round1_summary.md) |

### Results
- **43 boxes** across **12 images** (3.6 vehicles per image)
- **100% attribute completeness:** every box has occlusion and truncation answered
- **Class imbalance:** cars are 70% of boxes, and a bus appears only once, too few to train or evaluate that class
- **Large vehicles are often cut off:** 75% of trucks and 100% of buses are truncated by the image edge
- **1 very small box** flagged for review against the minimum-size rule

![Boxes per class](reports/round1_boxes_per_class.png)

---

## Project 2: Voice assistant speech annotation (audio)

**Goal:** Annotate Siri/Alexa-style voice commands and two-speaker conversations for intent, wake word, transcription, and speaker diarization, then evaluate a speech recognition (ASR) model against the human transcripts.

| | |
|---|---|
| **Tasks** | Intent classification (8 intents), wake word (Hey Siri / Alexa / None), verbatim transcription, speaker diarization with per-segment transcripts |
| **Data** | 6 voice commands recorded by the author, plus 3 two-speaker conversation clips |
| **Guidelines** | [guidelines/audio_speech.md](guidelines/audio_speech.md) |
| **Analysis** | [src/analyze_audio.py](src/analyze_audio.py) → [reports/audio_round1_summary.md](reports/audio_round1_summary.md) |

### Annotation results
- **6 voice commands**, all with wake words (3 Hey Siri, 3 Alexa), covering 6 intents, with fillers ("um", "uh") transcribed as the guidelines require
- **3 conversation clips** split into speaker segments with per-segment transcripts
- **All annotations pass automated quality checks** for transcription conventions, wake-word consistency, and segment validity

![Speaking time per speaker](reports/audio_speaking_time.png)

### ASR evaluation: Whisper vs. human transcripts (WER)
Machine transcripts from **Whisper (base.en)** were compared with the human transcripts as ground truth, using the same normalization for both ([scoring rules](guidelines/audio_speech.md)).

| Metric | Result |
|---|---|
| **Word error rate (WER)** | **7.4%** (6 clips, 54 words) |
| **WER excluding fillers** | **3.8%** |
| **Errors** | 2 substitutions, 2 deletions, 0 insertions |
| **Intents preserved** | **6 of 6**: no error changed what the user asked for |

**Findings**
- **The wake word was misheard:** "hey siri" became "hey cd". General-purpose ASR struggles with product names, which is why assistants use dedicated wake-word models.
- **Fillers inflate WER:** Whisper drops "uh" by design, so WER is reported both verbatim and without fillers. Which number matters depends on whether the product needs verbatim transcripts.
- **WER alone is not the whole story:** each error is also scored for its impact on the user's intent.
- The metric is verified with known-answer unit tests ([tests/test_wer.py](tests/test_wer.py)).

![ASR word error rate per clip](reports/audio_wer.png)

---

## Project 3: LLM response evaluation (human vs. autograder)

**Goal:** Rate AI-assistant responses with a written rubric, then measure how well an LLM autograder agrees with human judgment, to decide where the autograder can be trusted.

| | |
|---|---|
| **Evaluation set** | 20 prompts: helpful tasks, factual questions, instruction following, safety (should answer / should decline), and ambiguous requests ([prompts](data/llm_eval/prompts.csv)) |
| **Systems compared** | Gemini vs. ChatGPT, rated blind in a randomized, balanced order |
| **Rubric** | Helpfulness (1-5), accuracy (1-5), instruction following, safety (safe / over-refusal / unsafe), side-by-side preference ([guidelines/llm_rubric.md](guidelines/llm_rubric.md)) |
| **Human ratings** | 40 responses rated in Label Studio ([interface](label_studio/llm_eval_config.xml)) |
| **Autograder** | Claude, using the same rubric on the same blinded tasks ([judge prompt](data/llm_eval/judge_prompt.txt)) |
| **Analysis** | [src/analyze_llm_eval.py](src/analyze_llm_eval.py) → [reports/llm_eval_summary.md](reports/llm_eval_summary.md) |

### Human vs. autograder agreement

| Criterion | Exact agreement | Kappa | Strength |
|---|---|---|---|
| Helpfulness | 62.5% (90% within 1 point) | 0.42 (weighted) | Moderate |
| Accuracy | 72.5% (90% within 1 point) | 0.17 (weighted) | Slight |
| Instruction following | 80% | 0.16 | Slight |
| Safety | **95%** | **0.00** | Poor |
| Preference | 45% | 0.23 | Fair |

![Human vs. autograder agreement](reports/llm_eval_agreement.png)

### Findings
- **High agreement can hide low reliability (the kappa paradox):** safety agreement was 95%, but Cohen's kappa was 0.00. The autograder labeled every response safe and missed both cases the human flagged. Raw agreement looked excellent only because unsafe answers were rare.
- **The autograder was more lenient** than the human rater (+0.22 helpfulness and +0.32 accuracy on average), and it chose "tie" in 10 of 20 comparisons versus 2 for the human.
- **The assistants were closely matched:** Gemini fully followed instructions more often (85% vs. 70%), while ChatGPT was preferred on safety-related prompts for more careful guidance and for offering alternatives when declining.
- **Both assistants correctly declined** the privacy and deception requests. No position bias appeared in the human side-by-side choices (10 vs. 8).
- **Recommendation:** at this level of agreement, the autograder suits a first pass on clear-cut criteria, while safety and nuanced judgments still need human review.
- Agreement metrics are verified with known-answer unit tests ([tests/test_agreement.py](tests/test_agreement.py)).

---

## Limitations

These are deliberately small, hands-on datasets built to practice the full workflow, so the results show methods rather than benchmark-scale conclusions.

- **Small samples:** 12 images, 6 voice commands, and 20 prompts. Kappa in particular is unstable on rare categories, which is part of why the safety result matters.
- **One human rater:** human-vs-autograder agreement uses a single annotator. Adding a second would allow human-vs-human agreement as a baseline.
- **Simple conversations:** the diarization clips have long turns and no overlapping speech, so they don't test diarization hard.

---

## Repository structure

```
guidelines/     Annotation guidelines and rubrics
label_studio/   Custom Label Studio labeling interfaces (XML)
data/           Prompts, model responses, and raw audio
annotations/    Human and autograder labels exported from Label Studio
src/            Analysis scripts and metric implementations (WER, kappa)
tests/          Known-answer unit tests for the metrics
reports/        Generated summaries, CSVs, and charts
scripts/        Pre-push check: tests + analyses + quality checks
```

## How to run

```bash
pip install pandas matplotlib tabulate pytest

# Verify the metrics
python -m pytest -q tests/

# Rebuild every report and chart
python src/analyze_annotations.py annotations/image/round1.json
python src/analyze_audio.py
python src/analyze_wer.py
python src/analyze_llm_eval.py

# Or run everything at once before pushing
bash scripts/check_before_push.sh
```

Label Studio is only needed to open or edit the annotations, and Whisper only to regenerate the machine transcripts. Both outputs are already saved in `annotations/`.
