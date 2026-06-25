# Docalyzer

**AI-powered document summarizer for multiple file formats**

Docalyzer is a Python CLI tool that intelligently summarizes documents and code files in 18+ formats. It supports both local text processing and AI-powered summarization via Google's Gemini LLM API.

##  Features

- **Multi-format support**: PDF, Word, Excel, PowerPoint, Markdown, JSON, YAML, HTML, XML, CSV, plain text, and more
- **AI-powered summarization**: Optional Google Gemini API integration for intelligent summaries
- **Local fallback**: Built-in chunking algorithm for offline summarization
- **Production-ready**: Error handling with exponential backoff retries, comprehensive logging
- **Configurable**: Customize Gemini model effort, summary length, and output format via CLI flags or environment variables
- **Structured AI output**: Gemini summaries can be requested as plain text, Markdown, or JSON
- **Fully tested**: Unit tests covering CLI validation, model selection, output formatting, summarization, and Gemini retry handling

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

```bash
pip install -e .
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

**AI-powered summarization with JSON output:**
```bash
docalyzer path/to/document.pdf --gemini --output json --sentences 5
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
| `--output` | `txt \| md \| json` | `txt` | Output format for Gemini summaries (requires `--gemini`) |

### Output Formats

When using `--gemini`, you can control the LLM response format with `--output`:

| Output | Value | Description |
|--------|-------|-------------|
| Plain text | `txt` | Professional plain-text summary with readable spacing |
| Markdown | `md` | Structured Markdown summary with headers and bullet points |
| JSON | `json` | Structured JSON response with `document_title`, `short_description`, `short_summary`, and `full_summary` |

**Notes**:
- `--output` is valid only together with `--gemini`
- Local summarization ignores output formatting and returns plain text
- For JSON output, the prompt requests snake_case keys and a fixed response structure

### Model Effort Levels

When using `--gemini`, you can choose a higher or lower model effort depending on speed and quality needs:

| Effort | Gemini model |
|--------|--------------|
| `low` | `gemini-2.5-flash-lite` |
| `mid` | `gemini-2.5-flash` |
| `high` | `gemini-2.5-pro` |

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

# Request structured JSON output
docalyzer report.pdf --gemini --output json --sentences 5

# Combine Gemini, model effort, sentence count, and output format
docalyzer research.pdf --gemini --model low --sentences 7 --output md

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

For output formatting, the effective behavior is:
1. `--output txt|md|json` when using `--gemini`
2. Built-in default `txt`
3. Local summarization always returns plain text

### Local Summarization

When not using `--gemini`, the tool chunks your document and processes it locally:
- **Chunk size**: 2000 characters
- **Chunks per summary**: 2 sentences each
- **Final output**: Combined from all chunks
- **CLI note**: `--sentences`, `--model`, and `--output` apply only to Gemini summarization

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
- Output format prompt generation and fallback behavior
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

---

**Version**: 1.0.0 | **Last Updated**: 2026-06-25
