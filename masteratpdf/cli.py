import argparse
import os
from masteratpdf.core import build_docx_professional

def main():
    parser = argparse.ArgumentParser(description="MasteratPDF - PDF → DOCX profesional")
    parser.add_argument("pdf", help="Archivo PDF a convertir")
    parser.add_argument("-o", "--output", default=None, help="Ruta de salida del DOCX")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print("❌ Archivo no encontrado")
        return

    base = os.path.splitext(os.path.basename(args.pdf))[0]
    output = args.output or f"{base}_masterat.docx"

    build_docx_professional(args.pdf, output)
    print(f"✅ Convertido: {output}")

if __name__ == "__main__":
    main()