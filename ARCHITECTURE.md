# Architecture Documentation

## System Overview

The PDF to JSON Extractor is a vision-first document analysis pipeline that processes PDF presentations and outputs structured JSON containing facts, metrics, visual explanations, and inferred insights.

## Architecture Diagram

```
┌─────────────┐
│   PDF File  │
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────────────────────┐
│              PDF Processor (pdf_processor.py)           │
│  - Render pages to high-res images                      │
│  - Extract text layer                                   │
└──────┬──────────────────────────────┬──────────────────┘
       │                              │
       v                              v
┌──────────────┐              ┌─────────────┐
│    Images    │              │ Text Layers │
│  (PIL Image) │              │   (strings) │
└──────┬───────┘              └──────┬──────┘
       │                              │
       v                              │
┌──────────────────────┐              │
│  OCR Processor       │              │
│  (ocr_processor.py)  │              │
│  - Extract embedded  │              │
│    text from images  │              │
└──────┬───────────────┘              │
       │                              │
       v                              │
┌──────────────┐                     │
│  OCR Texts   │                     │
└──────┬───────┘                     │
       │                              │
       └──────────────┬───────────────┘
                      │
                      v
       ┌──────────────────────────────────────┐
       │  Vision Extractor (vision_extractor.py)
       │  - GPT-4 Vision analysis
       │  - Per-page structured extraction
       │  - JSON output matching schema
       └──────┬───────────────────────────────┘
              │
              v
       ┌─────────────┐
       │    Pages    │
       │  (List[Page])
       └──────┬──────┘
              │
              v
       ┌──────────────────────────────────┐
       │   Validator (validator.py)       │
       │   - Numbers coverage check       │
       │   - Empty page check             │
       │   - Branding spam detection      │
       │   - Title quality check          │
       └──────┬───────────────────────────┘
              │
              v
       ┌─────────────┐     ┌──────────────┐
       │ Valid Pages │────>│ Retry Logic  │
       └──────┬──────┘     └──────────────┘
              │
              v
       ┌────────────────────────────────────────┐
       │ Summary Generator (summary_generator.py)
       │ - Document-level synthesis
       │ - Key metrics, entities, claims
       └──────┬─────────────────────────────────┘
              │
              v
       ┌─────────────────┐
       │     Document    │
       │  (JSON Output)  │
       └─────────────────┘
```

## Core Components

### 1. Models (`models.py`)

Defines the JSON schema using Pydantic:

- **Document**: Top-level container
- **Page**: Per-page extraction
- **ExtractedNumber**: Structured number with context
- **PageType**: Enum of page categories
- **Language**: Document language detection
- **Confidence**: Per-aspect confidence scores

**Key Features:**
- Strict validation
- Type safety
- JSON serialization
- Field validators

### 2. PDF Processor (`pdf_processor.py`)

**Responsibilities:**
- Render PDF pages to high-resolution images (using `pdf2image`)
- Extract PDF text layer (using `PyPDF2`)
- Handle page limits

**Technologies:**
- `pdf2image` + `poppler`: PDF → PNG conversion
- `PyPDF2`: Text layer extraction

### 3. OCR Processor (`ocr_processor.py`)

**Responsibilities:**
- Extract text from embedded images, charts, screenshots
- Support multi-language (Arabic + English)

**Technologies:**
- `pytesseract` + `tesseract-ocr`
- Configured for `ara+eng` language models

### 4. Vision Extractor (`vision_extractor.py`)

**Core extraction engine using OpenAI GPT-4 Vision.**

**Process:**
1. Convert page image to base64
2. Build structured prompt with:
   - Page image
   - PDF text layer
   - OCR text
   - JSON schema
   - Extraction rules
3. Call GPT-4 Vision API with `response_format=json_object`
4. Parse and validate response into `Page` object

**Key Features:**
- Strict JSON-only output
- Context-aware number extraction
- Visual understanding (charts, diagrams, UI screenshots)
- Confidence scoring

### 5. Validator (`validator.py`)

**Quality Control Checks:**

1. **Numbers Coverage**: Ensures all numbers in evidence are captured
2. **Empty Page**: Detects missing content
3. **Branding Spam**: Identifies repeated decorative text
4. **Title Quality**: Validates title length and format
5. **Duplicate Facts**: Detects redundant information

**Validation Flags:**
- Severity: `warning` or `error`
- Used to trigger retry logic

### 6. Summary Generator (`summary_generator.py`)

**Responsibilities:**
- Synthesize document-level insights from all pages
- Extract key metrics, entities, claims, risks

**Uses LLM (GPT-4) to:**
- Generate one-paragraph summary
- Identify most important metrics across pages
- List key stakeholders and entities
- Summarize main value propositions
- Identify gaps and risks

### 7. Pipeline (`pipeline.py`)

**Main orchestration layer.**

**Process Flow:**
1. PDF Processing (render + text extraction)
2. OCR extraction
3. Per-page vision extraction
4. Validation & retry logic
5. Language detection
6. Document summary generation
7. Final validation
8. JSON output

**Features:**
- Automatic retry with enhanced instructions
- Progress logging
- Error handling
- Configuration management

### 8. CLI (`main.py`)

**Command-line interface for users.**

**Features:**
- Argument parsing
- Configuration validation
- Progress reporting
- Summary display
- Error handling

## Data Flow

```
PDF → [Render] → Images
              → Text Layers

Images → [OCR] → OCR Texts

Images + Text Layers + OCR Texts → [Vision] → Raw Pages

Raw Pages → [Validate] → Flags

Flags → [Retry if needed] → Final Pages

Final Pages → [Summarize] → Document Summary

All Pages + Summary → [Assemble] → Document JSON
```

## Configuration

**Environment Variables** (`.env`):

- `OPENAI_API_KEY`: Required for GPT-4 Vision
- `OPENAI_MODEL`: Default `gpt-4o`
- `PDF_RENDER_SCALE`: Image quality (default 2.5)
- `MAX_PAGES_PER_RUN`: Limit pages (default 20)
- `TESSERACT_LANGUAGES`: OCR languages (default `ara+eng`)
- `RETRY_FLAGGED_PAGES`: Enable retry logic (default `true`)

## Error Handling

**Graceful Degradation:**
- If text layer is empty → rely on OCR
- If OCR fails → rely on vision
- If vision fails → propagate error
- If validation fails → retry with enhanced prompt

**Validation Levels:**
- **Error**: Must fix (blocks output)
- **Warning**: Should review (logged but doesn't block)

## Quality Guarantees

1. **Schema Compliance**: Pydantic enforces structure
2. **Numbers Extraction**: Validator ensures coverage
3. **Non-empty Pages**: Empty page detection
4. **Noise Filtering**: Branding spam detection
5. **Sequential Pages**: Index validation
6. **Retry Logic**: Automatic improvement attempts

## Performance Characteristics

**Bottlenecks:**
- PDF rendering (scales with DPI)
- OCR processing (scales with image size)
- LLM API calls (rate limited, cost per page)

**Optimizations:**
- Batch OCR processing
- Configurable render scale
- Page limits
- Efficient image encoding

**Cost Factors:**
- LLM API calls: 2 calls per document (N pages + 1 summary)
- Retries add extra calls
- Image size affects token cost

## Extensibility

**Easy Extensions:**
- Add new `PageType` enums
- Add new validation rules
- Customize retry logic
- Change LLM model
- Add post-processing

**Future Enhancements (v2+):**
- PPTX direct processing
- Markdown output generation
- Multi-document batch processing
- Custom extraction schemas
- Fine-tuned models for specific domains

## Testing Strategy

1. **Unit Tests**: Each module independently
2. **Integration Tests**: Full pipeline with sample PDFs
3. **Validation Tests**: Schema compliance
4. **Quality Tests**: Extraction accuracy
5. **Performance Tests**: Speed and cost benchmarks

## Dependencies

**Core:**
- `pydantic`: Data modeling and validation
- `openai`: GPT-4 Vision API
- `pdf2image`: PDF rendering
- `PyPDF2`: Text extraction
- `pytesseract`: OCR
- `pillow`: Image processing

**System:**
- `poppler-utils`: PDF rendering backend
- `tesseract-ocr`: OCR engine
- `tesseract-ocr-ara`: Arabic language support

## Security Considerations

1. **API Keys**: Never commit `.env` to git
2. **Input Validation**: PDF file validation
3. **Output Sanitization**: JSON encoding
4. **Rate Limiting**: Respect OpenAI rate limits
5. **Cost Control**: Max pages limit

## Deployment

**Local:**
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with API key
python main.py input.pdf
```

**Docker** (future):
```dockerfile
FROM python:3.11
RUN apt-get update && apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-ara
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## Monitoring & Logging

**Logging Levels:**
- `DEBUG`: Detailed processing info
- `INFO`: Progress updates (default)
- `WARNING`: Validation flags, retries
- `ERROR`: Critical failures

**Metrics to Track:**
- Pages processed per document
- Extraction time per page
- API call count and cost
- Validation flag frequency
- Retry success rate

## Conclusion

This architecture provides a robust, extensible pipeline for extracting structured information from PDF presentations. The vision-first approach with validation and retry logic ensures high-quality output while the modular design allows for easy maintenance and enhancement.
