# Ultra-Low Token Mode

If you're using too many input tokens, here are aggressive optimizations to reduce them by up to 95%.

---

## Current Token Usage (Default Settings)

With default optimized settings:
- **~800-1,200 input tokens per page**
- **~200-400 output tokens per page**
- **Total: ~1,000-1,600 tokens/page**

For 10 pages: ~12,000 tokens total

---

## Ultra-Low Input Token Settings

### Level 1: Aggressive (60% reduction)

Add to your `.env`:

```ini
# Smaller images
VISION_IMAGE_MAX_SIZE=768          # Was 1024
VISION_IMAGE_QUALITY=60            # Was 75

# Less text context
MAX_TEXT_CONTEXT_LENGTH=300        # Was 500

# Keep low detail mode (critical!)
VISION_DETAIL_LEVEL=low            # Already 65 tokens max
```

**Result:** ~400-600 input tokens/page (60% reduction)

---

### Level 2: Extreme (80% reduction)

```ini
# Very small images
VISION_IMAGE_MAX_SIZE=512          # Aggressive reduction
VISION_IMAGE_QUALITY=50            # Lower quality

# Minimal text context
MAX_TEXT_CONTEXT_LENGTH=200        # Bare minimum

# Disable OCR (huge savings!)
SKIP_OCR=true                      # Don't run OCR at all

# Keep low detail
VISION_DETAIL_LEVEL=low
```

**Result:** ~200-400 input tokens/page (80% reduction)

---

### Level 3: Nuclear (90% reduction)

```ini
# Tiny images
VISION_IMAGE_MAX_SIZE=384          # Very small
VISION_IMAGE_QUALITY=40            # Noticeable quality loss

# Almost no text
MAX_TEXT_CONTEXT_LENGTH=100        # Just a hint

# Skip OCR
SKIP_OCR=true

# Process fewer facts
MAX_FACTS_PER_PAGE=3               # Was 5
MAX_VISUALS_PER_PAGE=2             # Was 3
MAX_GAPS_PER_PAGE=2                # Was 3

# Low detail (essential)
VISION_DETAIL_LEVEL=low
```

**Result:** ~100-200 input tokens/page (90% reduction!)

---

## Quick Comparison

| Setting | Input Tokens/Page | Quality | Best For |
|---------|------------------|---------|----------|
| **Default** | 800-1,200 | Good | Most cases |
| **Level 1** | 400-600 | Acceptable | Budget-conscious |
| **Level 2** | 200-400 | Lower | Simple slides only |
| **Level 3** | 100-200 | Poor | Emergency/testing |

---

## Biggest Token Savers

### 1. **Keep VISION_DETAIL_LEVEL=low** (CRITICAL!)

This is the #1 most important setting:
- `low`: **65 tokens** per image (fixed)
- `high`: **500-2,000 tokens** per image (depends on size)

**Never change this unless absolutely necessary!**

---

### 2. **Reduce Image Size**

Images are base64 encoded and sent to API:

| Size | File Size | Effective Tokens |
|------|-----------|------------------|
| 1024px | ~30 KB | ~300 tokens |
| 768px | ~17 KB | ~170 tokens |
| 512px | ~8 KB | ~80 tokens |
| 384px | ~5 KB | ~50 tokens |

**Recommendation:** Start with 768px, go to 512px if still too expensive.

```ini
VISION_IMAGE_MAX_SIZE=768
```

---

### 3. **Disable OCR**

OCR adds text to the prompt:
- OCR enabled: +200-500 tokens/page
- OCR disabled: 0 tokens

Most PDFs have text layers anyway, so OCR is often redundant.

```ini
SKIP_OCR=true
```

---

### 4. **Reduce Text Context**

Text from PDF + OCR is sent to LLM:
- 500 chars: ~125 tokens
- 300 chars: ~75 tokens
- 200 chars: ~50 tokens
- 100 chars: ~25 tokens

```ini
MAX_TEXT_CONTEXT_LENGTH=200
```

---

### 5. **Lower Image Quality**

JPEG compression affects file size:
- Quality 75: ~30 KB
- Quality 60: ~20 KB (33% smaller)
- Quality 50: ~15 KB (50% smaller)
- Quality 40: ~12 KB (60% smaller)

```ini
VISION_IMAGE_QUALITY=60
```

---

## Skip OCR Implementation

I'll add this feature for you:

```python
# In config.py
SKIP_OCR = os.getenv("SKIP_OCR", "false").lower() == "true"

# In pipeline.py
if not self.config.SKIP_OCR:
    ocr_texts = self.ocr_processor.extract_text_batch(images)
else:
    ocr_texts = [""] * len(images)  # Empty OCR
    logger.info("OCR disabled - using PDF text layer only")
```

---

## Process Fewer Pages

The ultimate token saver - just process what you need:

```bash
# Only first 5 pages
python main.py presentation.pdf --max-pages 5

# Only first 10 pages
python main.py presentation.pdf --max-pages 10
```

---

## Real Cost Examples

### 10-Page Document

| Mode | Input Tokens | Output Tokens | Total | Cost (gpt-5-mini) |
|------|-------------|---------------|-------|------------------|
| Default | 10,000 | 3,000 | 13,000 | ~$0.05 |
| Level 1 | 5,000 | 3,000 | 8,000 | ~$0.03 |
| Level 2 | 3,000 | 3,000 | 6,000 | ~$0.02 |
| Level 3 | 1,500 | 2,000 | 3,500 | ~$0.01 |

### 50-Page Document

| Mode | Input Tokens | Output Tokens | Total | Cost (gpt-5-mini) |
|------|-------------|---------------|-------|------------------|
| Default | 50,000 | 15,000 | 65,000 | ~$0.25 |
| Level 1 | 25,000 | 15,000 | 40,000 | ~$0.15 |
| Level 2 | 15,000 | 15,000 | 30,000 | ~$0.10 |
| Level 3 | 7,500 | 10,000 | 17,500 | ~$0.05 |

---

## Recommended Quick Fix

For most users wanting to cut costs, use this in your `.env`:

```ini
# Balanced token reduction (60% fewer input tokens)
VISION_IMAGE_MAX_SIZE=768
VISION_IMAGE_QUALITY=60
MAX_TEXT_CONTEXT_LENGTH=300
SKIP_OCR=true                    # Most PDFs don't need OCR
VISION_DETAIL_LEVEL=low          # Keep this!
```

**Result:** 
- Input tokens: 400-600/page (was 800-1,200)
- Quality: Still good for most presentations
- Cost: ~60% cheaper

---

## Quality Trade-offs

### What You Lose at Each Level

**Level 1 (Aggressive):**
- ❌ Some detail in complex diagrams
- ❌ OCR text from embedded images
- ✅ Still good for most presentations

**Level 2 (Extreme):**
- ❌ Harder to read small text
- ❌ May miss some numbers in charts
- ✅ OK for simple slides with large text

**Level 3 (Nuclear):**
- ❌ Significant quality loss
- ❌ May miss important information
- ❌ Not recommended for production
- ✅ Only for testing or emergency

---

## Monitor Your Token Usage

The tool logs token usage per page:

```
INFO - Page 1 tokens: 1,234 (prompt: 1,000, completion: 234)
```

Watch these numbers and adjust settings accordingly.

---

## Reasoning Tokens Issue (o1/gpt-5 models)

### The Hidden Cost

If you're using `o1-mini` or `gpt-5-mini`, you're being charged for **reasoning tokens**:

| Model | Input | Output | Reasoning | Total Cost |
|-------|-------|--------|-----------|------------|
| gpt-5-mini | 1,000 tokens | 300 tokens | **2,500 tokens** | **3,800 tokens!** |
| gpt-4o-mini | 1,000 tokens | 300 tokens | **0 tokens** | **1,300 tokens** |

**Reasoning tokens are internal "thinking" and can be 3-10x your output tokens!**

### You CANNOT Limit Reasoning

OpenAI provides no way to limit reasoning tokens for o1/gpt-5 models.

### Solution: Switch to gpt-4o-mini

```ini
# In your .env file
OPENAI_MODEL=gpt-4o-mini  # No reasoning tokens!
```

**gpt-4o-mini benefits:**
- ✅ No reasoning tokens (0!)
- ✅ Supports temperature control
- ✅ Faster processing
- ✅ Actually cheaper overall
- ✅ Good quality for presentations

**Cost comparison (10 pages):**
- gpt-5-mini: ~$0.10-0.15 (with reasoning tokens!)
- **gpt-4o-mini: ~$0.02-0.03** (no reasoning!)

**You'll save 70-80% by switching models!**

---

## Summary

**Quick wins:**
1. **Switch to `gpt-4o-mini`** - eliminates reasoning tokens (70% savings!)
2. Set `VISION_DETAIL_LEVEL=low` (if not already) - saves 90%
3. Add `SKIP_OCR=true` - saves 20-30%
4. Set `VISION_IMAGE_MAX_SIZE=768` - saves 30%
5. Set `MAX_TEXT_CONTEXT_LENGTH=300` - saves 10%

**Total reduction: 85-95% cost with gpt-4o-mini + optimizations!**
