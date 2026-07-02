# Docalyzer

**AI-powered document summarizer for multiple file formats**

Docalyzer is a Python CLI tool that intelligently summarizes documents and code files in 18+ formats. It supports both local text processing and AI-powered summarization via pluggable providers, currently Google Gemini and OpenAI.

##  Features

- **Multi-format support**: PDF, Word, Excel, PowerPoint, Markdown, JSON, YAML, HTML, XML, CSV, plain text, and more
- **AI-powered summarization**: Optional provider-based AI integration with Google Gemini and OpenAI
- **Local fallback**: Built-in chunking algorithm for offline summarization
- **Production-ready**: Error handling with exponential backoff retries, comprehensive logging
- **Configurable**: Customize AI provider, provider-specific model effort, summary length, description depth, summary detail, and output format via CLI flags or environment variables
- **Granular AI detail control**: Independently tune descriptive depth with `--desc_level` and summary richness with `--sum_level`
- **Structured AI output**: AI summaries can be requested as plain text, Markdown, or JSON with any supported provider
- **Save summaries to disk**: AI output can be written to a user-provided path with `--tofile`
- **JSON cleanup on save**: Saved JSON output is normalized by stripping Markdown fences and pretty-printing valid JSON
- **Backward compatibility preserved**: Legacy `--gemini` still works as an alias for `--provider gemini`
- **Fully tested**: Unit tests cover CLI validation, provider/model resolution, shared prompt/output helpers, file output, summarization, and Gemini/OpenAI retry handling

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

### 2. Configure an AI Provider (Optional)

Create a `.env` file in the project root for the provider you want to use:

```env
# Gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_RETRIES=3

# OpenAI
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1
OPENAI_MAX_RETRIES=3
```

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
Get your OpenAI API key from the [OpenAI API platform](https://platform.openai.com/api-keys).

### 3. Summarize a Document

**Local summarization (no API key required):**
```bash
docalyzer path/to/document.pdf
```

**AI-powered summarization with Gemini:**
```bash
docalyzer path/to/document.pdf --provider gemini
```

**AI-powered summarization with OpenAI:**
```bash
docalyzer path/to/document.pdf --provider openai
```

**AI-powered summarization with model effort selection:**
```bash
docalyzer path/to/document.pdf --provider gemini --model high --sentences 7
```

**AI-powered summarization with Markdown output:**
```bash
docalyzer path/to/document.pdf --provider gemini --output md
```

**AI-powered summarization with OpenAI and Markdown output:**
```bash
docalyzer path/to/document.pdf --provider openai --output md
```

**AI-powered summarization with detailed description and full summary output:**
```bash
docalyzer path/to/document.pdf --provider gemini --desc_level 3 --sum_level 3 --sentences 6
```

**AI-powered summarization with JSON output:**
```bash
docalyzer path/to/document.pdf --provider gemini --output json --sentences 5
```

**AI-powered summarization with OpenAI JSON output:**
```bash
docalyzer path/to/document.pdf --provider openai --output json --sentences 5
```

**Save AI output to a file (default plain text):**
```bash
docalyzer path/to/document.pdf --provider gemini --tofile summaries/document_summary
```

**Save OpenAI output to a file:**
```bash
docalyzer path/to/document.pdf --provider openai --tofile summaries/document_summary
```

**Save AI Markdown output to a file:**
```bash
docalyzer path/to/document.pdf --provider gemini --output md --tofile summaries/document_summary.md
```

**Save AI JSON output to a file:**
```bash
docalyzer path/to/document.pdf --provider gemini --output json --tofile summaries/document_summary.json
```

##  Usage

### Basic Usage

```bash
docalyzer <filepath> [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--provider` | `gemini \| openai` | local mode | Enable AI summarization with the selected provider. If omitted, Docalyzer uses local summarization |
| `--gemini` | flag | False | Deprecated compatibility alias for `--provider gemini` |
| `--sentences` | int | `5` in AI mode | Maximum number of sentences in the AI summary (`1-250`, requires AI provider) |
| `--model` | `low \| mid \| high` | `mid` in AI mode | Provider-neutral effort level mapped to a concrete model for the selected AI provider |
| `--desc_level` | `1 \| 2 \| 3` | `2` in AI mode | Controls how concise vs. in-depth the descriptive sections should be (requires AI provider) |
| `--sum_level` | `1 \| 2 \| 3` | `2` in AI mode | Controls how concise vs. full the summary should be while still respecting `--sentences` (requires AI provider) |
| `--output` | `txt \| md \| json` | `txt` | Output format. `md` and `json` require AI provider; default `txt` is used otherwise |
| `--tofile` | path | `None` | Save AI output to the provided file path (requires AI provider) |

### Output Formats

When using an AI provider, you can control the LLM response format with `--output`:

| Output | Value | Description |
|--------|-------|-------------|
| Plain text | `txt` | Professional plain-text summary with readable spacing |
| Markdown | `md` | Structured Markdown summary with headers and bullet points |
| JSON | `json` | Structured JSON response with `document_title`, `short_description`, `short_summary`, and `full_summary` |

**Notes**:
- `--tofile` works only together with an AI provider
- `--output md` and `--output json` require an AI provider
- Default output is `txt`
- If `--tofile` is used without a file extension, Docalyzer appends one based on the selected output format
- If `--tofile` includes an extension, it must match the selected output format
- Local summarization ignores output formatting and returns plain text
- For JSON output, the prompt requests snake_case keys and a fixed response structure
- Saved JSON output is cleaned before writing: Markdown code fences are removed and valid JSON is pretty-printed with indentation

### AI Providers

Docalyzer currently supports these AI providers:

| Provider | CLI value | Credentials | Default model env var | Retry env var |
|----------|-----------|-------------|-----------------------|---------------|
| Gemini | `gemini` | `GEMINI_API_KEY` | `GEMINI_MODEL` | `GEMINI_MAX_RETRIES` |
| OpenAI | `openai` | `OPENAI_API_KEY` | `OPENAI_MODEL` | `OPENAI_MAX_RETRIES` |

### Model Effort Levels

When using an AI provider, you can choose a higher or lower model effort depending on speed and quality needs.

#### Gemini model mapping

| Effort | Gemini model |
|--------|--------------|
| `low` | `gemini-2.5-flash-lite` |
| `mid` | `gemini-2.5-flash` |
| `high` | `gemini-2.5-pro` |

#### OpenAI model mapping

| Effort | OpenAI model |
|--------|--------------|
| `low` | `gpt-4.1-mini` |
| `mid` | `gpt-4.1` |
| `high` | `gpt-5.2` |

### AI Detail Levels

When using an AI provider, you can separately control the descriptive depth and the overall summary richness:

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
- Both flags require an AI provider
- Both flags accept values from `1` to `3`
- `--desc_level` controls descriptive/explanatory sections
- `--sum_level` controls the density of the actual summary while still respecting `--sentences`
- Local summarization ignores both flags

### Examples

```bash
# Summarize a text file (local)
docalyzer document.txt

# Summarize with Gemini and a custom summary length
docalyzer report.pdf --provider gemini --sentences 3

# Use Gemini AI for better summaries
docalyzer whitepaper.docx --provider gemini

# Use OpenAI for AI summarization
docalyzer whitepaper.docx --provider openai

# Use higher effort for a richer summary
docalyzer research.pdf --provider gemini --model high

# Request Markdown output
docalyzer README.md --provider gemini --output md

# Request Markdown output with OpenAI
docalyzer README.md --provider openai --output md

# Ask for a brief description but a fuller summary
docalyzer report.pdf --provider gemini --desc_level 1 --sum_level 3 --sentences 6

# Ask for an in-depth description and a rich Markdown response
docalyzer technical.md --provider gemini --desc_level 3 --sum_level 3 --output md --sentences 6

# Request structured JSON output
docalyzer report.pdf --provider gemini --output json --sentences 5

# Request structured JSON output with OpenAI
docalyzer report.pdf --provider openai --output json --sentences 5

# Save default AI text output to a file
docalyzer report.pdf --provider gemini --tofile outputs/report_summary

# Save Markdown output to a file
docalyzer research.pdf --provider gemini --model low --sentences 7 --output md --tofile outputs/research_summary.md

# Save cleaned, pretty-printed JSON output to a file
docalyzer report.pdf --provider gemini --output json --tofile outputs/report_summary.json

# Legacy compatibility alias for Gemini
docalyzer src/main.py --gemini
```

##  Configuration

### Environment Variables

```env
# Gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_RETRIES=3

# OpenAI
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1
OPENAI_MAX_RETRIES=3
```

`GEMINI_MODEL` and `OPENAI_MODEL` define the concrete provider model used by default for AI summarization. The CLI `--model` flag has higher priority and lets you choose between `low`, `mid`, and `high` effort presets at runtime.

### Configuration Priority

1. Command-line flags (highest priority)
2. Environment variables
3. Defaults (lowest priority)

For AI provider and model selection, the effective order is:
1. `--provider gemini|openai` (or legacy `--gemini`)
2. `--model low|mid|high`
3. Provider-specific environment model (`GEMINI_MODEL` or `OPENAI_MODEL`)
4. Built-in provider default model

For output formatting and file saving, the effective behavior is:
1. `--output txt|md|json` selects the requested output format
2. Built-in default output is `txt`
3. `--output md|json` requires an AI provider
4. `--tofile <path>` requires an AI provider
5. If `--tofile` has no extension, one is appended from the selected format
6. Local summarization always returns plain text

For AI detail controls, the effective behavior is:
1. `--desc_level 1|2|3` selects description depth
2. `--sum_level 1|2|3` selects summary richness
3. Built-in defaults for both are `2`
4. Both flags require an AI provider
5. `--sum_level` still respects the sentence cap from `--sentences`
6. The same controls are shared across Gemini and OpenAI through the common prompt builder

### Local Summarization

When no AI provider is selected, the tool chunks your document and processes it locally:
- **Chunk size**: 2000 characters
- **Chunks per summary**: 2 sentences each
- **Final output**: Combined from all chunks
- **CLI note**: `--provider` enables AI summarization; legacy `--gemini` is equivalent to `--provider gemini`
- **AI-only options**: `--sentences`, `--model`, `--desc_level`, `--sum_level`, `--output md|json`, and `--tofile` apply only when an AI provider is selected

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
├── README.md                      # This file (user documentation)
├── technical.md                   # Architecture & design decisions
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata
├── .env                           # Environment variables (create this)
├── main_shortcut.py               # Convenience entrypoint
├── src/docalyzer/
│   ├── main.py                    # CLI entrypoint and validation
│   ├── summarizer.py              # Local vs. AI summarization routing
│   ├── provider_enum.py           # Supported AI providers
│   ├── ai_types.py                # Shared AI request/client contracts
│   ├── ai_errors.py               # Shared AI error hierarchy
│   ├── ai_executor.py             # Provider-neutral request execution
│   ├── ai_client_factory.py       # Provider/model resolution
│   ├── prompt_builder.py          # Shared prompt construction
│   ├── output_writer.py           # Shared output normalization and saving
│   ├── gemini_client.py           # Gemini SDK integration
│   ├── openai_client.py           # OpenAI SDK integration
│   └── file_loaders.py            # Multi-format file parsing
└── tests/
    ├── test_main.py               # CLI validation tests
    ├── test_summarizer.py         # Routing/local summarization tests
    ├── test_gemini_client.py      # Gemini client tests
    ├── test_openai_client.py      # OpenAI client tests
    ├── test_ai_client_factory.py  # Provider/model factory tests
    ├── test_ai_executor.py        # Shared executor/protocol tests
    └── test_shared_ai_components.py # Shared prompt/output helper tests
```

##  License

This project is open source. See LICENSE file for details.

##  Contributing

Contributions are welcome! Areas for enhancement:
- Additional file format support
- Additional export formats and provider capabilities
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

**Version**: 1.1.0 | **Last Updated**: 2026-07-02
