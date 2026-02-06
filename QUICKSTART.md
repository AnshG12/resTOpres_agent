# 🚀 Quick Command Reference

## TL;DR - Simple Usage

```bash
cd /Users/anshgoel/Desktop/AR

# Just run it - LLM is automatically used if API key is configured
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 --yes

# When prompted for style, just press Enter or type your preferences:
# Examples: "50 slides" or "brief presentation" or "detailed methodology"
```

**That's it!** The system automatically:
- Uses LLM for intelligent content generation (if API key present)
- Falls back to rule-based mode (if no API key or limit exceeded)
- Determines optimal slide count (5-100)
- Generates smart summaries instead of copy-paste

---

## Setup (One-Time)

### Configure Gemini API for LLM Mode

1. **Get API Key**: https://ai.google.dev/
2. **Create `.env` file**:
   ```bash
   GEMINI_API_KEY=your_key_here
   LLM_PROVIDER=gemini
   GEMINI_MODEL=gemini-2.0-flash-exp
   ```

3. **Done!** LLM is now your PRIMARY brain

**No API key?** System automatically uses rule-based fallback (still works, just less intelligent)

---

## How It Works

### 🧠 LLM Mode (PRIMARY - Default when API key present)
- **Content**: Smart summarization, key insights, presentation-ready bullets
- **Slide Count**: Dynamically determined (5-100) based on content density
- **Quality**: Excellent presentation flow
- **Speed**: ~30-60s (API calls)
- **Cost**: ~$0.01-0.15 per paper

### ⚙️ Rule-Based Mode (FALLBACK - Backup when needed)
- **Content**: Direct text extraction with formatting rules
- **Slide Count**: Fixed (~20) or user-specified
- **Quality**: Good structure, basic content
- **Speed**: Fast (~5s)
- **Cost**: Free

**System automatically chooses best mode available!**

---

## Example Commands

### Let LLM decide everything (RECOMMENDED)
```bash
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 --yes
# Press Enter when prompted, or type: "Standard research presentation"
```

### Detailed presentation
```bash
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 \
  --style-prompt-opt "50 slides with detailed methodology coverage" \
  --yes
```

### Brief conference talk
```bash
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 \
  --style-prompt-opt "12 slides focusing on results" \
  --yes
```

### Focus on specific sections
```bash
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 \
  --style-prompt-opt "25 slides, detailed experiments section, brief intro" \
  --yes
```

### Custom output name
```bash
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 \
  --output-tex my_presentation.tex \
  --yes
```

---

## Behavior Summary

| Scenario | What Happens |
|----------|-------------|
| ✅ API key configured | LLM is PRIMARY brain for content |
| ❌ No API key | Rule-based fallback (still works!) |
| ⚠️ API limit exceeded | Automatic fallback to rules per section |
| 🔧 Forced rule mode | Remove API key from `.env` |

---

## What Gets Generated

- `output.tex` (or your custom name)
- Professional Beamer LaTeX presentation
- Ready to compile: `pdflatex output.tex`
- `report.json` with generation stats

---

## The Pipeline

```
Your Paper (.tex)
    ↓
Parse Structure (tex_parser.py)
    ↓
┌───────────────────────────┐
│ LLM MODE (PRIMARY)        │
│ ✓ Analyze content density │
│ ✓ Determine slide count   │ ← Intelligent
│ ✓ Generate smart bullets  │   decision-making
│ ✓ Extract key insights    │
└───────────────────────────┘
    ↓ (fallback if LLM fails)
┌───────────────────────────┐
│ RULE MODE (BACKUP)        │
│ • Apply 3 Laws            │ ← Deterministic
│ • Apply 8 Protocols       │   rules
│ • Format text content     │
└───────────────────────────┘
    ↓
Professional Beamer Slides
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'agent'"
```bash
# Use this exact command:
uv run python -m src.agent.cli make-presentation <folder> --yes
```

### "LLM mode not activating"
1. Check `.env` file exists with `GEMINI_API_KEY=...`
2. Verify API key: `uv run python -c "from src.agent.config import load_settings; print(load_settings().gemini_api_key)"`
3. Check logs - should see "🧠 LLM mode: Using intelligent content generation"

### "API rate limit exceeded"
System automatically falls back to rule-based mode per section. Your presentation will still be generated!

---

## Advanced: Force Rule-Based Mode

If you want to test rule-based mode specifically:
1. Temporarily rename `.env` to `.env.backup`
2. Run normally - system uses fallback
3. Restore `.env` when done

---

**Quick Start Command (Copy-Paste):**
```bash
cd /Users/anshgoel/Desktop/AR && uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 --yes
```
