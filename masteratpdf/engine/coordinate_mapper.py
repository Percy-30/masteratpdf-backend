"""
MasterAtPDF Engine: Coordinate Mapper

Mapea coordenadas PDF (puntos, bottom-left origin) 
→ DOCX (inches/twips, top-left origin)

CRÍTICO para bookmarks precisos.
"""

from typing import Tuple
from dataclasses import dataclass


@dataclass
class PDFRect:
    """Rectángulo en coordenadas PDF."""
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class DOCXPosition:
    """Posición en coordenadas DOCX."""
    left: float  # inches from left
    top: float   # inches from top
    width: float
    height: float


class CoordinateMapper:
    """
    Mapea coordenadas PDF → DOCX con precisión exacta.
    
    PDF Coordinate System:
    - Origin: Bottom-left corner
    - Units: Points (1/72 inch)
    - Y-axis: Up is positive
    
    DOCX Coordinate System:
    - Origin: Top-left corner
    - Units: Twips (1/1440 inch) or inches
    - Y-axis: Down is positive
    """
    
    # Constantes de conversión
    POINTS_PER_INCH = 72
    TWIPS_PER_INCH = 1440
    TWIPS_PER_POINT = TWIPS_PER_INCH / POINTS_PER_INCH
    
    def __init__(self, page_width_pts: float, page_height_pts: float):
        """
        Args:
            page_width_pts: Ancho de página PDF en puntos
            page_height_pts: Alto de página PDF en puntos
        """
        self.pdf_page_width = page_width_pts
        self.pdf_page_height = page_height_pts
        
        # DOCX standard page (Letter: 8.5 x 11)
        self.docx_page_width = 8.5  # inches
        self.docx_page_height = 11  # inches
    
    def pdf_to_docx(self, pdf_rect: PDFRect) -> DOCXPosition:
        """
        Convierte rectángulo PDF a posición DOCX.
        
        Args:
            pdf_rect: Rectángulo en coordenadas PDF
            
        Returns:
            Posición en coordenadas DOCX (inches)
        """
        # Convertir PDF points a inches
        x0_inch = pdf_rect.x0 / self.POINTS_PER_INCH
        y0_inch = pdf_rect.y0 / self.POINTS_PER_INCH
        x1_inch = pdf_rect.x1 / self.POINTS_PER_INCH
        y1_inch = pdf_rect.y1 / self.POINTS_PER_INCH
        
        # Flipear eje Y (PDF bottom-left → DOCX top-left)
        pdf_page_height_inch = self.pdf_page_height / self.POINTS_PER_INCH
        
        top = pdf_page_height_inch - y1_inch
        bottom = pdf_page_height_inch - y0_inch
        
        return DOCXPosition(
            left=x0_inch,
            top=top,
            width=x1_inch - x0_inch,
            height=bottom - top
        )
    
    def pdf_to_twips(self, pdf_rect: PDFRect) -> Tuple[int, int, int, int]:
        """
        Convierte a twips para manipulación XML directa.
        
        Returns:
            (left_twips, top_twips, width_twips, height_twips)
        """
        docx_pos = self.pdf_to_docx(pdf_rect)
        
        return (
            int(docx_pos.left * self.TWIPS_PER_INCH),
            int(docx_pos.top * self.TWIPS_PER_INCH),
            int(docx_pos.width * self.TWIPS_PER_INCH),
            int(docx_pos.height * self.TWIPS_PER_INCH)
        )
    
    def get_page_paragraph_position(self, pdf_y: float) -> int:
        """
        Calcula posición aproximada de párrafo en página DOCX.
        
        Args:
            pdf_y: Coordenada Y en PDF (bottom-left origin)
            
        Returns:
            Índice aproximado de párrafo (0-based)
        """
        # Convertir Y de PDF a DOCX
        pdf_page_height_inch = self.pdf_page_height / self.POINTS_PER_INCH
        docx_y = pdf_page_height_inch - (pdf_y / self.POINTS_PER_INCH)
        
        # Asumir ~0.2 inches por línea (aproximado)
        LINE_HEIGHT_ESTIMATE = 0.2
        paragraph_index = int(docx_y / LINE_HEIGHT_ESTIMATE)
        
        return max(0, paragraph_index)
    
    def is_in_same_line(self, rect1: PDFRect, rect2: PDFRect, tolerance: float = 2.0) -> bool:
        """
        Determina si dos rectángulos están en la misma línea horizontal.
        
        Args:
            rect1, rect2: Rectángulos a comparar
            tolerance: Tolerancia en puntos
        """
        return abs(rect1.y0 - rect2.y0) < tolerance
    
    def is_in_same_column(self, rect1: PDFRect, rect2: PDFRect, tolerance: float = 5.0) -> bool:
        """
        Determina si dos rectángulos están en la misma columna vertical.
        """
        return abs(rect1.x0 - rect2.x0) < tolerance
