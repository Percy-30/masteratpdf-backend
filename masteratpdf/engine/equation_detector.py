"""
MasterAtPDF: Equation Detector

Detecta ecuaciones matemáticas en PDF y las extrae como imágenes HD.

Estrategia:
1. Buscar símbolos matemáticos (∫, ∑, √, α, β, etc.)
2. Agrupar símbolos cercanos = ecuación
3. Extraer región como imagen de alta resolución
"""

import fitz
import re
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
import io
from PIL import Image


@dataclass
class EquationRegion:
    """Región donde se detectó una ecuación."""
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page_num: int
    confidence: float  # 0-1, qué tan seguro estamos que es ecuación
    text_preview: str  # Preview del texto detectado
    
    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]


class EquationDetector:
    """
    Detecta ecuaciones matemáticas en PDF.
    
    Usa heurísticas basadas en:
    - Símbolos matemáticos Unicode
    - Patrones de ecuaciones
    - Densidad de símbolos especiales
    """
    
    # Símbolos matemáticos comunes
    MATH_SYMBOLS = {
        # Operadores
        '∫', '∑', '∏', '∂', '∆', '∇',
        # Griegas
        'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
        'ν', 'ξ', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω',
        'Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ', 'Ι', 'Κ', 'Λ', 'Μ',
        'Ν', 'Ξ', 'Π', 'Ρ', 'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω',
        # Relaciones
        '≈', '≠', '≤', '≥', '∈', '∉', '⊂', '⊃', '∪', '∩',
        # Otros
        '√', '∞', '±', '×', '÷', '→', '←', '↔', '⇒', '⇐', '⇔'
    }
    
    # Patrones de ecuaciones comunes
    EQUATION_PATTERNS = [
        r'[a-zA-Z]\s*=\s*[^,\.]+',  # y = mx + b
        r'\d+\s*[+\-*/]\s*\d+',      # 2 + 2
        r'[a-zA-Z]\^\d+',             # x^2
        r'[a-zA-Z]_\d+',              # x_1
        r'\([^)]+\)\s*=',             # (x+y) =
    ]
    
    def __init__(self, min_confidence: float = 0.5):
        """
        Args:
            min_confidence: Mínima confianza para considerar ecuación
        """
        self.min_confidence = min_confidence
    
    def detect_equations_in_page(self, page: fitz.Page) -> List[EquationRegion]:
        """
        Detecta ecuaciones en una página.
        
        Args:
            page: Página de PyMuPDF
            
        Returns:
            Lista de ecuaciones detectadas
        """
        
        # Extraer texto con posiciones
        words_dict = page.get_text("dict")
        
        equations = []
        
        # Buscar por bloques
        for block in words_dict.get("blocks", []):
            for line in block.get("lines", []):
                # Analizar línea completa
                line_text = ""
                line_bbox = None
                
                for span in line.get("spans", []):
                    line_text += span["text"]
                    bbox = span["bbox"]
                    
                    if line_bbox is None:
                        line_bbox = list(bbox)
                    else:
                        # Expandir bbox
                        line_bbox[0] = min(line_bbox[0], bbox[0])
                        line_bbox[1] = min(line_bbox[1], bbox[1])
                        line_bbox[2] = max(line_bbox[2], bbox[2])
                        line_bbox[3] = max(line_bbox[3], bbox[3])
                
                if not line_text.strip():
                    continue
                
                # Calcular confianza de que es ecuación
                confidence = self._calculate_equation_confidence(line_text)
                
                if confidence >= self.min_confidence:
                    equations.append(EquationRegion(
                        bbox=tuple(line_bbox),
                        page_num=page.number,
                        confidence=confidence,
                        text_preview=line_text[:50]
                    ))
        
        # Filtrar ecuaciones muy cercanas (probablemente duplicados)
        equations = self._filter_overlapping(equations)
        
        return equations
    
    def _calculate_equation_confidence(self, text: str) -> float:
        """
        Calcula qué tan probable es que el texto sea una ecuación.
        
        Returns:
            Confianza de 0 a 1
        """
        
        if not text:
            return 0.0
        
        confidence = 0.0
        
        # 1. Contiene símbolos matemáticos
        math_symbol_count = sum(1 for char in text if char in self.MATH_SYMBOLS)
        if math_symbol_count > 0:
            confidence += 0.4 * min(math_symbol_count / 3, 1.0)
        
        # 2. Coincide con patrones de ecuaciones
        for pattern in self.EQUATION_PATTERNS:
            if re.search(pattern, text):
                confidence += 0.3
                break
        
        # 3. Tiene estructura matemática (números, operadores, variables)
        has_numbers = bool(re.search(r'\d', text))
        has_operators = bool(re.search(r'[+\-*/=<>]', text))
        has_variables = bool(re.search(r'[a-zA-Z]', text))
        
        if has_numbers and has_operators:
            confidence += 0.2
        if has_variables and has_operators:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _filter_overlapping(self, equations: List[EquationRegion]) -> List[EquationRegion]:
        """Filtra ecuaciones que se solapan (probablemente duplicados)."""
        
        if not equations:
            return []
        
        # Ordenar por confianza (mayor primero)
        sorted_eqs = sorted(equations, key=lambda e: e.confidence, reverse=True)
        
        filtered = []
        
        for eq in sorted_eqs:
            # Verificar si se solapa con alguna ya aceptada
            overlaps = False
            for accepted in filtered:
                if self._boxes_overlap(eq.bbox, accepted.bbox):
                    overlaps = True
                    break
            
            if not overlaps:
                filtered.append(eq)
        
        return filtered
    
    def _boxes_overlap(self, box1: tuple, box2: tuple, threshold: float = 0.5) -> bool:
        """Verifica si dos boxes se solapan significativamente."""
        
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # Calcular intersección
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        intersection = x_overlap * y_overlap
        
        # Área de cada box
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        
        # Porcentaje de overlap respecto al más pequeño
        min_area = min(area1, area2)
        
        if min_area == 0:
            return False
        
        overlap_ratio = intersection / min_area
        
        return overlap_ratio > threshold
    
    def extract_equation_image(self, page: fitz.Page, equation: EquationRegion, 
                               dpi: int = 300) -> Optional[Image.Image]:
        """
        Extrae ecuación como imagen de alta resolución.
        
        Args:
            page: Página de PyMuPDF
            equation: Ecuación a extraer
            dpi: Resolución (más alto = mejor calidad)
            
        Returns:
            Imagen PIL
        """
        
        # Expandir bbox un poco para incluir contexto
        x0, y0, x1, y1 = equation.bbox
        margin = 5
        expanded_bbox = (
            max(0, x0 - margin),
            max(0, y0 - margin),
            min(page.rect.width, x1 + margin),
            min(page.rect.height, y1 + margin)
        )
        
        # Renderizar solo esa región
        pix = page.get_pixmap(clip=expanded_bbox, dpi=dpi)
        
        # Convertir a PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        return img


if __name__ == "__main__":
    # Test
    pdf_path = "d:/PROYECTOS/PYTHON/masteratpdf-backend/tesis.pdf"
    
    print("🔍 Detectando ecuaciones en tesis.pdf...")
    
    detector = EquationDetector(min_confidence=0.4)
    pdf_doc = fitz.open(pdf_path)
    
    all_equations = []
    
    # Buscar en primeras 50 páginas
    for page_num in range(min(50, len(pdf_doc))):
        page = pdf_doc[page_num]
        equations = detector.detect_equations_in_page(page)
        all_equations.extend(equations)
    
    print(f"\n✅ Detectadas {len(all_equations)} ecuaciones")
    
    # Mostrar primeras 10
    print("\n📊 Primeras ecuaciones:")
    for i, eq in enumerate(all_equations[:10], 1):
        print(f"  {i}. Pág {eq.page_num + 1} (confianza: {eq.confidence:.2f}): {eq.text_preview}")
    
    # Extraer primera ecuación como imagen
    if all_equations:
        print("\n💾 Extrayendo primera ecuación como imagen...")
        page = pdf_doc[all_equations[0].page_num]
        img = detector.extract_equation_image(page, all_equations[0], dpi=300)
        
        if img:
            img.save("d:/PROYECTOS/PYTHON/masteratpdf-backend/test_equation.png")
            print(f"  ✓ Guardada: test_equation.png ({img.size[0]}x{img.size[1]})")
    
    pdf_doc.close()
