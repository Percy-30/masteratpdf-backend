"""
MasterAtPDF: ML Feature Extractor
Extrae características visuales y geométricas de bloques de texto PDF
para su clasificación (Título, Cuerpo, Caption, Header, Footer).
"""

import fitz
import re
import numpy as np
from collections import Counter

class FeatureExtractor:
    def __init__(self):
        pass

    def extract_features(self, block, page_width, page_height):
        """
        Extrae vector de características de un bloque.
        Args:
            block: dict de PyMuPDF (get_text("dict")['blocks'][i])
            page_width: float
            page_height: float
        Returns:
            dict: Features
        """
        bbox = block['bbox']
        x0, y0, x1, y1 = bbox
        
        # Geometría básica
        width = x1 - x0
        height = y1 - y0
        aspect_ratio = width / height if height > 0 else 0
        normalized_width = width / page_width
        normalized_y = y0 / page_height
        
        # Análisis de texto y fuentes
        text_content = ""
        font_sizes = []
        font_names = []
        is_bold_flags = []
        
        lines = block.get('lines', [])
        for line in lines:
            for span in line['spans']:
                text = span['text']
                text_content += text + " "
                font_sizes.append(span['size'])
                font_names.append(span['font'])
                # Detect bold in font name (e.g. "Arial-Bold", "TimesNewRoman,Bold")
                is_bold_flags.append(self._is_font_bold(span['font']))
        
        text_content = text_content.strip()
        
        # Estadísticas de fuente
        avg_font_size = np.mean(font_sizes) if font_sizes else 0
        max_font_size = np.max(font_sizes) if font_sizes else 0
        
        # Densidad de bold
        bold_ratio = np.mean(is_bold_flags) if is_bold_flags else 0
        
        # Patrones de texto
        has_digit = bool(re.search(r'\d', text_content))
        starts_with_figure = bool(re.match(r'^(figura|figure|fig\.)', text_content, re.IGNORECASE))
        starts_with_table = bool(re.match(r'^(tabla|table|cuadro)', text_content, re.IGNORECASE))
        is_centered = self._is_centered(x0, x1, page_width)
        
        # Word count
        word_count = len(text_content.split())
        
        return {
            'normalized_y': normalized_y,      # Posición vertical
            'normalized_width': normalized_width, # Ancho relativo
            'avg_font_size': avg_font_size,    # Tamaño fuente
            'is_bold': float(bold_ratio > 0.5), # Es negrita?
            'is_centered': float(is_centered), # Está centrado?
            'starts_figure': float(starts_with_figure), # Es caption figura?
            'starts_table': float(starts_with_table),   # Es caption tabla?
            'word_count': word_count,          # Longitud
            'text_density': len(text_content) / (width * height) if (width * height) > 0 else 0
        }

    def _is_font_bold(self, font_name):
        name = font_name.lower()
        return 'bold' in name or 'black' in name or 'demi' in name

    def _is_centered(self, x0, x1, page_width, tolerance=0.1):
        center_x = (x0 + x1) / 2
        page_center = page_width / 2
        return abs(center_x - page_center) < (page_width * tolerance)
