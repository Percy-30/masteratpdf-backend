"""
MasterAtPDF: Layout Analyzer

Analiza el layout EXACTO del índice del PDF.
Extrae fuentes, posiciones, espaciado - TODO.
"""

import fitz
from typing import List, Dict, Tuple
from dataclasses import dataclass
import re


@dataclass
class LayoutElement:
    """Un elemento de texto con layout completo."""
    text: str
    x: float
    y: float
    width: float
    height: float
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    color: Tuple[int, int, int]
    page_number: int


class LayoutAnalyzer:
    """
    Analiza el layout exacto del PDF.
    
    Extrae TODO el formato visual para recrearlo en DOCX.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
    
    def analyze_index_layout(self, start_page: int = 0, end_page: int = 12) -> Dict:
        """
        Analiza el layout del índice con precisión pixel-perfect.
        
        Returns:
            {
                'elements': List[LayoutElement],
                'page_width': float,
                'page_height': float,
                'fonts_used': Set[str],
                'indentation_levels': List[float]
            }
        """
        print(f"\n🔍 Analizando layout del índice (páginas {start_page}-{end_page})...")
        
        elements = []
        fonts_used = set()
        x_positions = []  # Para detectar niveles de indentación
        
        for page_num in range(start_page, min(end_page, len(self.doc))):
            page = self.doc[page_num]
            
            # Obtener texto con detalles completos
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:  # Solo bloques de texto
                    continue
                
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        
                        # Extraer información completa
                        bbox = span.get("bbox", [0, 0, 0, 0])
                        font = span.get("font", "")
                        size = span.get("size", 12)
                        flags = span.get("flags", 0)
                        color_int = span.get("color", 0)
                        
                        # Convertir color
                        r = (color_int >> 16) & 0xFF
                        g = (color_int >> 8) & 0xFF
                        b = color_int & 0xFF
                        
                        # Detectar bold/italic por flags
                        is_bold = bool(flags & 16)
                        is_italic = bool(flags & 2)
                        
                        element = LayoutElement(
                            text=text,
                            x=bbox[0],
                            y=bbox[1],
                            width=bbox[2] - bbox[0],
                            height=bbox[3] - bbox[1],
                            font_name=font,
                            font_size=size,
                            is_bold=is_bold,
                            is_italic=is_italic,
                            color=(r, g, b),
                            page_number=page_num + 1
                        )
                        
                        elements.append(element)
                        fonts_used.add(font)
                        x_positions.append(bbox[0])
        
        # Detectar niveles de indentación
        indentation_levels = self._detect_indentation_levels(x_positions)
        
        # Obtener dimensiones de página
        first_page = self.doc[start_page]
        page_width = first_page.rect.width
        page_height = first_page.rect.height
        
        print(f"  ✓ {len(elements)} elementos extraídos")
        print(f"  ✓ {len(fonts_used)} fuentes únicas")
        print(f"  ✓ {len(indentation_levels)} niveles de indentación")
        
        return {
            'elements': elements,
            'page_width': page_width,
            'page_height': page_height,
            'fonts_used': fonts_used,
            'indentation_levels': sorted(indentation_levels)
        }
    
    def _detect_indentation_levels(self, x_positions: List[float], tolerance: float = 5.0) -> List[float]:
        """
        Detecta niveles únicos de indentación.
        
        Agrupa posiciones X similares para identificar niveles de jerarquía.
        """
        if not x_positions:
            return []
        
        # Ordenar y agrupar posiciones similares
        sorted_x = sorted(set(x_positions))
        levels = []
        current_level = sorted_x[0]
        levels.append(current_level)
        
        for x in sorted_x[1:]:
            if x - current_level > tolerance:
                levels.append(x)
                current_level = x
        
        return levels
    
    def extract_index_structure(self, layout_data: Dict) -> List[Dict]:
        """
        Parsea la estructura del índice desde los elementos de layout.
        
        Returns:
            Lista de entradas con formato:
            {
                'text': 'INTRODUCCIÓN',
                'page': 16,
                'level': 1,
                'x': 72.0,
                'font_size': 12.0,
                'is_bold': True
            }
        """
        elements = layout_data['elements']
        indentation_levels = layout_data['indentation_levels']
        
        entries = []
        
        # Ordenar elementos por Y (top to bottom)
        sorted_elements = sorted(elements, key=lambda e: (e.page_number, e.y))
        
        for elem in sorted_elements:
            # Detectar si es una entrada del índice
            # (tiene número de página al final o puntos guía)
            if self._is_index_entry(elem.text):
                # Determinar nivel basado en indentación
                level = self._get_indentation_level(elem.x, indentation_levels)
                
                # Extraer número de página si existe
                page_num = self._extract_page_number(elem.text)
                
                entries.append({
                    'text': elem.text,
                    'page': page_num,
                    'level': level,
                    'x': elem.x,
                    'y': elem.y,
                    'font_name': elem.font_name,
                    'font_size': elem.font_size,
                    'is_bold': elem.is_bold,
                    'is_italic': elem.is_italic
                })
        
        return entries
    
    def _is_index_entry(self, text: str) -> bool:
        """Detecta si un texto es una entrada de índice."""
        # Filtros básicos
        if len(text.strip()) < 10:  # Muy corto
            return False
        
        # Detectar si es solo números o caracteres extraños
        if re.match(r'^[\d\s\t]+$', text):  # Solo números/spaces
            return False
        
        # Detectar texto corrupto (demasiados caracteres no-ASCII)
        non_ascii = len([c for c in text if ord(c) > 127])
        if non_ascii > len(text) * 0.5:  # >50% caracteres raros
            return False
        
        # Patrones comunes de índice
        patterns = [
            r'\.{3,}',  # Puntos guía (...)
            r'\d+\s*$',    # Termina en número
            r'CAPITULO|INTRODUCCIÓN|CONCLUSIONES|RECOMENDACIONES|REFERENCIAS',  # Palabras clave
            r'^\d+\.\d+',  # Numeración (1.1, 1.2.1, etc.)
            r'^Tabla\s+\d+',  # Tabla
            r'^Figura\s+\d+',  # Figura
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_page_number(self, text: str) -> int:
        """Extrae número de página de una entrada."""
        # Buscar último número en el texto
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[-1])
        return 0
    
    def _get_indentation_level(self, x: float, levels: List[float], tolerance: float = 5.0) -> int:
        """Determina el nivel de indentación basado en posición X."""
        for idx, level_x in enumerate(levels):
            if abs(x - level_x) <= tolerance:
                return idx + 1  # Level 1-indexed
        
        return 1  # Default
    
    def print_layout_report(self, layout_data: Dict):
        """Imprime reporte detallado del layout."""
        print("\n" + "="*70)
        print("📊 Reporte de Layout del Índice")
        print("="*70)
        
        print(f"\n📐 Dimensiones:")
        print(f"   Ancho: {layout_data['page_width']:.2f} pts")
        print(f"   Alto: {layout_data['page_height']:.2f} pts")
        
        print(f"\n🔤 Fuentes encontradas:")
        for font in sorted(layout_data['fonts_used']):
            print(f"   • {font}")
        
        print(f"\n📏 Niveles de indentación:")
        for idx, level in enumerate(layout_data['indentation_levels'], 1):
            print(f"   Nivel {idx}: {level:.2f} pts desde el margen")
        
        print(f"\n📄 Elementos totales: {len(layout_data['elements'])}")
        
        # Mostrar primeros 10 elementos
        print(f"\n🔍 Primeros 10 elementos:")
        for elem in layout_data['elements'][:10]:
            print(f"   [{elem.x:.1f}, {elem.y:.1f}] {elem.font_name} {elem.font_size:.1f}pt")
            print(f"       '{elem.text[:60]}...'")
    
    def close(self):
        """Cierra el documento PDF."""
        if self.doc:
            self.doc.close()
