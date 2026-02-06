# LaTeX to Beamer Presentation Converter

An intelligent agent that automatically converts research papers (LaTeX) into professional Beamer presentations. The system implements strict presentation design rules to ensure clean, readable slides with proper formatting, tables, and figure layouts.

## Features

### Automatic Structure Detection
- Parses LaTeX documents and extracts sections, figures, equations, and tables
- Intelligently combines text nodes to preserve paragraph structure
- Detects and preserves table rows with proper formatting

### Professional Slide Generation
- **Short Title Law**: Enforces 6-word maximum for slide titles
- **No Ghost Columns**: Only uses column layouts when images actually exist
- **Caption Sanitization**: Never splits sentences between title and body
- **Smart Figure Layout**: Filters long text bullets for narrow column layouts
- **Booktabs Tables**: Professional table formatting with proper headers

### LaTeX Cleaning & Processing
- Removes citations, labels, and references
- Handles custom macros and environments
- Strips broken LaTeX commands
- Sanitizes image paths

### Intelligent Content Filtering
- Automatically limits bullets per slide based on section priority
- Filters overly long text (>100 words or >500 chars) from narrow columns
- Splits long sections into continuation slides
- Enforces slide count limits

## Installation

### Prerequisites

- Python 3.10 or higher
- `uv` package manager ([install here](https://docs.astral.sh/uv/))

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd AR
```

2. Install dependencies with `uv`:
```bash
uv sync
```

Or with `pip`:
```bash
pip install -r requirements.txt
pip install -e .
```

3. Create a `.env` file (optional, only needed for LLM features):
```bash
cp .env.example .env
```

4. Add your Gemini API key to `.env`:
```
GEMINI_API_KEY=your_api_key_here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp
```

> **Note**: LLM integration is optional. The tool works without API keys using rule-based processing.

## Usage

### Basic Usage

Convert a research paper to a Beamer presentation:

```bash
uv run agent make-presentation <paper_folder> \
  --title "Your Paper Title" \
  --author "Author Names" \
  --output-tex output.tex \
  --style-prompt-opt "Create a focused research presentation with 18 slides"
```

### Command Line Options

```bash
uv run agent make-presentation --help
```

**Arguments:**
- `folder`: Path to folder containing the paper (.tex files, figures, bibliography)

**Options:**
- `--main-tex`: Specify main .tex file (otherwise auto-detects)
- `--title`: Presentation title (optional)
- `--author`: Author name(s) (optional)
- `--institute`: Institute/affiliation (optional)
- `--output-tex`: Output Beamer .tex file (default: `output.tex`)
- `--report-path`: Processing report JSON file (default: `report.json`)
- `--style-prompt-opt`: Style instructions (e.g., "18 slides with focus on methodology")
- `--yes`, `-y`: Skip confirmation prompt

### Example

```bash
uv run agent make-presentation arXiv-2602.04843v1 \
  --title "Fluid Reasoning Representations" \
  --author "Kharlapenko et al." \
  --output-tex presentation.tex \
  --style-prompt-opt "Create 15-18 slides focusing on methodology and results" \
  --yes
```

## The Three Laws of Slide Generation

### 1. The "SHORT TITLE" Law
**Constraint**: `\frametitle{...}` must NEVER exceed 6 words

**Bad Example:**
```latex
\frametitle{Figure 1 shows the accuracy of the model over time}
```

**Good Example:**
```latex
\frametitle{Model Accuracy Over Time}
```

**Implementation**: Long captions are automatically shortened, with full description moved to slide body.

### 2. The "NO GHOST COLUMNS" Rule
**Constraint**: Do NOT use `\begin{columns}` unless 100% certain an image exists

**Why**: Empty column layouts create awkward whitespace and confuse viewers.

**Implementation**: System checks if image file exists before generating column layout. Falls back to full-width `\begin{itemize}` if image is missing.

### 3. CAPTION SANITIZATION
**Constraint**: Never split a sentence between Title and Body

**Bad Example:**
- Title: "The results show that"
- Body: "accuracy improved."

**Good Example:**
- Title: "Experimental Results"
- Body: "The results show that accuracy improved."

**Implementation**: Pattern matching extracts meaningful short titles, with complete sentences preserved in body.

## The 8 Fix Protocols

### Protocol 1: Title Length Enforcement
- Max 6 words in `\frametitle`
- LaTeX commands stripped before truncation
- Natural phrase boundaries respected

### Protocol 2: Table Rendering
- Detects rows via ampersand delimiters (`&`)
- Splits concatenated table rows
- Renders with booktabs (`\toprule`, `\midrule`, `\bottomrule`)
- Auto-generates column headers for numbered items
- Uses `\scriptsize` font for data-heavy tables

### Protocol 3: Citation Removal
- Strips `\cite{}`, `\citep{}`, `\citet{}`
- Removes `\ref{}`, `\cref{}`, `\label{}`
- Handles multi-line citations

### Protocol 4: Ampersand Handling
- Escapes `&` → `\&` in regular text
- Preserves raw `&` in table cells (column delimiter)
- Handles both forms when detecting tables

### Protocol 5: Column Layout Safety
- Only creates columns if image exists
- Filters bullets >100 words or >500 chars for narrow columns
- Limits to 3 bullets max in column layouts
- Falls back to full-width layout if image missing

### Protocol 6: Manual Breaks
- Strips `\\` manual line breaks
- Normalizes whitespace
- Preserves LaTeX `\\` in commands

### Protocol 7: Demo Mode Prevention
- Never uses `\documentclass[demo]{beamer}`
- Regular `\usepackage{graphicx}` without [demo]
- Prevents black image placeholders

### Protocol 8: Path Sanitization
- Strips long folder prefixes
- Converts `arXiv-2602.04843v1/figures/img.pdf` → `figures/img.pdf`
- Keeps paths short and clean

## Architecture

```
src/agent/
├── __init__.py
├── cli.py                    # Command-line interface (Typer)
├── presentation_agent.py     # Main pipeline orchestrator
├── tex_cleaner.py           # LaTeX preprocessing
├── tex_parser.py            # Document structure parsing
├── beamer_generator.py      # Slide generation with 3 Laws + 8 Protocols
├── content_extractor.py     # Optional LLM summarization
├── gemini_client.py         # Gemini API client
├── hf_client.py             # Hugging Face API client (legacy)
└── config.py                # Settings and environment
```

### Pipeline Flow

1. **Load & Clean** (`tex_cleaner.py`)
   - Extract macros and custom commands
   - Strip comments and unnecessary LaTeX

2. **Parse Structure** (`tex_parser.py`)
   - Build hierarchical document tree
   - Identify sections, figures, equations, tables

3. **LLM Understanding** (`content_extractor.py`) [Optional]
   - Summarize content with Gemini API
   - Extract key points and themes

4. **Generate Beamer** (`beamer_generator.py`)
   - Apply 3 Laws and 8 Fix Protocols
   - Generate professional slides with proper formatting
   - Handle tables, figures, equations

5. **Output**
   - Save compiled `.tex` file
   - Generate processing report (JSON)

## Processing Report

Each run generates a `report.json` with:
- Input/output statistics
- Parsed sections and assets
- Processing pipeline log
- Detected figures and equations per section

Example:
```json
{
  "title": "My Paper Title",
  "slides_generated": 18,
  "section_assets": [
    {
      "section": "Introduction",
      "image_path": "figures/overview.pdf",
      "core_equation": null
    }
  ]
}
```

## Configuration

Environment variables (`.env`):

```bash
# Optional: Gemini API for LLM features
GEMINI_API_KEY=your_key_here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp

# Legacy: Hugging Face (not actively used)
HF_TOKEN=your_hf_token
HF_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
```

## Examples

### Minimal
```bash
uv run agent make-presentation paper_folder --yes
```

### Custom Slide Count
```bash
uv run agent make-presentation paper_folder \
  --style-prompt-opt "Generate exactly 20 slides" \
  --yes
```

### With Metadata
```bash
uv run agent make-presentation paper_folder \
  --title "Deep Learning for NLP" \
  --author "Smith et al." \
  --institute "MIT" \
  --output-tex slides.tex \
  --yes
```

## Troubleshooting

### LaTeX Compilation Errors

1. **Missing figures**: Check that `figures/` directory exists relative to output .tex
2. **Ampersand errors**: System auto-escapes `&` → `\&` in text (but not in tables)
3. **Black images**: Ensure no `[demo]` option in documentclass
4. **Long titles**: System auto-shortens to 6 words max

### Empty Slides

- Check that your paper has actual content (not just abstract)
- Try increasing slide limit in style prompt: `"Generate 25 slides"`

### Tables Not Rendering

- Ensure table rows contain `&` delimiters
- Minimum 2 rows required for table detection
- All rows must have same column count

## Development

### Running Tests
```bash
# Run test conversion
python test_table_split.py
```

### Project Structure
```
AR/
├── src/agent/           # Main source code
├── arXiv-*/            # Example paper (for testing)
├── figures/            # Generated or input figures
├── output_final_fixed.tex  # Generated presentation
├── report.json         # Processing report
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project metadata
└── .env               # API keys (not committed)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with multiple papers
5. Submit a pull request

## License

[Add your license here]

## Acknowledgments

Built for converting academic papers into clean, professional presentations with minimal manual intervention.

## Citation

If you use this tool in your research workflow, please cite:

```bibtex
@software{latex_beamer_converter,
  title={LaTeX to Beamer Presentation Converter},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/AR}
}
```
