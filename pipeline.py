"""
Main processing pipeline for PDF to JSON extraction.
"""
import logging
import uuid
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image

from config import Config
from models import Document, Source, Page, Language
from pdf_processor import PDFProcessor
from ocr_processor import OCRProcessor
from vision_extractor import VisionExtractor
from validator import Validator, ValidationFlag
from summary_generator import SummaryGenerator

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """Main pipeline for extracting structured information from PDFs."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize extraction pipeline.
        
        Args:
            config: Configuration object (uses defaults if None)
        """
        self.config = config or Config()
        
        # Initialize components
        self.pdf_processor = PDFProcessor(scale=self.config.PDF_RENDER_SCALE)
        self.ocr_processor = OCRProcessor(languages=self.config.TESSERACT_LANGUAGES)
        self.vision_extractor = VisionExtractor(
            api_key=self.config.OPENAI_API_KEY,
            model=self.config.OPENAI_MODEL
        )
        self.validator = Validator(
            min_title_length=self.config.MIN_TITLE_LENGTH,
            max_brand_repetition=self.config.MAX_BRAND_REPETITION
        )
        self.summary_generator = SummaryGenerator(
            api_key=self.config.OPENAI_API_KEY,
            model=self.config.OPENAI_MODEL
        )
    
    def _detect_language(self, pages: List[Page]) -> Language:
        """
        Detect document language from extracted pages.
        
        Args:
            pages: Extracted pages
        
        Returns:
            Detected language
        """
        # Simple heuristic: check for Arabic characters
        all_text = " ".join([
            p.title + " ".join(p.clean_facts[:3])
            for p in pages[:5]  # Check first 5 pages
        ])
        
        arabic_chars = sum(1 for c in all_text if '\u0600' <= c <= '\u06FF')
        latin_chars = sum(1 for c in all_text if c.isalpha() and ord(c) < 128)
        
        if arabic_chars > latin_chars * 2:
            return Language.ARABIC
        elif latin_chars > arabic_chars * 2:
            return Language.ENGLISH
        else:
            return Language.MIXED
    
    def _process_page(
        self,
        page_index: int,
        image: Image.Image,
        text_layer: str,
        ocr_text: str,
        retry: bool = False
    ) -> Tuple[Page, List[ValidationFlag]]:
        """
        Process a single page with validation.
        
        Args:
            page_index: Page number (1-indexed)
            image: Page image
            text_layer: PDF text layer
            ocr_text: OCR text
            retry: Whether this is a retry attempt
        
        Returns:
            Tuple of (Page object, validation flags)
        """
        # Extract page
        if retry:
            # Higher resolution image for retry
            retry_scale = self.config.PDF_RENDER_SCALE * self.config.RETRY_SCALE_MULTIPLIER
            logger.info(f"Retrying page {page_index} with higher scale: {retry_scale}")
            # Note: In a real retry, we'd re-render the image at higher scale
            # For now, we'll use the existing image but pass a retry instruction
        
        page = self.vision_extractor.extract_page(
            page_index=page_index,
            image=image,
            text_layer=text_layer,
            ocr_text=ocr_text
        )
        
        # Validate page
        flags = self.validator.validate_page(page, text_layer, ocr_text)
        
        if flags:
            logger.warning(f"Page {page_index} validation flags:")
            for flag in flags:
                logger.warning(f"  {flag}")
        
        return page, flags
    
    def _retry_page_if_needed(
        self,
        page: Page,
        flags: List[ValidationFlag],
        image: Image.Image,
        text_layer: str,
        ocr_text: str
    ) -> Page:
        """
        Retry page extraction if validation flags warrant it.
        
        Args:
            page: Original page object
            flags: Validation flags
            image: Page image
            text_layer: PDF text layer
            ocr_text: OCR text
        
        Returns:
            Page object (original or retried)
        """
        if not self.config.RETRY_FLAGGED_PAGES:
            return page
        
        if self.validator.should_retry_page(flags):
            logger.info(f"Retrying page {page.page_index} due to validation flags")
            
            # Get retry instruction
            retry_instruction = self.validator.get_retry_instruction(flags)
            
            # Retry extraction
            try:
                retried_page = self.vision_extractor.extract_page_with_retry(
                    page_index=page.page_index,
                    image=image,
                    text_layer=text_layer,
                    ocr_text=ocr_text,
                    retry_instruction=retry_instruction
                )
                
                # Validate retry
                retry_flags = self.validator.validate_page(retried_page, text_layer, ocr_text)
                
                if len(retry_flags) < len(flags):
                    logger.info(f"Retry improved page {page.page_index}: {len(flags)} -> {len(retry_flags)} flags")
                    return retried_page
                else:
                    logger.info(f"Retry did not improve page {page.page_index}, using original")
                    return page
            
            except Exception as e:
                logger.error(f"Retry failed for page {page.page_index}: {e}")
                return page
        
        return page
    
    def process_pdf(
        self,
        pdf_path: Path,
        max_pages: Optional[int] = None
    ) -> Document:
        """
        Process a PDF and extract structured information.
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process (uses config default if None)
        
        Returns:
            Document object with all extracted information
        """
        logger.info(f"Starting PDF extraction: {pdf_path}")
        
        # Use config default if not specified
        if max_pages is None:
            max_pages = self.config.MAX_PAGES_PER_RUN
        
        # Step 1: Process PDF (render + extract text)
        logger.info("Step 1: Rendering PDF and extracting text layer")
        images, text_layers, page_count = self.pdf_processor.process_pdf(pdf_path, max_pages)
        
        # Step 2: Run OCR
        logger.info("Step 2: Running OCR on pages")
        ocr_texts = self.ocr_processor.extract_text_batch(images)
        
        # Step 3: Extract each page with vision
        logger.info("Step 3: Extracting structured information from each page")
        pages = []
        
        for i in range(page_count):
            page_index = i + 1
            logger.info(f"Processing page {page_index}/{page_count}")
            
            # Extract page
            page, flags = self._process_page(
                page_index=page_index,
                image=images[i],
                text_layer=text_layers[i],
                ocr_text=ocr_texts[i]
            )
            
            # Retry if needed
            page = self._retry_page_if_needed(
                page=page,
                flags=flags,
                image=images[i],
                text_layer=text_layers[i],
                ocr_text=ocr_texts[i]
            )
            
            pages.append(page)
        
        # Step 4: Detect language
        logger.info("Step 4: Detecting document language")
        language = self._detect_language(pages)
        logger.info(f"Detected language: {language.value}")
        
        # Step 5: Generate document summary
        logger.info("Step 5: Generating document summary")
        summary = self.summary_generator.generate_summary(pages)
        
        # Step 6: Create document object
        logger.info("Step 6: Creating final document object")
        document = Document(
            schema_version="1.0",
            document_id=str(uuid.uuid4()),
            source=Source(
                filename=pdf_path.name,
                file_type="pdf"
            ),
            language=language,
            page_count=page_count,
            pages=pages,
            document_summary=summary
        )
        
        # Step 7: Validate document
        logger.info("Step 7: Validating document structure")
        doc_flags = self.validator.validate_document(document)
        
        if doc_flags:
            logger.warning("Document validation flags:")
            for flag in doc_flags:
                logger.warning(f"  {flag}")
            
            # Check for errors
            errors = [f for f in doc_flags if f.severity == "error"]
            if errors:
                raise ValueError(f"Document validation failed with {len(errors)} errors")
        
        logger.info(f"Successfully extracted {page_count} pages from {pdf_path}")
        return document
    
    def process_and_save(
        self,
        pdf_path: Path,
        output_path: Path,
        max_pages: Optional[int] = None
    ) -> Document:
        """
        Process PDF and save to JSON file.
        
        Args:
            pdf_path: Path to PDF file
            output_path: Path to output JSON file
            max_pages: Maximum pages to process
        
        Returns:
            Document object
        """
        # Process PDF
        document = self.process_pdf(pdf_path, max_pages)
        
        # Save to JSON
        logger.info(f"Saving results to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(document.model_dump_json(indent=2, exclude_none=True))
        
        logger.info(f"Successfully saved JSON to {output_path}")
        return document
