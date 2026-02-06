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

## Configuration

Create a `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

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
