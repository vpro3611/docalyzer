#!/bin/bash

set -u

PASS_COUNT=0
FAIL_COUNT=0
INFO_COUNT=0

print_header() {
    echo
    echo "========================================="
    echo "$1"
    echo "========================================="
}

record_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    echo "PASS: $1"
}

record_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "FAIL: $1"
}

record_info() {
    INFO_COUNT=$((INFO_COUNT + 1))
    echo "INFO: $1"
}

run_expectation() {
    local label="$1"
    local expected_rc="$2"
    local expected_text="$3"
    shift 3

    print_header "$label"
    echo "Command: $*"

    local output
    output=$("$@" 2>&1)
    local rc=$?

    echo "$output"
    echo
    echo "Exit code: $rc"

    if [ "$rc" -ne "$expected_rc" ]; then
        record_fail "$label (expected exit $expected_rc, got $rc)"
        return
    fi

    if [ -n "$expected_text" ]; then
        if ! printf '%s' "$output" | grep -F -- "$expected_text" >/dev/null 2>&1; then
            record_fail "$label (missing expected text: $expected_text)"
            return
        fi
    fi

    record_pass "$label"
}

run_optional_live_case() {
    local label="$1"
    shift 1

    print_header "$label"
    echo "Command: $*"

    local output
    output=$("$@" 2>&1)
    local rc=$?

    echo "$output"
    echo
    echo "Exit code: $rc"

    if printf '%s' "$output" | grep -F -- "configuration error" >/dev/null 2>&1; then
        record_info "$label produced configuration error"
        return
    fi

    if printf '%s' "$output" | grep -F -- "summarization failed" >/dev/null 2>&1; then
        record_info "$label reached provider path but runtime failed cleanly"
        return
    fi

    if [ "$rc" -eq 0 ] && printf '%s' "$output" | grep -F -- "=== Summary ===" >/dev/null 2>&1; then
        record_pass "$label"
        return
    fi

    record_info "$label produced unexpected live-provider output; inspect manually"
}

OUTPUT_PATH="check/cli_test_output.json"
rm -f "$OUTPUT_PATH"

run_expectation \
    "1. Local summarizer happy path" \
    0 \
    "=== Summary ===" \
    python3 main_shortcut.py technical.md

run_expectation \
    "2. --sentences requires provider" \
    1 \
    "--sentences requires an AI provider" \
    python3 main_shortcut.py technical.md --sentences 3

run_expectation \
    "3. --model requires provider" \
    1 \
    "--model requires an AI provider" \
    python3 main_shortcut.py technical.md --model high

run_expectation \
    "4. --desc_level requires provider" \
    1 \
    "--desc_level requires an AI provider" \
    python3 main_shortcut.py technical.md --desc_level 2

run_expectation \
    "5. --sum_level requires provider" \
    1 \
    "--sum_level requires an AI provider" \
    python3 main_shortcut.py technical.md --sum_level 2

run_expectation \
    "6. non-plain --output requires provider" \
    1 \
    "--output requires an AI provider" \
    python3 main_shortcut.py technical.md --output json

run_expectation \
    "7. --tofile requires provider" \
    1 \
    "--tofile requires an AI provider" \
    python3 main_shortcut.py technical.md --tofile "$OUTPUT_PATH"

run_expectation \
    "8. --provider gemini accepts desc/sum levels" \
    1 \
    "Description level must be between 1 and 3" \
    python3 main_shortcut.py technical.md --provider gemini --desc_level 99

run_expectation \
    "9. --provider openai accepts desc/sum levels" \
    1 \
    "Summary level must be between 1 and 3" \
    python3 main_shortcut.py technical.md --provider openai --sum_level 0

run_expectation \
    "10. --gemini conflicts with non-Gemini provider" \
    1 \
    "--gemini cannot be combined with a non-Gemini provider" \
    python3 main_shortcut.py technical.md --gemini --provider openai

run_expectation \
    "11. Missing file in local mode" \
    1 \
    "File not found: missing_file.md" \
    python3 main_shortcut.py missing_file.md

run_expectation \
    "12. Missing file in AI mode" \
    1 \
    "File not found: missing_file.md" \
    python3 main_shortcut.py missing_file.md --provider gemini

run_expectation \
    "13. Invalid model choice is rejected by argparse" \
    2 \
    "invalid ModelEnum value" \
    python3 main_shortcut.py technical.md --provider gemini --model invalid

run_expectation \
    "14. Zero sentences rejected in AI mode" \
    1 \
    "Sentences cannot be less than 1 and more than 250" \
    python3 main_shortcut.py technical.md --provider gemini --sentences 0

run_expectation \
    "15. Negative sentences rejected in AI mode" \
    1 \
    "Sentences cannot be less than 1 and more than 250" \
    python3 main_shortcut.py technical.md --provider gemini --sentences -5

run_expectation \
    "16. Too many sentences rejected in AI mode" \
    1 \
    "Sentences cannot be less than 1 and more than 250" \
    python3 main_shortcut.py technical.md --provider gemini --sentences 999999

if [ -n "${GEMINI_API_KEY:-}" ]; then
    run_optional_live_case \
        "17. Live Gemini smoke test via canonical provider flag" \
        python3 main_shortcut.py technical.md --provider gemini --sentences 3 --desc_level 2 --sum_level 2

    run_optional_live_case \
        "18. Live Gemini smoke test via compatibility alias" \
        python3 main_shortcut.py technical.md --gemini --sentences 3 --desc_level 2 --sum_level 2
else
    print_header "17. Live Gemini smoke test via canonical provider flag"
    record_info "Skipped: GEMINI_API_KEY is not set"

    print_header "18. Live Gemini smoke test via compatibility alias"
    record_info "Skipped: GEMINI_API_KEY is not set"
fi

if [ -n "${OPENAI_API_KEY:-}" ]; then
    run_optional_live_case \
        "19. Live OpenAI smoke test" \
        python3 main_shortcut.py technical.md --provider openai --sentences 3 --desc_level 2 --sum_level 2
else
    print_header "19. Live OpenAI smoke test"
    record_info "Skipped: OPENAI_API_KEY is not set"
fi

rm -f "$OUTPUT_PATH"

print_header "SUMMARY"
echo "Passed: $PASS_COUNT"
echo "Failed: $FAIL_COUNT"
echo "Info:   $INFO_COUNT"

if [ "$FAIL_COUNT" -ne 0 ]; then
    exit 1
fi

exit 0
