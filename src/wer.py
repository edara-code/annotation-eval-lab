"""Word error rate (WER) with text normalization and error breakdown.

WER = (substitutions + deletions + insertions) / words in the reference
The reference is the human transcript (ground truth); the hypothesis is the machine transcript.
"""
import re

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
         "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def number_to_words(n: int) -> str:
    """Spell out 0-999 (enough for times, durations and counts in voice commands)."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + ("" if ones == 0 else " " + _ONES[ones])
    hundreds, rest = divmod(n, 100)
    return _ONES[hundreds] + " hundred" + ("" if rest == 0 else " " + number_to_words(rest))


def _time_to_words(match: re.Match) -> str:
    hour, minute = int(match.group(1)), int(match.group(2))
    if minute == 0:
        return number_to_words(hour)
    if minute < 10:
        return f"{number_to_words(hour)} oh {number_to_words(minute)}"
    return f"{number_to_words(hour)} {number_to_words(minute)}"


def normalize(text: str) -> str:
    """Apply the guideline conventions so human and machine text compare fairly:
    lowercase, times and numbers as words, a.m./p.m. -> am/pm, no punctuation."""
    text = text.lower().replace("'", "").replace("\u2019", "")
    text = re.sub(r"\b([ap])\.\s?m\.?", r"\1m", text)          # p.m. -> pm
    text = re.sub(r"\b(\d{1,2})[:.](\d{2})\b", _time_to_words, text)  # 6:30 / 6.30 -> six thirty
    text = re.sub(r"\b\d{1,3}\b", lambda m: number_to_words(int(m.group())), text)
    text = re.sub(r"[^a-z ]", " ", text)                          # drop punctuation
    return " ".join(text.split())


FILLERS = {"um", "uh", "hmm", "er", "ah"}


def remove_fillers(text: str) -> str:
    """Drop filler words (many ASR systems omit them by design)."""
    return " ".join(w for w in normalize(text).split() if w not in FILLERS)


def wer_details(reference: str, hypothesis: str, ignore_fillers: bool = False) -> dict:
    """Return WER plus counts of substitutions, deletions, insertions and the aligned errors."""
    if ignore_fillers:
        reference, hypothesis = remove_fillers(reference), remove_fillers(hypothesis)
    ref, hyp = normalize(reference).split(), normalize(hypothesis).split()
    n, m = len(ref), len(hyp)
    # dynamic-programming edit distance table
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    # walk back through the table to classify each error
    i, j, subs, dels, ins, errors = n, m, 0, 0, 0, []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
            if ref[i - 1] != hyp[j - 1]:
                subs += 1
                errors.append(("substitution", ref[i - 1], hyp[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            dels += 1
            errors.append(("deletion", ref[i - 1], ""))
            i -= 1
        else:
            ins += 1
            errors.append(("insertion", "", hyp[j - 1]))
            j -= 1
    errors.reverse()
    wer = (subs + dels + ins) / n if n else (0.0 if m == 0 else 1.0)
    return {"wer": wer, "substitutions": subs, "deletions": dels, "insertions": ins,
            "ref_words": n, "errors": errors}


def wer(reference: str, hypothesis: str, ignore_fillers: bool = False) -> float:
    return wer_details(reference, hypothesis, ignore_fillers)["wer"]
