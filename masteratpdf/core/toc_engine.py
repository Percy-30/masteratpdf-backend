import fitz
import re

def extract_real_toc(pdf_path: str):
    """Devuelve TOC real del PDF: [(level, title, page), ...]"""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    doc.close()
    return toc  # [(level, title, page), ...]


def extract_embedded_toc(pdf_path: str) -> dict:
    """
    Extrae TOC embedded en el contenido del PDF.
    Busca secciones como "Índice de Figuras", "Índice de Tablas".
    Retorna: {"figures": [...], "tables": [...]}
    """
    doc = fitz.open(pdf_path)
    embedded = {"figures": [], "tables": []}
    
    in_figure_section = False
    in_table_section = False
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Detectar inicio de secciones
            if re.search(r'índice\s+de\s+figuras', line_stripped, re.IGNORECASE):
                in_figure_section = True
                in_table_section = False
                continue
            
            if re.search(r'índice\s+de\s+tablas', line_stripped, re.IGNORECASE):
                in_table_section = True
                in_figure_section = False
                continue
            
            # Detectar fin de secciones (nuevo heading)
            if re.match(r'^[A-ZÁÉÍÓÚ\s]+$', line_stripped) and len(line_stripped) > 10:
                in_figure_section = False
                in_table_section = False
            
            # Extraer entradas
            if in_figure_section:
                match = re.search(r'(Figura\s+\d+[^\d]+).*?(\d+)\s*$', line_stripped, re.IGNORECASE)
                if match:
                    embedded["figures"].append((match.group(1).strip(), int(match.group(2))))
            
            if in_table_section:
                match = re.search(r'(Tabla\s+\d+[^\d]+).*?(\d+)\s*$', line_stripped, re.IGNORECASE)
                if match:
                    embedded["tables"].append((match.group(1).strip(), int(match.group(2))))
    
    doc.close()
    return embedded