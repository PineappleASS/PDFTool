# PDF to Structured JSON Extractor

A tool that extracts structured information from PDF presentations and outputs clean JSON with facts, visual meanings, metrics, and inferred insights.

## Features

- **PDF-first processing**: Converts PPTX to PDF, then processes
- **Vision + Text extraction**: Uses page images, PDF text layer, and OCR
- **Structured JSON output**: Clean, validated schema with per-page analysis
- **Quality control**: Automatic validation and re-processing of flagged pages
- **Multi-language support**: Handles Arabic, English, and mixed content

## Installation

```bash
pip install -r requirements.txt
```

### System Dependencies

**For PDF rendering:**
- `poppler-utils` (Linux/Mac) or `poppler` (Windows)

**For OCR:**
- `tesseract-ocr`
- `tesseract-ocr-ara` (for Arabic support)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-ara
```

**macOS:**
```bash
brew install poppler tesseract tesseract-lang
```

**Windows:**

1. **Install Poppler:**
   - Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
   - Extract to `C:\Program Files\poppler`
   - Add `C:\Program Files\poppler\Library\bin` to PATH, OR
   - Use the automatic installer: `python install_windows_deps.py`

2. **Install Tesseract:**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install with default options
   - Add Tesseract to PATH or set `TESSERACT_CMD` in `.env`
   - Download Arabic language data during installation

## Configuration

Create a `.env` file with your OpenAI API key:

```ini
OPENAI_API_KEY=your_api_key_here

# Optional: Token optimization (see TOKEN_OPTIMIZATION.md)
VISION_DETAIL_LEVEL=low          # Use 'low' for 80-90% cost reduction
VISION_IMAGE_MAX_SIZE=1024       # Max image size in pixels
VISION_IMAGE_QUALITY=75          # JPEG quality (1-100)
MAX_TEXT_CONTEXT_LENGTH=500      # Truncate text context
```

**Cost Optimization:** The tool now uses ~1,500-3,000 tokens per page (vs 25,000 originally).
See `TOKEN_OPTIMIZATION.md` for detailed cost/quality trade-offs.

## Usage

```bash
python main.py input.pdf -o output.json
```

### Options

- `-o, --output`: Output JSON file path (default: output.json)
- `--scale`: PDF render scale factor (default: 2.5)
- `--max-pages`: Maximum pages to process (default: 20)

## Output Schema

The tool produces JSON with:

- **Document-level metadata**: filename, language, page count
- **Per-page extraction**: facts, visuals, inferred message, metrics, gaps
- **Document summary**: key metrics, entities, claims, risks

See the specification for detailed schema.

## Examples

Process a single PDF:
```bash
python main.py presentation.pdf
```

Process with custom output:
```bash
python main.py deck.pdf -o results/analysis.json
```

## Architecture

1. **Ingest**: Accept PDF (or PPTX → PDF conversion)
2. **Render**: Convert pages to high-res images
3. **Text extraction**: Extract PDF text layer
4. **OCR**: Extract text from images/charts
5. **Vision extraction**: LLM-based per-page analysis
6. **Validation**: Quality checks and retry logic
7. **Summary**: Document-level synthesis
8. **Output**: Single JSON file

## License

MIT
