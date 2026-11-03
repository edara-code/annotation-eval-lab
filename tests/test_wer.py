"""Known-answer tests: each case has a WER we can work out by hand."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wer import normalize, wer, wer_details  # noqa: E402


def test_identical_is_zero():
    assert wer("set an alarm for six thirty", "set an alarm for six thirty") == 0.0


def test_one_deletion():  # 1 missed word out of 6 = 1/6
    d = wer_details("set an alarm for six thirty", "set alarm for six thirty")
    assert d["deletions"] == 1 and abs(d["wer"] - 1 / 6) < 1e-9


def test_one_substitution():  # remind -> rewind: 1 of 6 words
    d = wer_details("remind me to call mom tomorrow", "rewind me to call mom tomorrow")
    assert d["substitutions"] == 1 and abs(d["wer"] - 1 / 6) < 1e-9


def test_one_insertion():  # extra "the": 1 error / 3 reference words
    d = wer_details("play relaxing jazz", "play the relaxing jazz")
    assert d["insertions"] == 1 and abs(d["wer"] - 1 / 3) < 1e-9


def test_completely_different():
    assert wer("play jazz", "call mom") == 1.0


def test_normalization_makes_formatting_free():
    # casing, punctuation and digits must NOT count as errors
    assert wer("set an alarm for six thirty", "Set an alarm for 6:30.") == 0.0
    assert wer("remind me at five pm", "Remind me at 5 p.m.") == 0.0
    assert wer("set a timer for twelve minutes", "Set a timer for 12 minutes!") == 0.0


def test_normalize_examples():
    assert normalize("Hey Siri, set an alarm for 6:05 AM.") == "hey siri set an alarm for six oh five am"
    assert normalize("What's the weather?") == "whats the weather"


def test_dot_time_format():
    # Whisper sometimes writes times as 6.30
    assert wer("set an alarm for six thirty", "Set an alarm for 6.30.") == 0.0


def test_ignore_fillers():
    ref = "um set a timer for uh twelve minutes"
    hyp = "set a timer for twelve minutes"
    assert abs(wer(ref, hyp) - 2 / 8) < 1e-9          # 2 deleted fillers / 8 words
    assert wer(ref, hyp, ignore_fillers=True) == 0.0  # fillers excluded


def test_apostrophes_do_not_count():
    # guideline transcripts omit apostrophes; ASR keeps them - must not be an error
    assert wer("hey alexa whats the weather", "Hey Alexa, what's the weather?") == 0.0
