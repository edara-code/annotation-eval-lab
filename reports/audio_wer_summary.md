# ASR evaluation: human vs. Whisper (base.en)

Human transcripts from Label Studio are the reference (ground truth). Both texts are normalized
with the same rules (lowercase, numbers as words, no punctuation) before comparison.

## Overall
- Clips: **6** · reference words: **54**
- **Overall WER: 7.4%** · excluding fillers: **3.8%**
- Errors: **2** substitutions, **2** deletions, **0** insertions

## Per clip
| clip   | intent          |   ref_words |   S |   D |   I |   WER_% |   WER_no_fillers_% | impact                       |
|:-------|:----------------|------------:|----:|----:|----:|--------:|-------------------:|:-----------------------------|
| cmd_01 | Set Alarm       |          10 |   1 |   0 |   0 |      10 |               10   | intent kept, details changed |
| cmd_02 | Create Reminder |          10 |   0 |   0 |   0 |       0 |                0   | no impact                    |
| cmd_03 | Play Music      |           6 |   0 |   0 |   0 |       0 |                0   | no impact                    |
| cmd_04 | Weather         |          10 |   0 |   0 |   0 |       0 |                0   | no impact                    |
| cmd_05 | Navigation      |           8 |   0 |   0 |   0 |       0 |                0   | no impact                    |
| cmd_06 | Set Timer       |          10 |   1 |   2 |   0 |      30 |               12.5 | no impact                    |

## Errors by category
| category      |   errors |
|:--------------|---------:|
| filler        |        2 |
| wake word     |        1 |
| function word |        1 |

## All errors
| clip   | type         | human_word   | machine_word   | category      |
|:-------|:-------------|:-------------|:---------------|:--------------|
| cmd_01 | substitution | siri         | cd             | wake word     |
| cmd_06 | substitution | a            | your           | function word |
| cmd_06 | deletion     | uh           |                | filler        |
| cmd_06 | deletion     | uh           |                | filler        |

## Side by side
| clip   | human                                                   | machine                                                 |
|:-------|:--------------------------------------------------------|:--------------------------------------------------------|
| cmd_01 | hey siri set an alarm for six thirty tomorrow morning   | hey cd set an alarm for six thirty tomorrow morning     |
| cmd_02 | hey alexa remind me to call mom at five pm              | hey alexa remind me to call mom at five pm              |
| cmd_03 | hey siri play some relaxing music                       | hey siri play some relaxing music                       |
| cmd_04 | hey alexa whats the weather like in dublin this weekend | hey alexa whats the weather like in dublin this weekend |
| cmd_05 | hey alexa navigate to the nearest gas station           | hey alexa navigate to the nearest gas station           |
| cmd_06 | hey siri set a timer for uh uh fifteen minutes          | hey siri set your timer for fifteen minutes             |
