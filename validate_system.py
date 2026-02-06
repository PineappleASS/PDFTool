#!/usr/bin/env python3
"""
System validation script - checks if all components are properly set up.
"""
import sys
from pathlib import Path


def validate_imports():
    """Validate that all modules can be imported."""
    print("Validating imports...")
    
    try:
        import models
        print("✓ models")
        
        import config
        print("✓ config")
        
        import pdf_processor
        print("✓ pdf_processor")
        
        import ocr_processor
        print("✓ ocr_processor")
        
        import vision_extractor
        print("✓ vision_extractor")
        
        import validator
        print("✓ validator")
        
        import summary_generator
        print("✓ summary_generator")
        
        import pipeline
        print("✓ pipeline")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def validate_models():
    """Validate data models."""
    print("\nValidating data models...")
    
    try:
        from models import (
            Document, Page, PageType, Language,
            ExtractedNumber, Confidence, Source, DocumentSummary
        )
        
        # Test creating a minimal valid document
        page = Page(
            page_index=1,
            page_type=PageType.COVER,
            title="Test Page",
            confidence=Confidence(facts=0.9, visuals=0.8, inference=0.85)
        )
        print(f"✓ Created page: {page.title}")
        
        doc = Document(
            schema_version="1.0",
            document_id="test-123",
            source=Source(filename="test.pdf", file_type="pdf"),
            language=Language.ENGLISH,
            page_count=1,
            pages=[page]
        )
        print(f"✓ Created document: {doc.document_id}")
        
        # Test JSON serialization
        json_str = doc.model_dump_json(indent=2)
        print(f"✓ JSON serialization: {len(json_str)} bytes")
        
        return True
    except Exception as e:
        print(f"✗ Model validation failed: {e}")
        return False


def validate_file_structure():
    """Validate project file structure."""
    print("\nValidating file structure...")
    
    required_files = [
        'main.py',
        'models.py',
        'config.py',
        'pdf_processor.py',
        'ocr_processor.py',
        'vision_extractor.py',
        'validator.py',
        'summary_generator.py',
        'pipeline.py',
        'requirements.txt',
        'README.md',
        '.env.example',
        '.gitignore',
        '__init__.py'
    ]
    
    all_exist = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} not found")
            all_exist = False
    
    return all_exist


def main():
    """Run all validations."""
    print("="*60)
    print("PDF to JSON Extractor - System Validation")
    print("="*60)
    
    results = []
    
    # Run validations
    results.append(("File Structure", validate_file_structure()))
    results.append(("Imports", validate_imports()))
    results.append(("Data Models", validate_models()))
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name:20s}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ All validations passed!")
        print("\nSystem is ready. To use:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your OPENAI_API_KEY to .env")
        print("  3. Install dependencies: pip install -r requirements.txt")
        print("  4. Run: python main.py <pdf_file>")
        return 0
    else:
        print("\n✗ Some validations failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
