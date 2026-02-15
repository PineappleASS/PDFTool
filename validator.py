"""
Validation and quality control for extracted pages.
"""
import logging
import re
from typing import List, Set, Dict, Any
from models import Page, Document

logger = logging.getLogger(__name__)


class ValidationFlag:
    """Represents a validation issue."""
    
    def __init__(self, page_index: int, flag_type: str, message: str, severity: str = "warning"):
        self.page_index = page_index
        self.flag_type = flag_type
        self.message = message
        self.severity = severity  # "warning" or "error"
    
    def __repr__(self):
        return f"[{self.severity.upper()}] Page {self.page_index} - {self.flag_type}: {self.message}"


class Validator:
    """Validates extracted pages and performs quality checks."""
    
    def __init__(
        self,
        min_title_length: int = 3,
        max_brand_repetition: int = 5
    ):
        """
        Initialize validator.
        
        Args:
            min_title_length: Minimum acceptable title length
            max_brand_repetition: Maximum allowed repetitions of short tokens
        """
        self.min_title_length = min_title_length
        self.max_brand_repetition = max_brand_repetition
    
    def _extract_numbers_from_text(self, text: str) -> Set[str]:
        """
        Extract numeric tokens from text.
        
        Args:
            text: Text to search
        
        Returns:
            Set of number strings found
        """
        # Pattern matches numbers with optional units, percentages, currency
        # Examples: 60%, 1000, 5.2, 2023, Q1, 50 SAR
        pattern = r'\d+(?:\.\d+)?%?'
        numbers = set(re.findall(pattern, text))
        return numbers
    
    def check_numbers_coverage(
        self,
        page: Page,
        text_layer: str,
        ocr_text: str
    ) -> List[ValidationFlag]:
        """
        Check if all numbers in evidence are captured in extracted_numbers.
        
        Args:
            page: Extracted page object
            text_layer: PDF text layer
            ocr_text: OCR text
        
        Returns:
            List of validation flags
        """
        flags = []
        
        # Collect all numbers from evidence
        evidence_numbers = set()
        if text_layer:
            evidence_numbers.update(self._extract_numbers_from_text(text_layer))
        if ocr_text:
            evidence_numbers.update(self._extract_numbers_from_text(ocr_text))
        
        # Collect extracted numbers
        extracted_raws = {num.raw for num in page.extracted_numbers}
        
        # Find missing numbers (in evidence but not extracted)
        missing_numbers = evidence_numbers - extracted_raws
        
        # Filter out very common numbers that might be page numbers or noise
        # (numbers < 100 are often noise unless they have context)
        significant_missing = [
            num for num in missing_numbers
            if '%' in num or float(re.sub(r'[^\d.]', '', num)) >= 100
        ]
        
        if significant_missing and len(significant_missing) > 2:
            flags.append(ValidationFlag(
                page.page_index,
                "numbers_coverage",
                f"Found {len(significant_missing)} significant numbers in text but not in extracted_numbers: {', '.join(list(significant_missing)[:5])}",
                "warning"
            ))
        
        return flags
    
    def check_empty_page(self, page: Page) -> List[ValidationFlag]:
        """
        Check if page extraction is empty.
        
        Args:
            page: Extracted page object
        
        Returns:
            List of validation flags
        """
        flags = []
        
        if (not page.clean_facts and 
            not page.visual_explanation and 
            not page.inferred_message.strip()):
            flags.append(ValidationFlag(
                page.page_index,
                "empty_page",
                "All content fields (clean_facts, visual_explanation, inferred_message) are empty",
                "error"
            ))
        
        return flags
    
    def check_branding_spam(self, page: Page) -> List[ValidationFlag]:
        """
        Check for repeated branding/short tokens.
        
        Args:
            page: Extracted page object
        
        Returns:
            List of validation flags
        """
        flags = []
        
        # Count occurrences of short tokens in facts
        all_text = " ".join(page.clean_facts + page.visual_explanation)
        words = all_text.split()
        
        # Count short words (likely brand names)
        short_words = [w for w in words if len(w) <= 10 and len(w) >= 2]
        word_counts = {}
        for word in short_words:
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        # Find words repeated too many times
        spam_words = [
            (word, count) for word, count in word_counts.items()
            if count > self.max_brand_repetition
        ]
        
        if spam_words:
            flags.append(ValidationFlag(
                page.page_index,
                "branding_spam",
                f"Repeated short tokens detected: {', '.join([f'{w}({c}x)' for w, c in spam_words[:3]])}",
                "warning"
            ))
        
        return flags
    
    def check_title_quality(self, page: Page) -> List[ValidationFlag]:
        """
        Check title quality.
        
        Args:
            page: Extracted page object
        
        Returns:
            List of validation flags
        """
        flags = []
        
        # Check length
        if len(page.title) < self.min_title_length:
            flags.append(ValidationFlag(
                page.page_index,
                "title_quality",
                f"Title too short: '{page.title}' ({len(page.title)} chars)",
                "warning"
            ))
        
        # Check if garbled (too many non-alphanumeric)
        alphanumeric_ratio = sum(c.isalnum() or c.isspace() for c in page.title) / len(page.title)
        if alphanumeric_ratio < 0.6:
            flags.append(ValidationFlag(
                page.page_index,
                "title_quality",
                f"Title appears garbled: '{page.title}'",
                "warning"
            ))
        
        return flags
    
    def check_duplicate_facts(self, page: Page) -> List[ValidationFlag]:
        """
        Check for duplicate facts.
        
        Args:
            page: Extracted page object
        
        Returns:
            List of validation flags
        """
        flags = []
        
        # Check exact duplicates
        if len(page.clean_facts) != len(set(page.clean_facts)):
            flags.append(ValidationFlag(
                page.page_index,
                "duplicate_facts",
                "Duplicate facts detected in clean_facts",
                "warning"
            ))
        
        return flags
    
    def validate_page(
        self,
        page: Page,
        text_layer: str = "",
        ocr_text: str = ""
    ) -> List[ValidationFlag]:
        """
        Run all validation checks on a page.
        
        Args:
            page: Extracted page object
            text_layer: PDF text layer (for numbers check)
            ocr_text: OCR text (for numbers check)
        
        Returns:
            List of all validation flags
        """
        flags = []
        
        # Run all checks
        flags.extend(self.check_empty_page(page))
        flags.extend(self.check_title_quality(page))
        flags.extend(self.check_duplicate_facts(page))
        flags.extend(self.check_branding_spam(page))
        flags.extend(self.check_numbers_coverage(page, text_layer, ocr_text))
        
        return flags
    
    def validate_document(self, document: Document) -> List[ValidationFlag]:
        """
        Validate document-level constraints.
        
        Args:
            document: Document object
        
        Returns:
            List of validation flags
        """
        flags = []
        
        # Check schema version
        if document.schema_version != "1.0":
            flags.append(ValidationFlag(
                0,
                "schema_version",
                f"Invalid schema_version: {document.schema_version}, expected '1.0'",
                "error"
            ))
        
        # Check page_count matches
        if document.page_count != len(document.pages):
            flags.append(ValidationFlag(
                0,
                "page_count",
                f"page_count ({document.page_count}) != len(pages) ({len(document.pages)})",
                "error"
            ))
        
        # Check sequential page indices
        expected_indices = list(range(1, document.page_count + 1))
        actual_indices = [p.page_index for p in document.pages]
        if actual_indices != expected_indices:
            flags.append(ValidationFlag(
                0,
                "page_indices",
                f"Page indices not sequential: expected {expected_indices}, got {actual_indices}",
                "error"
            ))
        
        return flags
    
    def should_retry_page(self, flags: List[ValidationFlag]) -> bool:
        """
        Determine if a page should be retried based on flags.
        
        Args:
            flags: List of validation flags
        
        Returns:
            True if page should be retried
        """
        # Retry if there are any errors or critical warnings
        error_flags = [f for f in flags if f.severity == "error"]
        critical_warnings = [f for f in flags if f.flag_type in ["numbers_coverage", "empty_page"]]
        
        return len(error_flags) > 0 or len(critical_warnings) > 0
    
    def get_retry_instruction(self, flags: List[ValidationFlag]) -> str:
        """
        Generate retry instruction based on validation flags.
        
        Args:
            flags: List of validation flags
        
        Returns:
            Instruction string for retry
        """
        instructions = []
        
        for flag in flags:
            if flag.flag_type == "numbers_coverage":
                instructions.append("Carefully extract ALL numbers visible on the page with their full context.")
            elif flag.flag_type == "empty_page":
                instructions.append("Extract meaningful content from this page - look carefully at all text and visuals.")
            elif flag.flag_type == "title_quality":
                instructions.append("Provide a clear, descriptive title for this page.")
        
        return " ".join(set(instructions))
