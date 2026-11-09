"""Known-answer tests for agreement metrics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agreement import cohen_kappa, interpret, percent_agreement, weighted_kappa, within_one  # noqa: E402


def test_textbook_kappa():
    # Classic 2x2 example: 20 yes/yes, 5 yes/no, 10 no/yes, 15 no/no
    # observed = 35/50 = 0.70, chance = 0.50  ->  kappa = 0.40
    a = ["yes"] * 25 + ["no"] * 25
    b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
    assert abs(percent_agreement(a, b) - 0.70) < 1e-9
    assert abs(cohen_kappa(a, b) - 0.40) < 1e-9


def test_perfect_agreement():
    assert cohen_kappa(["a", "b", "a"], ["a", "b", "a"]) == 1.0
    assert weighted_kappa([1, 3, 5, 4], [1, 3, 5, 4]) == 1.0


def test_no_variation_is_undefined():
    assert cohen_kappa(["Safe"] * 5, ["Safe"] * 5) is None
    assert interpret(None) == "n/a (no variation)"


def test_weighted_penalizes_big_gaps_more():
    off_by_one = weighted_kappa([1, 2, 3, 4, 5, 5], [2, 2, 3, 4, 4, 5])
    off_by_four = weighted_kappa([1, 2, 3, 4, 5, 5], [5, 2, 3, 4, 1, 5])
    assert off_by_one > off_by_four


def test_weighted_matches_reference_formula():
    # cross-check against scikit-learn's implementation when available
    try:
        from sklearn.metrics import cohen_kappa_score
    except ImportError:
        return
    a, b = [5, 4, 4, 3, 5, 2, 1, 4], [5, 5, 4, 3, 4, 2, 2, 4]
    ref = cohen_kappa_score(a, b, weights="quadratic", labels=[1, 2, 3, 4, 5])
    assert abs(weighted_kappa(a, b) - ref) < 1e-9


def test_within_one():
    assert within_one([5, 4, 1], [4, 4, 3]) == 2 / 3
