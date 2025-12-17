import fitz
import re
from typing import List, Tuple, Dict

def extract_figure_index(pdf_path: str) -> List[Tuple[str, int]]:
    """
    Extrae índice de figuras del PDF, eliminando duplicados y ordenando ascendentemente.
    Retorna: [(title_completo, page_number), ...]
    """
    doc = fitz.open(pdf_path)
    figures_dict = {}  # {numero: (titulo_mas_largo, pagina)}
    
    # Patrones para detectar figuras
    patterns = [
        r'Figura\s+(\d+)\s+([^\n]+)',  # Figura N ...
        r'Figure\s+(\d+)\s+([^\n]+)',  # Figure N ...
    ]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                fig_num = int(match.group(1))
                description = match.group(2).strip()
                
                # Limpiar descripción
                description = re.sub(r'\s+', ' ', description)
                description = re.sub(r'\.+$', '', description)  # Remove trailing dots
                
                # Evitar entradas que solo tienen "..." o son muy cortas
                if len(description) < 5 or description.startswith('...'):
                    continue
                
                # Si ya existe este número, mantener el título más largo
                if fig_num in figures_dict:
                    existing_title, existing_page = figures_dict[fig_num]
                    if len(description) > len(existing_title):
                        figures_dict[fig_num] = (description, page_num + 1)
                else:
                    figures_dict[fig_num] = (description, page_num + 1)
    
    doc.close()
    
    # Convertir a lista y ordenar ascendentemente por número
    figures = []
    for fig_num in sorted(figures_dict.keys()):
        title, page = figures_dict[fig_num]
        full_title = f"Figura {fig_num} {title}"
        figures.append((full_title, page))
    
    return figures


def extract_table_index(pdf_path: str) -> List[Tuple[str, int]]:
    """
    Extrae índice de tablas del PDF, eliminando duplicados y ordenando ascendentemente.
    Retorna: [(title_completo, page_number), ...]
    """
    doc = fitz.open(pdf_path)
    tables_dict = {}  # {numero: (titulo_mas_largo, pagina)}
    
    # Patrones para detectar tablas
    patterns = [
        r'Tabla\s+(\d+)\s+([^\n]+)',  # Tabla N ...
        r'Table\s+(\d+)\s+([^\n]+)',  # Table N ...
    ]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                table_num = int(match.group(1))
                description = match.group(2).strip()
                
                # Limpiar descripción
                description = re.sub(r'\s+', ' ', description)
                description = re.sub(r'\.+$', '', description)  # Remove trailing dots
                
                # Evitar entradas que solo tienen "..." o son muy cortas
                if len(description) < 5 or description.startswith('...'):
                    continue
                
                # Si ya existe este número, mantener el título más largo
                if table_num in tables_dict:
                    existing_title, existing_page = tables_dict[table_num]
                    if len(description) > len(existing_title):
                        tables_dict[table_num] = (description, page_num + 1)
                else:
                    tables_dict[table_num] = (description, page_num + 1)
    
    doc.close()
    
    # Convertir a lista y ordenar ascendentemente por número
    tables = []
    for table_num in sorted(tables_dict.keys()):
        title, page = tables_dict[table_num]
        full_title = f"Tabla {table_num} {title}"
        tables.append((full_title, page))
    
    return tables


def extract_all_indices(pdf_path: str) -> dict:
    """
    Extrae todos los índices del PDF.
    Retorna: {"figures": [...], "tables": [...]}
    """
    return {
        "figures": extract_figure_index(pdf_path),
        "tables": extract_table_index(pdf_path)
    }
