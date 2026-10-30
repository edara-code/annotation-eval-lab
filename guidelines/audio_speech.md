# Audio Annotation Guidelines: Voice Assistant Speech (v2)

This project covers three tasks on the same audio:
1. **Speaker diarization**: who spoke when (conversation clips)
2. **Transcription**: what was said (all clips)
3. **Intent and wake word**: what the user wants (voice-command clips)

**Data:** `cmd_01`–`cmd_06` (single-speaker voice commands) and `conv_01`–`conv_03` (two-speaker conversations, 30 seconds each).

---

## Part 1: Speaker diarization (segmentation)

### Objective
Identify who spoke when in an audio recording containing two speakers, using precise time segmentation.

### Speaker labels
- **Speaker 1**: the **first person to speak** in the clip
- **Speaker 2**: the second voice heard

Numbering by order of first appearance keeps labels consistent between annotators and rounds.

### Annotation instructions
1. Listen to the entire audio before starting annotation.
2. Create a new segment every time the speaker changes.
3. Each segment must include a start time, an end time and the correct speaker label.
4. Ignore short pauses under 0.5 seconds if the same speaker continues speaking (keep it as one segment).
5. For pauses of 0.5 seconds or longer, end the segment and start a new one when speech resumes.
6. If speakers overlap, annotate separate overlapping segments for each speaker.
7. Keep speaker identity consistent throughout the full audio. The same voice always gets the same label.

### Segment boundaries
- **Start** the segment at the first audible sound of speech, not at the breath before it.
- **End** the segment at the last audible sound of the final word.
- Aim for about ±0.2 seconds of accuracy. Zoom in on the waveform for precision.

### Overlapping speech rule
When both speakers talk at the same time, create separate segments for each speaker with their own labels. The overlapping time appears in both segments.

### Short responses (backchannels)
Short replies like "mm-hmm", "yeah" or "right" while the other person is speaking **are** segments. Label them with the speaker who said them, even if they overlap.

### Do not label
- Silence, music, background noise, laughter without words, coughs.
- If you truly cannot tell who is speaking, label the segment with your best guess and add a note in the comment box.

---

## Part 2: Transcription

### General rule
Transcribe **exactly what is said** (verbatim), including mistakes and repetitions. Do not correct grammar.

### Conventions
| Situation | How to write it | Example |
|---|---|---|
| Casing | All lowercase, including names | `hey siri what's the weather in dublin` |
| Punctuation | None, except `?` for clear questions | `what's the weather this weekend?` |
| Fillers | Write them as spoken | `um`, `uh`, `hmm` |
| False starts / self-corrections | Keep both, mark the cut-off with `-` | `set a timer for ten- actually twelve minutes` |
| Numbers and times | Write as spoken words | `six thirty`, `twelve minutes` |
| Wake words | Write as spoken, lowercase | `hey siri set an alarm` |
| Unclear words | Use a tag | `[unintelligible]` |
| Overlapping speech you can't separate | Use a tag | `[crosstalk]` |
| Non-speech sounds | Only if they interrupt speech | `[laughter]`, `[noise]` |

In conversations, transcribe **each speaker segment separately** in its own text box.

**Why these rules:** speech-recognition accuracy (WER) is measured word by word. "6:30" vs. "six thirty", or "Set" vs. "set", would count as errors, so normalized transcripts keep comparisons fair.

---

## Part 3: Intent and wake word (voice commands only)

### Intent: choose ONE label that matches the main request
| Intent | Example |
|---|---|
| **Set Alarm** | "Set an alarm for six thirty" |
| **Set Timer** | "Set a timer for twelve minutes" |
| **Create Reminder** | "Remind me to call mom at five" |
| **Play Music** | "Play some relaxing jazz" |
| **Send Message** | "Text Priya I'm running late" |
| **Weather** | "What's the weather this weekend?" |
| **Navigation** | "Navigate to the nearest gas station" |
| **Other** | Anything that fits none of the above |

- If the user corrects themselves, label the **final** request.
- Alarm vs. timer: an alarm is set for a **clock time** ("at six thirty"); a timer is set for a **duration** ("for twelve minutes").

### Wake word
- **Wake word present:** Yes / No
- **Which:** Hey Siri / Alexa / None

---

## Change log
- **v2:** updated to two-speaker diarization; added explicit casing and punctuation rules for transcripts.

## Edge cases found during annotation
- (add notes here as you annotate)
