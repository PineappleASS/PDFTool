#!/usr/bin/env python3
"""
PDF to JSON Extractor - Command Line Interface

Extracts structured information from PDF presentations and outputs JSON.
"""
import argparse
import logging
import sys
from pathlib import Path

from config import Config
from pipeline import ExtractionPipeline


def setup_logging(verbose: bool = False):
    """
    Configure logging.
    
    Args:
        verbose: Enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract structured information from PDF presentations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s presentation.pdf
  %(prog)s deck.pdf -o results/output.json
  %(prog)s slides.pdf --max-pages 10 --verbose
  %(prog)s input.pdf -o output.json --scale 3.0

For more information, see README.md
        """
    )
    
    # Required arguments
    parser.add_argument(
        'pdf_path',
        type=str,
        help='Path to input PDF file'
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output.json',
        help='Output JSON file path (default: output.json)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help=f'Maximum pages to process (default: {Config.MAX_PAGES_PER_RUN})'
    )
    
    parser.add_argument(
        '--scale',
        type=float,
        default=None,
        help=f'PDF render scale factor (default: {Config.PDF_RENDER_SCALE})'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate input file
        pdf_path = Path(args.pdf_path)
        if not pdf_path.exists():
            logger.error(f"Input file not found: {pdf_path}")
            sys.exit(1)
        
        if not pdf_path.suffix.lower() == '.pdf':
            logger.error(f"Input file must be a PDF, got: {pdf_path.suffix}")
            sys.exit(1)
        
        # Validate output path
        output_path = Path(args.output)
        if output_path.suffix.lower() != '.json':
            logger.warning(f"Output file should have .json extension, got: {output_path.suffix}")
        
        # Validate configuration
        logger.info("Validating configuration...")
        Config.validate()
        
        # Override config if specified
        if args.scale:
            Config.PDF_RENDER_SCALE = args.scale
            logger.info(f"Using custom scale: {args.scale}")
        
        if args.max_pages:
            Config.MAX_PAGES_PER_RUN = args.max_pages
            logger.info(f"Using custom max pages: {args.max_pages}")
        
        # Initialize pipeline
        logger.info("Initializing extraction pipeline...")
        pipeline = ExtractionPipeline(config=Config)
        
        # Process PDF
        logger.info(f"Processing PDF: {pdf_path}")
        logger.info(f"Output will be saved to: {output_path}")
        
        document = pipeline.process_and_save(
            pdf_path=pdf_path,
            output_path=output_path,
            max_pages=args.max_pages
        )
        
        # Print summary
        print("\n" + "="*60)
        print("EXTRACTION COMPLETE")
        print("="*60)
        print(f"Input:      {pdf_path}")
        print(f"Output:     {output_path}")
        print(f"Pages:      {document.page_count}")
        print(f"Language:   {document.language.value}")
        print(f"Document ID: {document.document_id}")
        print("\n" + "─"*60)
        print("DOCUMENT SUMMARY")
        print("─"*60)
        print(f"\n{document.document_summary.one_paragraph}")
        
        print(f"\n📊 Key Metrics ({len(document.document_summary.key_metrics)}):")
        for metric in document.document_summary.key_metrics:
            print(f"  • {metric}")
        
        print(f"\n👥 Key Entities ({len(document.document_summary.key_entities)}):")
        for entity in document.document_summary.key_entities:
            print(f"  • {entity}")
        
        print(f"\n💡 Top Claims ({len(document.document_summary.top_claims)}):")
        for claim in document.document_summary.top_claims:
            print(f"  • {claim}")
        
        print(f"\n⚠️  Risks & Gaps ({len(document.document_summary.risks_and_gaps)}):")
        for risk in document.document_summary.risks_and_gaps:
            print(f"  • {risk}")
        print("="*60)
        print(f"\nJSON output saved to: {output_path}")
        
        logger.info("Extraction completed successfully")
        sys.exit(0)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()
