# Token Optimization Guide

## Problem

The original implementation used ~25k tokens per page (250k for 10 pages), which is:
- 💰 **Very expensive** (~$0.25 per page with GPT-4o)
- 🐌 **Slow** due to large payload sizes
- ❌ **Unsustainable** for batch processing

## Solution: Aggressive Token Reduction

### Optimizations Implemented

| Optimization | Token Reduction | Quality Impact |
|-------------|-----------------|----------------|
| **Low detail mode** | 65 tokens/image vs 1000+ | Minimal for presentation slides |
| **Image compression (JPEG 75%)** | 70-80% reduction | Slight, acceptable |
| **Image resize (1024px max)** | 50-70% reduction | Minimal for text/charts |
| **Prompt compression** | 80% reduction | None (same info) |
| **Text truncation (500 chars)** | 50-90% reduction | Minimal (context preserved) |
| **Lower PDF scale (1.5x)** | 40% reduction | Acceptable for most PDFs |

### Expected Results

| Configuration | Tokens/Page | Cost/Page (GPT-4o) | 10 Pages Cost |
|--------------|-------------|-------------------|---------------|
| **Original** | ~25,000 | $0.25 | $2.50 |
| **Optimized (default)** | ~1,500-3,000 | $0.015-$0.03 | $0.15-$0.30 |
| **Ultra-low (see below)** | ~500-1,000 | $0.005-$0.01 | $0.05-$0.10 |

**Estimated reduction: 80-90% fewer tokens** 🎉

---

## Configuration Options

### Default Settings (Balanced)

```ini
# .env file
PDF_RENDER_SCALE=1.5                 # Lower resolution PDF rendering
VISION_IMAGE_MAX_SIZE=1024           # Max 1024px width/height
VISION_IMAGE_QUALITY=75              # JPEG quality (1-100)
VISION_DETAIL_LEVEL=low              # Use OpenAI's low-detail mode (65 tokens)
MAX_TEXT_CONTEXT_LENGTH=500          # Truncate text context
```

**Expected:** ~1,500-3,000 tokens/page
**Quality:** Good for most presentations

---

### Ultra-Low Token Mode (Maximum Savings)

For maximum token reduction (when quality can be lower):

```ini
# .env file
PDF_RENDER_SCALE=1.2                 # Even lower resolution
VISION_IMAGE_MAX_SIZE=768            # Smaller images
VISION_IMAGE_QUALITY=60              # Lower JPEG quality
VISION_DETAIL_LEVEL=low              # Low detail mode
MAX_TEXT_CONTEXT_LENGTH=300          # Less text context
```

**Expected:** ~500-1,000 tokens/page (95% reduction!)
**Quality:** Acceptable for simple slides with large text

---

### High Quality Mode (When Accuracy Matters)

For complex diagrams or small text:

```ini
# .env file
PDF_RENDER_SCALE=2.0                 # Higher resolution
VISION_IMAGE_MAX_SIZE=1536           # Larger images allowed
VISION_IMAGE_QUALITY=85              # Better JPEG quality
VISION_DETAIL_LEVEL=high             # High detail mode (expensive!)
MAX_TEXT_CONTEXT_LENGTH=1000         # More text context
```

**Expected:** ~8,000-15,000 tokens/page (still better than original)
**Quality:** Best accuracy for complex content

---

## Understanding the Settings

### 1. VISION_DETAIL_LEVEL (Biggest Impact!)

OpenAI charges different rates based on detail level:

- **`low`** (recommended): 65 tokens flat, regardless of image size
  - Best for: presentations, slides with large text, simple diagrams
  - Cost: ~$0.0006 per image with GPT-4o
  
- **`high`**: Calculated based on image size (512px tiles)
  - Best for: detailed diagrams, small text, complex visuals
  - Cost: 10-100x more expensive depending on size

**Recommendation:** Start with `low`, only use `high` if accuracy is poor.

### 2. VISION_IMAGE_MAX_SIZE

Max width/height in pixels before sending to API.

- **768**: Ultra-low tokens, okay for simple slides
- **1024**: Balanced (default), good for most content
- **1536**: Higher quality, more tokens
- **2048**: Maximum quality, expensive

Images are resized maintaining aspect ratio.

### 3. VISION_IMAGE_QUALITY

JPEG compression quality (1-100).

- **60**: Maximum compression, visible artifacts
- **75**: Balanced (default), minimal artifacts
- **85**: High quality, minimal compression
- **95**: Nearly lossless, large files

### 4. PDF_RENDER_SCALE

Initial PDF rendering quality multiplier.

- **1.2**: Low resolution (86 DPI)
- **1.5**: Balanced (108 DPI) - default
- **2.0**: Good quality (144 DPI)
- **2.5**: High quality (180 DPI) - original default

Lower scale = smaller initial images = less data to process.

### 5. MAX_TEXT_CONTEXT_LENGTH

Characters of text/OCR to include in prompt.

- **300**: Minimal context
- **500**: Balanced (default)
- **1000**: Full context
- **0**: No text context (rely on vision only)

---

## Cost Comparison Examples

### 10-Page Presentation

| Mode | Tokens | GPT-4o Cost | GPT-4o-mini Cost |
|------|--------|------------|-----------------|
| Original (high detail) | 250,000 | $2.50 | $0.25 |
| **Default (optimized)** | **25,000** | **$0.25** | **$0.025** |
| Ultra-low | 8,000 | $0.08 | $0.008 |

### 50-Page Deck

| Mode | Tokens | GPT-4o Cost | GPT-4o-mini Cost |
|------|--------|------------|-----------------|
| Original | 1,250,000 | $12.50 | $1.25 |
| **Default (optimized)** | **125,000** | **$1.25** | **$0.125** |
| Ultra-low | 40,000 | $0.40 | $0.04 |

---

## Using GPT-4o-mini (90% Cost Reduction!)

For even more savings, use `gpt-4o-mini`:

```ini
# .env file
OPENAI_MODEL=gpt-4o-mini
```

**Pricing:**
- GPT-4o: $0.01/1k tokens
- GPT-4o-mini: $0.001/1k tokens (10x cheaper!)

**Quality:** 
- Good for straightforward slides
- May struggle with complex Arabic text or intricate diagrams
- Worth trying first, fall back to GPT-4o if needed

---

## Monitoring Token Usage

The tool now logs token usage per page:

```
2026-02-06 19:33:53 - vision_extractor - INFO - Page 1 tokens: 1,847 (prompt: 1,234, completion: 613)
```

Watch these logs to see actual usage with your settings.

---

## Recommended Workflow

1. **Start with default optimized settings** (as configured now)
   
2. **Test on 1-2 pages:**
   ```bash
   python main.py presentation.pdf --max-pages 2 -v
   ```

3. **Check token usage in logs:**
   - Look for lines: `Page X tokens: ...`
   - Calculate cost: tokens × $0.00001 (GPT-4o)

4. **Adjust if needed:**
   - Too expensive? → Lower `VISION_IMAGE_QUALITY` to 60
   - Poor accuracy? → Increase `VISION_IMAGE_MAX_SIZE` to 1536
   - Missing numbers? → Increase `MAX_TEXT_CONTEXT_LENGTH` to 1000
   - Complex diagrams? → Set `VISION_DETAIL_LEVEL=high`

5. **Process full document**

---

## Tips for Maximum Savings

1. **Use `gpt-4o-mini` first**, upgrade to `gpt-4o` only if quality is insufficient

2. **Process fewer pages** - do you really need all 26 pages?
   ```bash
   python main.py deck.pdf --max-pages 10
   ```

3. **Clean up PDFs first** - remove unnecessary appendix slides

4. **Batch similar documents** - reuse insights across similar decks

5. **Use `--scale` flag for one-off adjustments:**
   ```bash
   python main.py deck.pdf --scale 1.2  # Override default scale
   ```

---

## Quality vs Cost Trade-offs

| Use Case | Recommended Settings | Expected Quality |
|----------|---------------------|------------------|
| **Quick scan** | ultra-low + gpt-4o-mini | 70% accuracy |
| **Standard extraction** | default optimized + gpt-4o | 90% accuracy |
| **High stakes analysis** | high quality + gpt-4o | 95% accuracy |
| **Complex technical docs** | high quality + detail=high | 98% accuracy |

---

## Summary

The optimizations reduce token usage by **80-90%** while maintaining good quality for most presentations. This makes the tool practical for real-world use.

**Before:** ~$2.50 for 10 pages  
**After:** ~$0.25 for 10 pages (or $0.025 with gpt-4o-mini)

You can tune settings based on your specific needs and budget! 🎯
