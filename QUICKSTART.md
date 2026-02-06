# 🚀 Quick Command Reference

## TL;DR - Simple Usage

```bash
cd /Users/anshgoel/Desktop/AR

# Just run it - NVIDIA LLM is automatically used if API key is configured
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 --yes

# When prompted for style, just press Enter or type your preferences:
# Examples: "50 slides" or "brief presentation" or "detailed methodology"
```

**That's it!** The system automatically:
- Uses **NVIDIA DeepSeek-V3.2 with MULTIMODAL support** (analyzes figures, tables, images)
- Falls back to Gemini (text-only) or rule-based mode if needed
- Determines optimal slide count (5-100)
- Generates smart summaries instead of copy-paste

---

## Setup (One-Time) - NVIDIA API

### 🎯 PRIMARY: NVIDIA DeepSeek-V3.2 (MULTIMODAL - Recommended)

**Why NVIDIA?**
✨ **Analyzes figures and tables** - Not just text!
✨ Generates insights FROM your charts/plots
✨ More powerful model (DeepSeek-V3.2)
✨ Better presentation quality

**Setup Steps:**

1. **Get NVIDIA API Key**: https://build.nvidia.com/
   - Sign in to NVIDIA Build
   - Click "Get API Key"
   - Copy your key

2. **Create `.env` file** in project root:
   ```bash
   LLM_PROVIDER=nvidia
   NVIDIA_API_KEY=your_nvidia_api_key_here
   NVIDIA_MODEL=nvidia/deepseek-ai/deepseek-v3.2
   NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
   ```

3. **Done!** NVIDIA multimodal LLM is now your PRIMARY brain

---

### Fallback: Gemini API (Text-Only)

If you prefer Gemini or NVIDIA isn't available:

1. **Get API Key**: https://ai.google.dev/
2. **Configure `.env`**:
   ```bash
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-exp
   ```

**Note:** Gemini doesn't support multimodal figure analysis.

---

## How It Works

### 🧠 NVIDIA Mode (PRIMARY - Multimodal)
- **Content**: Smart summarization with **figure/table analysis**
- **Multimodal**: LLM **sees and analyzes your figures**
- **Slide Count**: Dynamically determined (5-100) based on content density
- **Quality**: Excellent - integrates visual insights
- **Speed**: ~40-80s (API calls + image encoding)
- **Cost**: ~$0.02-0.20 per paper

### 📝 Gemini Mode (FALLBACK - Text-Only)
- **Content**: Smart text summarization
- **Multimodal**: No (text-only)
- **Slide Count**: Dynamically determined (5-100)
- **Quality**: Good - text insights only
- **Speed**: ~30-60s
- **Cost**: ~$0.01-0.15 per paper

### ⚙️ Rule-Based Mode (FALLBACK - No LLM)
- **Content**: Direct text extraction with formatting rules
- **Multimodal**: No
- **Slide Count**: Fixed (~20) or user-specified
- **Quality**: Basic structure
- **Speed**: Fast (~5s)
- **Cost**: Free

**System automatically chooses best mode available!**

---

## Multimodal Features (NVIDIA Only)

### What NVIDIA Can Do:

**1. Figure Analysis** - LLM sees your charts/plots and generates insights:
```
Example: Instead of generic text bullets, you get:
✓ "Accuracy peaks at 94.3% with Model-B (blue line), outperforming baseline by 12%"
✓ "Training converges after epoch 15, showing stable performance"
```

**2. Table Understanding** - Analyzes table structure and values

**3. Visual Insights** - Identifies trends, comparisons, anomalies in images

**Automatic:** No special commands needed. When a section has figures, NVIDIA analyzes them!

---

## Example Commands

### Let NVIDIA decide everything (RECOMMENDED)
```bash
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 --yes
# Press Enter when prompted
# NVIDIA will analyze all figures and generate smart content
```

### Detailed presentation with figure analysis
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
| ✅ NVIDIA API key configured | NVIDIA multimodal is PRIMARY brain |
| ✅ Gemini API key configured | Gemini (text-only) is PRIMARY brain |
| ❌ No API key | Rule-based fallback (still works!) |
| ⚠️ API limit exceeded | Automatic fallback to rules per section |
| 🖼️ Figures in paper | NVIDIA analyzes them multimodally |

---

## What Gets Generated

- `output.tex` (or your custom name)
- Professional Beamer LaTeX presentation
- **Bullet points with image insights** (NVIDIA mode)
- Ready to compile: `pdflatex output.tex`
- `report.json` with generation stats

---

## The Pipeline (NVIDIA Multimodal)

```
Your Paper (.tex)
    ↓
Parse Structure (tex_parser.py)
    ↓
┌────────────────────────────────┐
│ NVIDIA MODE (PRIMARY)          │
│ ✓ Analyze content density      │
│ ✓ Determine slide count        │ ← Intelligent
│ ✓ 🖼️  ANALYZE FIGURES (NEW!)   │   decision-making
│ ✓ 📊 ANALYZE TABLES (NEW!)     │   + multimodal
│ ✓ Generate smart bullets       │   vision
│ ✓ Extract key insights         │
└────────────────────────────────┘
    ↓ (fallback if fails)
┌────────────────────────────────┐
│ GEMINI/RULE MODE (BACKUP)     │
│ • Apply 3 Laws                 │ ← Text-only
│ • Apply 8 Protocols            │   fallback
│ • Format text content          │
└────────────────────────────────┘
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

### "NVIDIA mode not activating"
1. Check `.env` file exists with `NVIDIA_API_KEY=...`
2. Verify API key:
   ```bash
   uv run python -c "from src.agent.config import load_settings; print(load_settings().nvidia_api_key)"
   ```
3. Check logs - should see "🧠 LLM enabled with NVIDIA model: nvidia/deepseek-ai/deepseek-v3.2"

### "Multimodal not working (no figure analysis)"
- Verify you're using NVIDIA (not Gemini)
- Check logs for "MULTIMODAL: If figure exists, use image-aware generation"
- Ensure figures have valid paths in your LaTeX

### "Read operation timed out" or "Too Many Requests (429)"

**Don't worry!** The system automatically handles these errors:

✅ **Timeout errors:**
- 5-minute timeout for DeepSeek thinking
- Automatic retry with 10s delay

✅ **Rate limiting (429):**
- Exponential backoff: 5s, 10s, 20s, 40s, 80s
- Up to 5 retry attempts

✅ **Connection errors:**
- Auto-retry with 10s delay
- Handles network hiccups

✅ **Polite delays:**
- 2s delay between requests
- Prevents hitting rate limits

**You'll see logs like:**
```
⚠️  Rate limit hit (429). Waiting 10.0s before retry...
⚠️  Timeout error. Retrying in 10.0s...
```

**This is normal!** The system recovers automatically.

See `ERROR_HANDLING.md` for details.

### "API rate limit exceeded"
System automatically falls back to rule-based mode per section. Your presentation will still be generated!

---

## Advanced: Switch Between Providers

**Use NVIDIA:**
```bash
# In .env:
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=your_key
```

**Use Gemini:**
```bash
# In .env:
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key
```

**Use rule-based only:**
```bash
# Remove .env or leave API keys empty
```

---

## Quick Start Command (Copy-Paste):
```bash
cd /Users/anshgoel/Desktop/AR && uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 --yes
```

**🎯 With NVIDIA multimodal, your slides will include insights FROM your figures, not just text bullets!**
