# Docalyzer

**AI-powered document summarizer for multiple file formats**

Docalyzer is a Python CLI tool that intelligently summarizes documents and code files in 18+ formats. It supports both local text processing and AI-powered summarization via Google's Gemini LLM API.

##  Features

- **Multi-format support**: PDF, Word, Excel, PowerPoint, Markdown, JSON, YAML, HTML, XML, CSV, plain text, and more
- **AI-powered summarization**: Optional Google Gemini API integration for intelligent summaries
- **Local fallback**: Built-in chunking algorithm for offline summarization
- **Production-ready**: Error handling with exponential backoff retries, comprehensive logging
- **Configurable**: Customize Gemini model effort, summary length, description depth, summary detail, and output format via CLI flags or environment variables
- **Granular AI detail control**: Independently tune descriptive depth with `--desc_level` and summary richness with `--sum_level`
- **Structured AI output**: Gemini summaries can be requested as plain text, Markdown, or JSON
- **Save summaries to disk**: Gemini output can be written to a user-provided path with `--tofile`
- **JSON cleanup on save**: Saved JSON output is normalized by stripping Markdown fences and pretty-printing valid JSON
- **Fully tested**: Unit tests covering CLI validation, model selection, output formatting, file output, summarization, and Gemini retry handling

##  Supported File Formats

| Format | Extension | Library |
|--------|-----------|---------|
| Plain Text | `.txt` | Built-in |
| Markdown | `.md` | Built-in |
| PDF | `.pdf` | PyPDF2 |
| Word Document | `.docx` | python-docx |
| Excel Spreadsheet | `.xlsx` | openpyxl |
| PowerPoint | `.pptx` | python-pptx |
| JSON | `.json` | Built-in |
| YAML | `.yaml`, `.yml` | PyYAML |
| HTML | `.html`, `.htm` | beautifulsoup4 |
| XML | `.xml` | Built-in |
| CSV | `.csv` | Built-in |
| Source Code | `.py`, `.js`, `.ts`, `.go`, `.java`, `.c`, `.cpp` | Built-in |

##  Quick Start

### 1. Install

**For local development:**
```bash
pip install -e .
```

**For CLI-style isolated install (recommended for end users):**
```bash
pipx install .
```

### 2. Configure Gemini API (Optional)

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_RETRIES=3
```

Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey).

### 3. Summarize a Document

**Local summarization (no API key required):**
```bash
docalyzer path/to/document.pdf
```

**AI-powered summarization (requires Gemini API key):**
```bash
docalyzer path/to/document.pdf --gemini
```

**AI-powered summarization with model effort selection:**
```bash
docalyzer path/to/document.pdf --gemini --model high --sentences 7
```

**AI-powered summarization with Markdown output:**
```bash
docalyzer path/to/document.pdf --gemini --output md
```

**AI-powered summarization with detailed description and full summary output:**
```bash
docalyzer path/to/document.pdf --gemini --desc_level 3 --sum_level 3 --sentences 6
```

**AI-powered summarization with JSON output:**
```bash
docalyzer path/to/document.pdf --gemini --output json --sentences 5
```

**Save Gemini output to a file (default plain text):**
```bash
docalyzer path/to/document.pdf --gemini --tofile summaries/document_summary
```

**Save Gemini Markdown output to a file:**
```bash
docalyzer path/to/document.pdf --gemini --output md --tofile summaries/document_summary.md
```

**Save Gemini JSON output to a file:**
```bash
docalyzer path/to/document.pdf --gemini --output json --tofile summaries/document_summary.json
```

##  Usage

### Basic Usage

```bash
docalyzer <filepath> [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--sentences` | int | 5 | Maximum number of sentences in the Gemini summary (`1-250`, requires `--gemini`) |
| `--gemini` | flag | False | Use Google Gemini API for summarization |
| `--model` | `low \| mid \| high` | `mid` | Gemini effort level to use for AI summarization (requires `--gemini`) |
| `--desc_level` | `1 \| 2 \| 3` | `2` | Controls how concise vs. in-depth the descriptive sections should be (requires `--gemini`) |
| `--sum_level` | `1 \| 2 \| 3` | `2` | Controls how concise vs. full the summary should be while still respecting `--sentences` (requires `--gemini`) |
| `--output` | `txt \| md \| json` | `txt` | Output format. `md` and `json` require `--gemini`; default `txt` is used otherwise |
| `--tofile` | path | `None` | Save Gemini output to the provided file path (requires `--gemini`) |

### Output Formats

When using `--gemini`, you can control the LLM response format with `--output`:

| Output | Value | Description |
|--------|-------|-------------|
| Plain text | `txt` | Professional plain-text summary with readable spacing |
| Markdown | `md` | Structured Markdown summary with headers and bullet points |
| JSON | `json` | Structured JSON response with `document_title`, `short_description`, `short_summary`, and `full_summary` |

**Notes**:
- `--tofile` works only together with `--gemini`
- `--output md` and `--output json` require `--gemini`
- Default output is `txt`
- If `--tofile` is used without a file extension, Docalyzer appends one based on the selected output format
- If `--tofile` includes an extension, it must match the selected output format
- Local summarization ignores output formatting and returns plain text
- For JSON output, the prompt requests snake_case keys and a fixed response structure
- Saved JSON output is cleaned before writing: Markdown code fences are removed and valid JSON is pretty-printed with indentation

### Model Effort Levels

When using `--gemini`, you can choose a higher or lower model effort depending on speed and quality needs:

| Effort | Gemini model |
|--------|--------------|
| `low` | `gemini-2.5-flash-lite` |
| `mid` | `gemini-2.5-flash` |
| `high` | `gemini-2.5-pro` |

### AI Detail Levels

When using `--gemini`, you can separately control the descriptive depth and the overall summary richness:

#### Description levels (`--desc_level`)

| Level | Meaning |
|-------|---------|
| `1` | Brief description with minimal explanatory detail |
| `2` | Detailed description with balanced explanation |
| `3` | Very detailed, in-depth description |

#### Summary levels (`--sum_level`)

| Level | Meaning |
|-------|---------|
| `1` | Concise summary that stays compact within the sentence cap |
| `2` | Detailed summary with balanced coverage within the sentence cap |
| `3` | Full, richer summary that uses the available sentence budget more aggressively |

**Notes**:
- Both flags require `--gemini`
- Both flags accept values from `1` to `3`
- `--desc_level` controls descriptive/explanatory sections
- `--sum_level` controls the density of the actual summary while still respecting `--sentences`
- Local summarization ignores both flags

### Examples

```bash
# Summarize a text file (local)
docalyzer document.txt

# Summarize with Gemini and a custom summary length
docalyzer report.pdf --gemini --sentences 3

# Use Gemini AI for better summaries
docalyzer whitepaper.docx --gemini

# Use higher effort for a richer summary
docalyzer research.pdf --gemini --model high

# Request Markdown output
docalyzer README.md --gemini --output md

# Ask for a brief description but a fuller summary
docalyzer report.pdf --gemini --desc_level 1 --sum_level 3 --sentences 6

# Ask for an in-depth description and a rich Markdown response
docalyzer technical.md --gemini --desc_level 3 --sum_level 3 --output md --sentences 6

# Request structured JSON output
docalyzer report.pdf --gemini --output json --sentences 5

# Save default Gemini text output to a file
docalyzer report.pdf --gemini --tofile outputs/report_summary

# Save Markdown output to a file
docalyzer research.pdf --gemini --model low --sentences 7 --output md --tofile outputs/research_summary.md

# Save cleaned, pretty-printed JSON output to a file
docalyzer report.pdf --gemini --output json --tofile outputs/report_summary.json

# Summarize source code
docalyzer src/main.py --gemini
```

##  Configuration

### Environment Variables

```env
# Required for --gemini flag
GEMINI_API_KEY=your_api_key_here

# Optional: customize Gemini behavior
GEMINI_MODEL=gemini-2.5-flash          # Model to use (default: gemini-2.5-flash)
GEMINI_MAX_RETRIES=3                   # Max retries on transient errors (default: 3)
```

`GEMINI_MODEL` defines the concrete Gemini model used by default for AI summarization. The CLI `--model` flag has higher priority and lets you choose between `low`, `mid`, and `high` effort presets at runtime.

### Configuration Priority

1. Command-line flags (highest priority)
2. Environment variables
3. Defaults (lowest priority)

For Gemini model selection, the effective order is:
1. `--model low|mid|high`
2. `GEMINI_MODEL`
3. Built-in default model

For output formatting and file saving, the effective behavior is:
1. `--output txt|md|json` selects the requested output format
2. Built-in default output is `txt`
3. `--output md|json` requires `--gemini`
4. `--tofile <path>` requires `--gemini`
5. If `--tofile` has no extension, one is appended from the selected format
6. Local summarization always returns plain text

For Gemini detail controls, the effective behavior is:
1. `--desc_level 1|2|3` selects description depth
2. `--sum_level 1|2|3` selects summary richness
3. Built-in defaults for both are `2`
4. Both flags require `--gemini`
5. `--sum_level` still respects the sentence cap from `--sentences`

### Local Summarization

When not using `--gemini`, the tool chunks your document and processes it locally:
- **Chunk size**: 2000 characters
- **Chunks per summary**: 2 sentences each
- **Final output**: Combined from all chunks
- **CLI note**: `--sentences`, `--model`, `--desc_level`, and `--sum_level` apply only to Gemini summarization; `--output md|json` and `--tofile` also require Gemini

##  Installation & Development

### Requirements

- Python 3.10+
- Virtual environment (recommended)

### Setup for Development

```bash
# Clone the repository
git clone https://github.com/vpro3611/docalyzer.git
cd docalyzer

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .

# Run tests
python3 -m unittest discover tests -v
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Build Release Artifacts

To build a distributable wheel and source archive for GitHub Releases:

```bash
python3 -m pip install build
python3 -m build
```

This produces artifacts in `dist/`, typically:
- `docalyzer-<version>-py3-none-any.whl`
- `docalyzer-<version>.tar.gz`

You can then validate the built CLI locally:

```bash
python3 -m pip install --force-reinstall dist/docalyzer-<version>-py3-none-any.whl
docalyzer --help
```

##  Testing

Run the test suite:

```bash
# All tests
python3 -m unittest discover tests -v

# Gemini client tests only
python3 -m unittest tests.test_gemini_client -v
```

The test suite includes:
- File loader tests for all 18+ formats
- Gemini client error handling and retry logic
- CLI argument parsing and validation
- Description and summary level prompt generation and validation
- Output format prompt generation and fallback behavior
- File output behavior, including extension handling and JSON normalization
- Integration tests for end-to-end workflows

##  Error Handling

Docalyzer includes robust error handling:

### Local Summarization
- Returns error message if file cannot be read
- Gracefully handles unsupported formats
- Handles missing optional dependencies

### Gemini API
- **Transient errors** (5xx, timeout): Automatic retry with exponential backoff
- **Validation errors** (401, 400): Immediate failure with clear error message
- **Max retries exceeded**: Returns error message instead of crashing
- **Missing API key**: Clear error on startup

Example error handling:
```bash
# Missing API key
$ docalyzer doc.pdf --gemini
Error: Gemini configuration error: GEMINI_API_KEY is not set in the environment

# File not found
$ docalyzer nonexistent.pdf
File not found: nonexistent.pdf

# Unsupported format
$ docalyzer file.xyz
Error: Unsupported file type: .xyz
```

##  Performance

- **Local summarization**: < 100ms for typical documents
- **Gemini API call**: ~1-3 seconds (depends on document size and API load)
- **Large documents** (>100MB): Automatically chunked to avoid timeouts

##  Project Structure

```
docalyzer/
├── README.md                 # This file (user documentation)
├── technical.md              # Architecture & design decisions
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project metadata
├── .env                       # Environment variables (create this)
├── src/docalyzer/
│   ├── main.py              # CLI entrypoint
│   ├── summarizer.py        # Summarization logic
│   ├── gemini_client.py     # Gemini API abstraction with retries
│   └── file_loaders.py      # Multi-format file parsing
└── tests/
    └── test_gemini_client.py # Comprehensive test suite
```

##  License

This project is open source. See LICENSE file for details.

##  Contributing

Contributions are welcome! Areas for enhancement:
- Additional file format support
- Additional export formats beyond current Gemini output options
- Web UI or API server
- CI/GitHub Actions pipeline

##  Documentation

- **[technical.md](technical.md)** - Architecture, design decisions, and implementation details for developers

##  Release Notes

For a Phase 1 release, Docalyzer is distributed as a standard Python CLI package:
- installable from source with `pip install .` or `pipx install .`
- buildable into a wheel and source archive with `python3 -m build`
- suitable for attaching `.whl` and `.tar.gz` artifacts to GitHub Releases

---

**Version**: 1.0.0 | **Last Updated**: 2026-06-26
