"""
MasterAtPDF CLI - Native Engine

CLI mejorado usando el motor nativo.
"""

import argparse
import sys
from pathlib import Path

# Ensure masteratpdf is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from masteratpdf.engine import ConversionPipeline
from masteratpdf.engine.quality_checker import QualityChecker


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='MasterAtPDF - Professional PDF to DOCX Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  masteratpdf-native input.pdf

  # Specify output
  masteratpdf-native input.pdf -o output.docx

  # With quality report
  masteratpdf-native input.pdf --quality-report

  # Quiet mode
  masteratpdf-native input.pdf -q
        """
    )
    
    parser.add_argument('pdf_file', help='Input PDF file')
    parser.add_argument('-o', '--output', help='Output DOCX file (default: input_converted.docx)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (no progress)')
    parser.add_argument('--quality-report', action='store_true', help='Generate quality report after conversion')
    parser.add_argument('--version', action='version', version='MasterAtPDF Native Engine 1.0.0')
    
    args = parser.parse_args()
    
    # Validate input
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return 1
    
    # Determine output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.with_stem(f"{pdf_path.stem}_converted")
    
    # Convert
    print(f"\n🚀 MasterAtPDF Native Engine")
    print(f"📄 Input: {pdf_path}")
    print(f"💾 Output: {output_path}\n")
    
    pipeline = ConversionPipeline(verbose=not args.quiet)
    success = pipeline.convert(str(pdf_path), str(output_path))
    
    if not success:
        print("\n❌ Conversion failed")
        return 1
    
    # Quality report
    if args.quality_report:
        print("\n" + "="*70)
        print("Generating quality report...")
        print("="*70)
        
        checker = QualityChecker(str(output_path))
        metrics = checker.check_all()
        checker.print_report()
    
    print(f"\n✅ Success! File saved to: {output_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
