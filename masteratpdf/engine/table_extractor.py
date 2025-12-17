"""
MasterAtPDF: Table Extractor

Extrae contenido de tablas detectadas, incluyendo:
- Texto de cada celda
- Formato (bold, italic, font, size)
- Alineación
- Celdas merged
"""

import fitz
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class CellAlignment(Enum):
    """Alineación de texto en celda."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass
class CellContent:
    """Contenido de una celda de tabla."""
    text: str
    is_bold: bool = False
    is_italic: bool = False
    font_name: str = "Times New Roman"
    font_size: float = 12.0
    alignment: CellAlignment = CellAlignment.LEFT
    
    def __repr__(self):
        flags = []
        if self.is_bold:
            flags.append("B")
        if self.is_italic:
            flags.append("I")
        flag_str = f"[{','.join(flags)}]" if flags else ""
        return f"Cell({self.text[:20]}... {flag_str})"


@dataclass
class MergedCellRegion:
    """Región de celdas merged."""
    start_row: int
    start_col: int
    end_row: int
    end_col: int


@dataclass
class Table:
    """Representación de tabla completa."""
    rows: int
    cols: int
    data: List[List[CellContent]]
    merged_cells: List[MergedCellRegion] = field(default_factory=list)
    
    def __repr__(self):
        return f"Table({self.rows}x{self.cols}, {len(self.merged_cells)} merged)"


class TableExtractor:
    """
    Extrae contenido de tablas desde regiones detectadas.
    """
    
    def __init__(self):
        self.min_cell_width = 10  # Mínimo ancho de celda en puntos
        self.min_cell_height = 5  # Mínimo alto de celda
    
    def extract_table(self, page: fitz.Page, table_region) -> Optional[Table]:
        """
        Extrae tabla completa desde una región.
        
        Args:
            page: Página de PyMuPDF
            table_region: TableRegion detectada
            
        Returns:
            Tabla con todo su contenido y formato
        """
        
        # Extraer texto con posiciones en la región
        words = page.get_text("dict", clip=table_region.bbox)
        
        # Detectar estructura de filas/columnas
        grid = self._detect_cell_grid(table_region, words)
        
        if not grid:
            return None
        
        # Extraer contenido de cada celda
        table_data = []
        for row_cells in grid:
            row_data = []
            for cell_bbox in row_cells:
                content = self._extract_cell_content(words, cell_bbox)
                row_data.append(content)
            table_data.append(row_data)
        
        # Detectar celdas merged
        merged = self._detect_merged_cells(table_data)
        
        return Table(
            rows=len(table_data),
            cols=len(table_data[0]) if table_data else 0,
            data=table_data,
            merged_cells=merged
        )
    
    def _detect_cell_grid(self, table_region, words_dict) -> List[List[tuple]]:
        """
        Detecta grid de celdas basándose en posiciones de texto.
        
        Returns:
            Lista de filas, cada fila es lista de bboxes de celdas
        """
        
        # Extraer todas las palabras en la tabla
        all_words = []
        for block in words_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bbox = span["bbox"]
                    all_words.append({
                        'text': span["text"],
                        'bbox': bbox,
                        'x': bbox[0],
                        'y': bbox[1],
                        'font': span.get("font", ""),
                        'size': span.get("size", 12),
                        'flags': span.get("flags", 0)
                    })
        
        if not all_words:
            return []
        
        # Agrupar palabras por filas (mismo Y aproximadamente)
        rows = self._group_by_rows(all_words)
        
        # Detectar columnas (posiciones X)
        col_positions = self._detect_column_positions(all_words)
        
        # Crear grid de celdas
        grid = []
        for row_words in rows:
            row_cells = []
            for i in range(len(col_positions) - 1):
                x_start = col_positions[i]
                x_end = col_positions[i + 1]
                
                # Bbox de esta celda
                y_min = min(w['y'] for w in row_words)
                y_max = max(w['bbox'][3] for w in row_words)
                
                cell_bbox = (x_start, y_min, x_end, y_max)
                row_cells.append(cell_bbox)
            
            grid.append(row_cells)
        
        return grid
    
    def _group_by_rows(self, words: List[dict], threshold: float = 5.0) -> List[List[dict]]:
        """Agrupa palabras en filas basándose en posición Y."""
        
        if not words:
            return []
        
        # Ordenar por Y
        sorted_words = sorted(words, key=lambda w: w['y'])
        
        rows = []
        current_row = [sorted_words[0]]
        current_y = sorted_words[0]['y']
        
        for word in sorted_words[1:]:
            if abs(word['y'] - current_y) < threshold:
                current_row.append(word)
            else:
                rows.append(current_row)
                current_row = [word]
                current_y = word['y']
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def _detect_column_positions(self, words: List[dict]) -> List[float]:
        """Detecta posiciones X de columnas."""
        
        # Obtener todas las posiciones X únicas
        x_positions = sorted(set(w['x'] for w in words))
        
        # Agrupar posiciones cercanas
        if not x_positions:
            return []
        
        col_positions = [x_positions[0]]
        
        for x in x_positions[1:]:
            if x - col_positions[-1] > self.min_cell_width:
                col_positions.append(x)
        
        # Agregar posición final (ancho de tabla)
        max_x = max(w['bbox'][2] for w in words)
        col_positions.append(max_x)
        
        return col_positions
    
    def _extract_cell_content(self, words_dict: dict, cell_bbox: tuple) -> CellContent:
        """Extrae contenido de una celda específica."""
        
        x0, y0, x1, y1 = cell_bbox
        
        # Encontrar palabras dentro de esta celda
        cell_words = []
        for block in words_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bbox = span["bbox"]
                    # Verificar si está dentro de la celda
                    if (bbox[0] >= x0 and bbox[2] <= x1 and 
                        bbox[1] >= y0 and bbox[3] <= y1):
                        cell_words.append({
                            'text': span["text"],
                            'font': span.get("font", ""),
                            'size': span.get("size", 12),
                            'flags': span.get("flags", 0)
                        })
        
        if not cell_words:
            return CellContent(text="", font_size=12.0)
        
        # Combinar texto
        text = " ".join(w['text'] for w in cell_words)
        
        # Detectar formato (usar primera palabra como referencia)
        first_word = cell_words[0]
        flags = first_word['flags']
        
        is_bold = bool(flags & 2**4)  # Flag 16 = bold
        is_italic = bool(flags & 2**1)  # Flag 2 = italic
        
        return CellContent(
            text=text.strip(),
            is_bold=is_bold,
            is_italic=is_italic,
            font_name=first_word['font'],
            font_size=first_word['size']
        )
    
    def _detect_merged_cells(self, table_data: List[List[CellContent]]) -> List[MergedCellRegion]:
        """
        Detecta celdas merged (vacías que deberían ser parte de celda anterior).
        """
        
        merged = []
        
        if not table_data:
            return merged
        
        rows = len(table_data)
        cols = len(table_data[0])
        
        # Buscar celdas vacías consecutivas horizontalmente
        for i in range(rows):
            j = 0
            while j < cols:
                if table_data[i][j].text:
                    # Buscar cuántas celdas vacías siguen
                    empty_count = 0
                    k = j + 1
                    while k < cols and not table_data[i][k].text:
                        empty_count += 1
                        k += 1
                    
                    if empty_count > 0:
                        # Estas celdas están merged
                        merged.append(MergedCellRegion(
                            start_row=i,
                            start_col=j,
                            end_row=i,
                            end_col=k - 1
                        ))
                    
                    j = k
                else:
                    j += 1
        
        return merged


if __name__ == "__main__":
    # Test
    from table_detector import TableDetector
    
    pdf_path = "d:/PROYECTOS/PYTHON/masteratpdf-backend/tesis.pdf"
    
    print("🔍 Detectando y extrayendo tablas...")
    
    # Detectar
    detector = TableDetector(dpi=200)
    pdf_doc = fitz.open(pdf_path)
    
    # Extraer primera página con tabla (ej: página 52)
    page = pdf_doc[51]  # Página 52 (0-indexed)
    tables = detector.detect_tables_in_page(page)
    
    print(f"\n✅ Detectadas {len(tables)} tablas en página 52")
    
    # Extraer contenido
    extractor = TableExtractor()
    
    for i, table_region in enumerate(tables[:3], 1):
        table = extractor.extract_table(page, table_region)
        if table:
            print(f"\n📊 Tabla {i}: {table}")
            print(f"   Primeras celdas:")
            for row in table.data[:3]:
                print(f"     {[cell.text[:20] for cell in row[:3]]}")
    
    pdf_doc.close()
