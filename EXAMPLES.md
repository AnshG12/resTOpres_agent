# Quick Start Examples

This guide provides practical examples for common use cases.

## Example 1: Basic Conversion

Convert a simple paper with default settings:

```bash
uv run agent make-presentation my_paper/ --yes
```

This will:
- Auto-detect the main `.tex` file
- Generate `output.tex` with ~20 slides
- Create `report.json` with processing stats

## Example 2: Custom Slide Count

Control the number of slides generated:

```bash
uv run agent make-presentation my_paper/ \
  --style-prompt-opt "Create exactly 15 slides" \
  --yes
```

Or specify a range:
```bash
uv run agent make-presentation my_paper/ \
  --style-prompt-opt "Generate between 12-15 slides focusing on results" \
  --yes
```

## Example 3: Conference Presentation

For a 15-minute conference talk:

```bash
uv run agent make-presentation paper_folder/ \
  --title "Novel Deep Learning Architecture" \
  --author "Smith et al." \
  --institute "MIT" \
  --output-tex conference_talk.tex \
  --style-prompt-opt "Conference presentation: 12 slides, emphasize methodology and results, minimal background" \
  --yes
```

## Example 4: Thesis Defense

For a 45-minute thesis defense:

```bash
uv run agent make-presentation thesis_folder/ \
  --title "PhD Thesis: Machine Learning in NLP" \
  --author "Jane Doe" \
  --institute "Stanford University" \
  --output-tex defense.tex \
  --style-prompt-opt "Thesis defense: 35-40 slides, comprehensive coverage, include related work and detailed results" \
  --yes
```

## Example 5: Journal Club

For a quick overview presentation:

```bash
uv run agent make-presentation downloaded_paper/ \
  --title "Paper Summary: Attention is All You Need" \
  --author "Vaswani et al." \
  --output-tex journal_club.tex \
  --style-prompt-opt "Journal club: 10 slides, focus on key contributions and main results only" \
  --yes
```

## Example 6: Methods-Focused

For a methods-heavy paper:

```bash
uv run agent make-presentation paper/ \
  --style-prompt-opt "18 slides prioritizing methodology and experimental design, minimal introduction" \
  --output-tex methods_focus.tex \
  --yes
```

## Example 7: Results-Focused

For a results-heavy presentation:

```bash
uv run agent make-presentation paper/ \
  --style-prompt-opt "20 slides emphasizing results, figures, and tables. Brief methodology." \
  --output-tex results_focus.tex \
  --yes
```

## Example 8: Batch Processing

Convert multiple papers:

```bash
#!/bin/bash
for paper in papers/*/; do
  basename=$(basename "$paper")
  uv run agent make-presentation "$paper" \
    --output-tex "presentations/${basename}.tex" \
    --style-prompt-opt "15 slides, balanced coverage" \
    --yes
done
```

## Example 9: With Specific Main File

If your paper has multiple .tex files:

```bash
uv run agent make-presentation paper_folder/ \
  --main-tex main.tex \
  --output-tex output.tex \
  --yes
```

## Example 10: Testing Output

After generation, compile to PDF and review:

```bash
# Generate presentation
uv run agent make-presentation paper/ --output-tex slides.tex --yes

# Compile to PDF
cd paper/
pdflatex ../slides.tex
pdflatex ../slides.tex  # Run twice for references

# Open PDF
open slides.pdf  # macOS
xdg-open slides.pdf  # Linux
```

## Common Patterns

### arXiv Papers

```bash
# Download from arXiv
wget https://arxiv.org/e-print/2301.12345
tar -xzf 2301.12345
cd 2301.12345/

# Generate slides
uv run agent make-presentation . \
  --title "Paper Title" \
  --author "Authors" \
  --output-tex ../arxiv_presentation.tex \
  --yes
```

### Overleaf Projects

```bash
# Download Overleaf project as .zip
# Extract and navigate to folder

uv run agent make-presentation overleaf_project/ \
  --main-tex main.tex \
  --output-tex slides.tex \
  --yes
```

### Multi-Chapter Thesis

```bash
# For thesis with chapters/ directory
uv run agent make-presentation thesis/ \
  --main-tex thesis.tex \
  --style-prompt-opt "40 slides covering all chapters, 2-3 slides per chapter" \
  --output-tex defense_slides.tex \
  --yes
```

## Advanced Customization

### Modifying Generated Slides

After generation, you can manually edit `output.tex`:

1. **Add custom slides**: Insert between `\begin{frame}...\end{frame}`
2. **Adjust layout**: Change column widths, add graphics
3. **Update theme**: Change `\usetheme{Madrid}` to other Beamer themes
4. **Modify colors**: Adjust `\usecolortheme{default}`

### Using with CI/CD

```yaml
# .github/workflows/generate-slides.yml
name: Generate Presentation

on:
  push:
    paths:
      - 'paper/**'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Generate slides
        run: |
          uv run agent make-presentation paper/ \
            --output-tex slides.tex \
            --yes
      - name: Upload slides
        uses: actions/upload-artifact@v4
        with:
          name: presentation
          path: slides.tex
```

## Troubleshooting Examples

### Problem: Too many slides

**Solution**: Reduce slide count in prompt:
```bash
uv run agent make-presentation paper/ \
  --style-prompt-opt "Generate exactly 12 slides" \
  --yes
```

### Problem: Missing figures

**Solution**: Check figures directory exists:
```bash
ls paper/figures/  # Should show .pdf, .png files
```

### Problem: Tables not rendering

**Solution**: Check source LaTeX has proper table structure:
```latex
% Good - will be detected
Row1 & val1 & val2 \\
Row2 & val3 & val4 \\

% Bad - won't be detected
Row1: val1, val2
Row2: val3, val4
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute improvements
- See [report.json](report.json) for detailed processing info after each run
