#!/bin/bash

echo "========================================="
echo "1. Happy path: local summarizer"
echo "========================================="
python3 main_shortcut.py technical.md

echo
echo "========================================="
echo "2. Happy path: Gemini default settings"
echo "========================================="
python3 main_shortcut.py technical.md --gemini

echo
echo "========================================="
echo "3. Gemini with sentence limit"
echo "========================================="
python3 main_shortcut.py technical.md --gemini --sentences 3

echo
echo "========================================="
echo "4. Gemini with LOW model"
echo "========================================="
python3 main_shortcut.py technical.md --gemini --model low

echo
echo "========================================="
echo "5. Gemini with MID model"
echo "========================================="
python3 main_shortcut.py technical.md --gemini --model mid

echo
echo "========================================="
echo "6. Gemini with HIGH model"
echo "========================================="
python3 main_shortcut.py technical.md --gemini --model high

echo
echo "========================================="
echo "7. Gemini with all options"
echo "========================================="
python3 main_shortcut.py technical.md --gemini --sentences 2 --model high

echo
echo "========================================="
echo "8. Validation: --sentences without --gemini"
echo "========================================="
python3 main_shortcut.py technical.md --sentences 3

echo
echo "========================================="
echo "9. Validation: --model without --gemini"
echo "========================================="
python3 main_shortcut.py technical.md --model high

echo
echo "========================================="
echo "10. Missing file"
echo "========================================="
python3 main_shortcut.py missing_file.md

echo
echo "========================================="
echo "11. Missing file + Gemini"
echo "========================================="
python3 main_shortcut.py missing_file.md --gemini

echo
echo "========================================="
echo "12. Invalid model"
echo "========================================="
python3 main_shortcut.py technical.md --gemini --model invalid

echo
echo "========================================="
echo "DONE"
echo "========================================="

echo
echo "========================================="
echo "13. Edge case: zero sentences"
echo "========================================="
python3 main_shortcut.py technical.md --gemini --sentences 0

echo
echo "========================================="
echo "14. Edge case: negative sentences"
echo "========================================="
python3 main_shortcut.py technical.md --gemini --sentences -5

echo
echo "========================================="
echo "14. Edge case: too big sentences"
python3 main_shortcut.py technical.md --gemini --sentences 999999