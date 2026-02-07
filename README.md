# LaTeX to Beamer Presentation Converter

Automatically convert research papers (LaTeX) into professional Beamer presentations using intelligent heuristics and rule-based processing.

## Quick Start (Running from Zip)

### 1. Prerequisites

- **Python 3.10 or higher**
- **LaTeX distribution** (for PDF compilation):
  - macOS: `brew install --cask mactex`
  - Linux: `apt-get install texlive-full latexmk`
  - Windows: Install MiKTeX or TeX Live

### 2. Setup

Extract the zip and navigate to the folder:
```bash
cd AR
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run

Convert your paper to a presentation:
```bash
python -m src.agent.cli make-presentation <paper_folder> --yes
```

**Example:**
```bash
python -m src.agent.cli make-presentation arXiv-2602.04843v1 --yes
```

This will:
1. Find the main `.tex` file automatically
2. Parse the document structure
3. Generate `presentation.tex` in the paper folder
4. Compile to `presentation.pdf` automatically

### 4. Open Your Presentation

```bash
open arXiv-2602.04843v1/presentation.pdf
```

## Basic Usage

### Simple Generation
```bash
python -m src.agent.cli make-presentation my_paper/ --yes
```

### With Custom Options
```bash
python -m src.agent.cli make-presentation my_paper/ \
  --title "My Research" \
  --author "John Doe" \
  --style-prompt-opt "20 slides focusing on methodology" \
  --yes
```

### Skip PDF Compilation (Generate .tex only)
```bash
python -m src.agent.cli make-presentation my_paper/ --tex-only --yes
```

## Command Options

- `<folder>` - Path to folder with your paper (required)
- `--main-tex` - Specify main .tex file (otherwise auto-detects)
- `--title` - Presentation title
- `--author` - Author name(s)
- `--institute` - Institution/affiliation
- `--style-prompt-opt` - Instructions like "20 slides" or "focus on results"
- `--tex-only` - Skip PDF compilation
- `--yes` - Skip confirmation prompt

## Folder Structure

Your paper folder should contain:
```
my_paper/
├── main.tex          # Main LaTeX file (will be auto-detected)
├── bibliography.bib  # Bibliography (optional)
└── figures/          # Figures/images
    ├── fig1.pdf
    └── fig2.png
```

## How It Works

**No API keys needed!** The system uses intelligent heuristics:

1. **Find Main File** - Searches for `.tex` files with `\documentclass`
2. **Parse Structure** - Extracts sections, figures, equations, tables
3. **Generate Slides** - Applies professional formatting rules
4. **Compile PDF** - Uses `latexmk` to create the final PDF

## Troubleshooting

### "latexmk not found"
Install LaTeX:
- macOS: `brew install --cask mactex`
- Linux: `apt-get install texlive-full latexmk`

### Missing Figures
Check that figures are in a `figures/` subfolder relative to your main `.tex` file.

### Need Help?
See `DOCUMENTATION.md` for detailed technical information.

## Features

- ✅ Automatic section detection
- ✅ Professional slide formatting
- ✅ Table and figure handling
- ✅ Smart title shortening (6-word max)
- ✅ No API keys required
- ✅ Automatic PDF compilation
- ✅ Citation removal
- ✅ Equation extraction

## License

MIT License - See LICENSE file for details
