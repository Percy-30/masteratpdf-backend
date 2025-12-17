"""
MasterAtPDF Engine: Structure Analyzer

Analiza la estructura del PDF para detectar automáticamente:
- Índices (general, figuras, tablas)
- Títulos y secciones
- Figuras con captions
- Tablas con títulos
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from .pdf_reader import Block


@dataclass
class IndexSection:
    """Representa una sección de índice detectada."""
    type: str  # 'general', 'figures', 'tables'
    start_page: int
    end_page: int
    entries: List[Tuple[str, int]]  # (text, page_number)


@dataclass
class DocumentElement:
    """Elemento estructural del documento."""
    type: str  # 'heading', 'paragraph', 'figure', 'table', 'index_entry'
    content: str
    page_number: int
    bbox: Tuple[float, float, float, float]
    level: Optional[int] = None  # Para headings
    number: Optional[str] = None  # Para figuras/tablas


class StructureAnalyzer:
    """
    Analiza la estructura del documento para extracción inteligente.
    
    Detecta automáticamente:
    - Dónde empiezan y terminan los índices
    - Qué son figuras, tablas, títulos
    - Jerarquía de secciones
    """
    
    # Patrones para detección
    PATTERNS = {
        'index_general': [
            r'^Índice\s*$',
            r'^ÍNDICE\s*$',
            r'^TABLE OF CONTENTS\s*$'
        ],
        'index_figures': [
            r'ÍNDICE\s+DE\s+FIGURAS',
            r'Índice\s+de\s+Figuras',
            r'LIST OF FIGURES'
        ],
        'index_tables': [
            r'ÍNDICE\s+DE\s+TABLAS',
            r'Índice\s+de\s+Tablas',
            r'LIST OF TABLES'
        ],
        'chapter': [
            r'^CAPITULO\s+[IVXLC]+',
            r'^CAPÍTULO\s+[IVXLC]+',
            r'^CHAPTER\s+\d+'
        ],
        'section': [
            r'^\d+\.\d+(?:\.\d+)?\s+',  # 1.1, 1.2.1, etc.
        ],
        'figure': [
            r'^Figura\s+\d+',
            r'^Figure\s+\d+',
            r'^Fig\.\s+\d+'
        ],
        'table': [
            r'^Tabla\s+\d+',
            r'^Table\s+\d+',
            r'^Cuadro\s+\d+'
        ]
    }
    
    def __init__(self, pdf_data: Dict):
        """
        Args:
            pdf_data: Output de PDFReader.read()
        """
        self.pdf_data = pdf_data
        self.pages = pdf_data['pages']
    
    def detect_index_sections(self) -> List[IndexSection]:
        """
        Detecta todas las secciones de índice en el documento.
        
        Returns:
            Lista de IndexSection encontradas
        """
        sections = []
        current_section = None
        
        for page in self.pages:
            for block in page['blocks']:
                if block.type != 'text':
                    continue
                
                text = self._extract_text_from_block(block)
                
                # Detectar inicio de índice
                index_type = self._detect_index_start(text)
                if index_type:
                    # Guardar sección anterior si existe
                    if current_section:
                        sections.append(current_section)
                    
                    # Iniciar nueva sección
                    current_section = IndexSection(
                        type=index_type,
                        start_page=page['number'],
                        end_page=page['number'],
                        entries=[]
                    )
                    continue
                
                # Detectar fin de índice
                if current_section and self._is_end_of_index(text):
                    current_section.end_page = page['number']
                    sections.append(current_section)
                    current_section = None
                    continue
                
                # Agregar entrada a índice actual
                if current_section:
                    entry = self._parse_index_entry(text, current_section.type)
                    if entry:
                        current_section.entries.append(entry)
                        current_section.end_page = page['number']
        
        # Agregar última sección si existe
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def detect_figures(self) -> List[DocumentElement]:
        """Detecta todas las figuras con sus captions."""
        figures = []
        
        for page in self.pages:
            for block in page['blocks']:
                if block.type != 'text':
                    continue
                
                text = self._extract_text_from_block(block)
                
                # Detectar caption de figura
                for pattern in self.PATTERNS['figure']:
                    match = re.match(pattern, text, re.IGNORECASE)
                    if match:
                        # Extraer número
                        num_match = re.search(r'\d+', text)
                        fig_num = num_match.group() if num_match else None
                        
                        figures.append(DocumentElement(
                            type='figure',
                            content=text,
                            page_number=page['number'],
                            bbox=block.bbox,
                            number=fig_num
                        ))
                        break
        
        return figures
    
    def detect_tables(self) -> List[DocumentElement]:
        """Detecta todas las tablas con sus títulos."""
        tables = []
        
        for page in self.pages:
            for block in page['blocks']:
                if block.type != 'text':
                    continue
                
                text = self._extract_text_from_block(block)
                
                # Detectar título de tabla
                for pattern in self.PATTERNS['table']:
                    match = re.match(pattern, text, re.IGNORECASE)
                    if match:
                        num_match = re.search(r'\d+', text)
                        table_num = num_match.group() if num_match else None
                        
                        tables.append(DocumentElement(
                            type='table',
                            content=text,
                            page_number=page['number'],
                            bbox=block.bbox,
                            number=table_num
                        ))
                        break
        
        return tables
    
    def detect_headings(self) -> List[DocumentElement]:
        """Detecta títulos y secciones del documento."""
        headings = []
        
        for page in self.pages:
            for block in page['blocks']:
                if block.type != 'text':
                    continue
                
                text = self._extract_text_from_block(block)
                
                # Detectar capítulos (nivel 1)
                for pattern in self.PATTERNS['chapter']:
                    if re.match(pattern, text, re.IGNORECASE):
                        headings.append(DocumentElement(
                            type='heading',
                            content=text,
                            page_number=page['number'],
                            bbox=block.bbox,
                            level=1
                        ))
                        break
                
                # Detectar secciones (nivel 2+)
                for pattern in self.PATTERNS['section']:
                    match = re.match(pattern, text)
                    if match:
                        # Contar puntos para determinar nivel
                        section_num = match.group().strip()
                        level = section_num.count('.') + 1
                        
                        headings.append(DocumentElement(
                            type='heading',
                            content=text,
                            page_number=page['number'],
                            bbox=block.bbox,
                            level=level
                        ))
                        break
        
        return headings
    
    def _extract_text_from_block(self, block: Block) -> str:
        """Extrae texto limpio de un bloque."""
        if block.type != 'text':
            return ""
        
        lines = block.content.get('lines', [])
        text_parts = []
        
        for line in lines:
            for span in line.get('spans', []):
                text_parts.append(span.get('text', ''))
        
        return ' '.join(text_parts).strip()
    
    def _detect_index_start(self, text: str) -> Optional[str]:
        """Detecta si un texto marca el inicio de un índice."""
        for pattern in self.PATTERNS['index_general']:
            if re.search(pattern, text, re.IGNORECASE):
                return 'general'
        
        for pattern in self.PATTERNS['index_figures']:
            if re.search(pattern, text, re.IGNORECASE):
                return 'figures'
        
        for pattern in self.PATTERNS['index_tables']:
            if re.search(pattern, text, re.IGNORECASE):
                return 'tables'
        
        return None
    
    def _is_end_of_index(self, text: str) -> bool:
        """Detecta si un texto marca el fin de un índice."""
        # Detectar capítulos o secciones principales
        if len(text) > 20:
            for pattern in self.PATTERNS['chapter']:
                if re.match(pattern, text, re.IGNORECASE):
                    return True
            
            # All-caps titles
            if re.match(r'^[A-ZÁÉÍÓÚÑ\s]{15,}$', text):
                return True
        
        return False
    
    def _parse_index_entry(self, text: str, index_type: str) -> Optional[Tuple[str, int]]:
        """
        Parsea una entrada de índice para extraer texto y página.
        
        Returns:
            (text, page_number) o None si no es una entrada válida
        """
        # Intentar extraer número de página
        # Formatos comunes: "... 25", "... Pág. 25", "....... 25"
        page_match = re.search(r'(?:Pág\.|Page|p\.)?\s*(\d+)\s*$', text, re.IGNORECASE)
        
        if page_match:
            page_num = int(page_match.group(1))
            # Limpiar texto (remover página y puntos)
            clean_text = re.sub(r'\.+\s*(?:Pág\.|Page|p\.)?\s*\d+\s*$', '', text, flags=re.IGNORECASE).strip()
            return (clean_text, page_num)
        
        return None
    
    def analyze(self) -> Dict:
        """
        Análisis completo del documento.
        
        Returns:
            {
                'indices': List[IndexSection],
                'figures': List[DocumentElement],
                'tables': List[DocumentElement],
                'headings': List[DocumentElement]
            }
        """
        return {
            'indices': self.detect_index_sections(),
            'figures': self.detect_figures(),
            'tables': self.detect_tables(),
            'headings': self.detect_headings()
        }
