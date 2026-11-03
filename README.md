# Annotation Eval Lab

AI/ML data annotation and evaluation work: annotation guidelines, custom Label Studio interfaces, multimodal labeling, and Python-based quality checks and metrics.

## Project 1: Vehicle bounding-box annotation (image)

**Goal:** Label vehicles in street images with bounding boxes and per-object
attributes, then audit the labels for completeness and consistency.

| | |
|---|---|
| **Tool** | Label Studio (custom labeling interface with embedded instructions) |
| **Classes** | Car, Bus, Truck, Motorcycle |
| **Attributes (per box)** | Occlusion (Yes/No), Truncation (Yes/No), required |
| **Data** | 12 street images (see [DATASETS.md](DATASETS.md)) |
| **Guidelines** | [guidelines/image_bbox.md](guidelines/image_bbox.md) |
| **Labeling config** | [label_studio/vehicles_config.xml](label_studio/vehicles_config.xml) |

### Results
- **43 boxes** across **12 images** (3.6 vehicles per image)
- **100% attribute completeness**: every box has occlusion and truncation answered
- **Class imbalance:** cars are 70% of boxes, and buses appear once
- **Large vehicles are often truncated:** trucks (75%) and buses (100%) are frequently cut off by the image edge

![Boxes per class](reports/round1_boxes_per_class.png)

## Project 2: Voice assistant speech annotation (audio)

**Goal:** Annotate Siri/Alexa-style voice commands and two-speaker conversations
for intent, wake word, transcription and speaker diarization, with automated
quality checks against the guidelines.

| | |
|---|---|
| **Tool** | Label Studio (two projects: voice commands; speaker diarization) |
| **Tasks** | Intent classification (8 intents), wake word (Hey Siri / Alexa / None), verbatim transcription, speaker diarization with per-segment transcripts |
| **Data** | 6 voice commands recorded by the author + 3 two-speaker conversation clips |
| **Guidelines** | [guidelines/audio_speech.md](guidelines/audio_speech.md) |
| **Labeling config** | [label_studio/audio_conversations_config.xml](label_studio/audio_conversations_config.xml) |
| **Analysis** | [src/analyze_audio.py](src/analyze_audio.py) → [reports/audio_round1_summary.md](reports/audio_round1_summary.md) |

### Results
- **6 voice commands**, all with wake words (3 Hey Siri, 3 Alexa), covering 6 intents, with fillers ("um", "uh") transcribed per the guidelines
- **3 conversation clips** diarized into speaker segments with per-segment transcripts
- **All annotations pass automated quality checks** for transcription conventions, wake-word consistency and segment validity

![Speaking time per speaker](reports/audio_speaking_time.png)

### ASR evaluation (WER)
Machine transcripts from **Whisper (base.en)** were compared against the human transcripts (ground truth),
with identical normalization applied to both ([scoring rules](guidelines/audio_speech.md)).

- **Overall WER: 7.4%**, or **3.8% excluding fillers** (6 clips, 54 words)
- **All 6 intents preserved:** no ASR error changed the user's request
- **Wake word misrecognized:** "hey siri" transcribed as "hey cd". General ASR models struggle with product names, which is why assistants use dedicated wake-word models
- Whisper omits fillers ("uh") by design, so WER is reported both verbatim and excluding fillers
- Metric verified with known-answer unit tests ([tests/test_wer.py](tests/test_wer.py))

![ASR word error rate per clip](reports/audio_wer.png)

### Observations
- The conversation clips contain long, uninterrupted turns with no overlapping speech. Clips with more back-and-forth would test diarization more thoroughly.

## How to run

```bash
pip install -r requirements.txt
python src/analyze_annotations.py annotations/image/round1.json
python src/analyze_audio.py
python src/analyze_wer.py
```
