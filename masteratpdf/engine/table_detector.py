"""
MasterAtPDF: Table Detector

Detecta tablas en PDF usando análisis visual con OpenCV.
Mucho más preciso que métodos basados en texto.
"""

import fitz
import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TableRegion:
    """Región donde se detectó una tabla."""
    x: float
    y: float
    width: float
    height: float
    page_num: int
    
    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Bounding box en formato PyMuPDF (x0, y0, x1, y1)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    @property
    def area(self) -> float:
        """Área de la región."""
        return self.width * self.height


class TableDetector:
    """
    Detector de tablas basado en visión por computadora.
    
    Estrategia:
    1. Renderizar página como imagen
    2. Detectar líneas horizontales y verticales (bordes de tabla)
    3. Encontrar intersecciones que forman celdas
    4. Agrupar celdas en tablas completas
    """
    
    def __init__(self, dpi: int = 300):
        """
        Args:
            dpi: Resolución para renderizar PDF (mayor = más preciso)
        """
        self.dpi = dpi
    
    def detect_tables_in_page(self, page: fitz.Page) -> List[TableRegion]:
        """
        Detecta todas las tablas en una página.
        
        Args:
            page: Página de PyMuPDF
            
        Returns:
            Lista de regiones de tabla detectadas
        """
        
        # Renderizar página como imagen
        pix = page.get_pixmap(dpi=self.dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8)
        img = img.reshape(pix.height, pix.width, pix.n)
        
        # Convertir RGB a BGR (OpenCV usa BGR)
        if pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        elif pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        
        # Detectar tablas
        tables = self._detect_tables_in_image(img, page.number)
        
        # Convertir coordenadas de imagen a PDF
        scale_x = page.rect.width / pix.width
        scale_y = page.rect.height / pix.height
        
        for table in tables:
            table.x *= scale_x
            table.y *= scale_y
            table.width *= scale_x
            table.height *= scale_y
        
        return tables
    
    def _detect_tables_in_image(self, img: np.ndarray, page_num: int) -> List[TableRegion]:
        """Detecta tablas en imagen usando detección de líneas."""
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Binarizar
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Detectar bordes
        edges = cv2.Canny(binary, 50, 150, apertureSize=3)
        
        # Detectar líneas horizontales
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Detectar líneas verticales
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Combinar líneas para formar grid de tabla
        table_mask = cv2.add(horizontal_lines, vertical_lines)
        
        # Dilatar para conectar líneas cercanas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        table_mask = cv2.dilate(table_mask, kernel, iterations=3)
        
        # Encontrar contornos (estas son nuestras tablas)
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar contornos para obtener solo tablas válidas
        tables = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filtrar regiones muy pequeñas (no son tablas)
            if w < 100 or h < 50:
                continue
            
            # Filtrar regiones muy grandes (probablemente toda la página)
            if w > img.shape[1] * 0.95 or h > img.shape[0] * 0.95:
                continue
            
            # Verificar que tenga aspecto de tabla (más ancho que alto generalmente)
            aspect_ratio = w / h
            if aspect_ratio < 0.3 or aspect_ratio > 10:
                continue
            
            tables.append(TableRegion(
                x=float(x),
                y=float(y),
                width=float(w),
                height=float(h),
                page_num=page_num
            ))
        
        # Ordenar por posición vertical (top -> bottom)
        tables.sort(key=lambda t: t.y)
        
        return tables
    
    def detect_tables_in_document(self, pdf_path: str) -> List[TableRegion]:
        """
        Detecta todas las tablas en un documento PDF.
        
        Args:
            pdf_path: Ruta al PDF
            
        Returns:
            Lista de todas las tablas detectadas en el documento
        """
        
        pdf_doc = fitz.open(pdf_path)
        all_tables = []
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            tables = self.detect_tables_in_page(page)
            all_tables.extend(tables)
        
        pdf_doc.close()
        
        return all_tables


if __name__ == "__main__":
    # Test rápido
    pdf_path = "d:/PROYECTOS/PYTHON/masteratpdf-backend/tesis.pdf"
    
    print("🔍 Detectando tablas en tesis.pdf...")
    
    detector = TableDetector(dpi=300)
    tables = detector.detect_tables_in_document(pdf_path)
    
    print(f"\n✅ Detectadas {len(tables)} tablas:")
    for i, table in enumerate(tables[:10], 1):
        print(f"  {i}. Página {table.page_num + 1}: {table.width:.1f}x{table.height:.1f} @ ({table.x:.1f}, {table.y:.1f})")
    
    if len(tables) > 10:
        print(f"  ... y {len(tables) - 10} más")
