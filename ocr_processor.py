"""
OCR processing for extracting text from images.
"""
import logging
import os
from pathlib import Path
from typing import Optional
from PIL import Image
import pytesseract
from typing import List

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Handles OCR text extraction from images."""
    
    def __init__(self, languages: str = "ara+eng", tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR processor.
        
        Args:
            languages: Tesseract language codes (e.g., 'ara+eng' for Arabic+English)
            tesseract_cmd: Path to tesseract executable (Windows)
        """
        self.languages = languages
        
        # Set custom tesseract path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif os.name == 'nt':
            # Auto-detect on Windows
            found_path = self._find_tesseract_windows()
            if found_path:
                pytesseract.pytesseract.tesseract_cmd = found_path
    
    def _find_tesseract_windows(self) -> Optional[str]:
        """
        Try to find tesseract installation on Windows.
        
        Returns:
            Path to tesseract.exe or None
        """
        common_paths = [
            Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
            Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
            Path.home() / "AppData/Local/Programs/Tesseract-OCR/tesseract.exe"
        ]
        
        for path in common_paths:
            if path.exists():
                logger.info(f"Found tesseract at: {path}")
                return str(path)
        
        return None
    
    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image: PIL Image
        
        Returns:
            Extracted text string
        """
        try:
            # Run Tesseract OCR
            text = pytesseract.image_to_string(
                image,
                lang=self.languages,
                config='--psm 6'  # Assume uniform block of text
            )
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return ""
    
    def extract_text_batch(self, images: List[Image.Image]) -> List[str]:
        """
        Extract text from multiple images.
        
        Args:
            images: List of PIL Images
        
        Returns:
            List of extracted text strings
        """
        logger.info(f"Running OCR on {len(images)} images")
        
        ocr_texts = []
        for i, image in enumerate(images, start=1):
            logger.debug(f"OCR processing page {i}/{len(images)}")
            text = self.extract_text(image)
            ocr_texts.append(text)
            logger.debug(f"Page {i}: extracted {len(text)} chars via OCR")
        
        logger.info(f"OCR completed for {len(images)} pages")
        return ocr_texts
