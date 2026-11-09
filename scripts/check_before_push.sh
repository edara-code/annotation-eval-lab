#!/bin/bash
# Run before every push: stops at the first failure.
set -e
cd "$(dirname "$0")/.."

echo "1/4  Known-answer tests for metrics..."
python -m pytest -q tests/

echo "2/4  Running analysis scripts..."
python src/analyze_annotations.py annotations/image/round1.json > /dev/null
python src/analyze_audio.py > /dev/null
if [ -f src/analyze_wer.py ]; then python src/analyze_wer.py > /dev/null; fi
if [ -f src/analyze_llm_eval.py ]; then python src/analyze_llm_eval.py > /dev/null; fi

echo "3/4  Checking automated quality checks report no issues..."
if grep -q '^- `' reports/audio_round1_summary.md; then
  echo "❌ Audio quality issues found - see reports/audio_round1_summary.md"
  exit 1
fi

echo "4/4  Files changed (review before pushing):"
git status --short

echo ""
echo "✅ All checks passed - safe to commit and push."
