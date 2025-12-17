"""
MasterAtPDF Engine: Conversion Pipeline

Orquesta el proceso completo de conversión PDF → DOCX.
"""

import logging
from typing import Dict
from pathlib import Path

from .pdf_reader import PDFReader
from .structure_analyzer import StructureAnalyzer
from .docx_writer import DOCXWriter

logger = logging.getLogger(__name__)


class ConversionPipeline:
    """
    Pipeline completo de conversión PDF → DOCX.
    
    Fases:
    1. Leer y parsear PDF (PDFReader)
    2. Analizar estructura (StructureAnalyzer)
    3. Construir DOCX (DOCXWriter)
    4. Insertar bookmarks
    5. Crear índices navegables
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        
        if verbose:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.WARNING)
    
    def convert(self, pdf_path: str, output_path: str) -> bool:
        """
        Convierte PDF a DOCX con calidad profesional.
        
        Args:
            pdf_path: Ruta del PDF de entrada
            output_path: Ruta del DOCX de salida
            
        Returns:
            True si la conversión fue exitosa
        """
        try:
            self._log("[INFO] 🚀 Iniciando conversión con Motor Nativo")
            self._log(f"[INFO] PDF: {pdf_path}")
            
            # ============================================
            # FASE 1: Leer PDF
            # ============================================
            self._log("[INFO] Paso 1/5: Leyendo PDF...")
            with PDFReader(pdf_path) as reader:
                pdf_data = reader.read()
            
            self._log(f"  ✓ {len(pdf_data['pages'])} páginas leídas")
            self._log(f"  ✓ {len(pdf_data['toc'])} entradas TOC")
            self._log(f"  ✓ {len(pdf_data['links'])} links")
            
            # ============================================
            # FASE 2: Analizar Estructura
            # ============================================
            self._log("[INFO] Paso 2/5: Analizando estructura...")
            analyzer = StructureAnalyzer(pdf_data)
            structure = analyzer.analyze()
            
            self._log(f"  ✓ {len(structure['indices'])} secciones de índice")
            self._log(f"  ✓ {len(structure['figures'])} figuras")
            self._log(f"  ✓ {len(structure['tables'])} tablas")
            self._log(f"  ✓ {len(structure['headings'])} títulos")
            
            # ============================================
            # FASE 3: Construir DOCX Base
            # ============================================
            self._log("[INFO] Paso 3/5: Construyendo DOCX...")
            writer = DOCXWriter()
            writer.write(pdf_data, output_path)
            
            self._log(f"  ✓ DOCX base creado")
            
            # ============================================
            # FASE 4: Insertar Bookmarks
            # ============================================
            self._log("[INFO] Paso 4/5: Insertando bookmarks...")
            self._insert_bookmarks(writer, structure)
            
            # ============================================
            # FASE 5: Hacer Índices Navegables
            # ============================================
            self._log("[INFO] Paso 5/5: Haciendo índices navegables...")
            self._make_indices_navigable(writer, structure)
            
            # Guardar final
            writer.doc.save(output_path)
            
            self._log(f"[SUCCESS] ✅ Conversión completada: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en conversión: {e}", exc_info=True)
            return False
    
    def _insert_bookmarks(self, writer: DOCXWriter, structure: Dict):
        """Inserta bookmarks en ubicaciones exactas."""
        bookmarks_added = 0
        
        # Bookmarks para figuras
        for fig in structure['figures']:
            para_idx = writer.find_paragraph_by_text(fig.content, min_similarity=0.5)
            if para_idx >= 0:
                bookmark_name = f"figura_{fig.number}" if fig.number else f"figura_{bookmarks_added}"
                writer.insert_bookmark(writer.doc.paragraphs[para_idx], bookmark_name)
                bookmarks_added += 1
        
        # Bookmarks para tablas
        for table in structure['tables']:
            para_idx = writer.find_paragraph_by_text(table.content, min_similarity=0.5)
            if para_idx >= 0:
                bookmark_name = f"tabla_{table.number}" if table.number else f"tabla_{bookmarks_added}"
                writer.insert_bookmark(writer.doc.paragraphs[para_idx], bookmark_name)
                bookmarks_added += 1
        
        # Bookmarks para headings
        for heading in structure['headings']:
            para_idx = writer.find_paragraph_by_text(heading.content, min_similarity=0.6)
            if para_idx >= 0:
                bookmark_name = f"heading_{heading.page_number}_{bookmarks_added}"
                writer.insert_bookmark(writer.doc.paragraphs[para_idx], bookmark_name)
                bookmarks_added += 1
        
        self._log(f"  ✓ {bookmarks_added} bookmarks insertados")
    
    def _make_indices_navigable(self, writer: DOCXWriter, structure: Dict):
        """Convierte entradas de índice en hyperlinks."""
        links_created = 0
        
        for index_section in structure['indices']:
            # Para cada índice, buscar y convertir entradas
            if index_section.type == 'figures':
                for entry_text, page_num in index_section.entries:
                    # Buscar entrada en documento
                    para_idx = writer.find_paragraph_by_text(entry_text, min_similarity=0.4)
                    if para_idx >= 0:
                        # Extraer número de figura
                        import re
                        match = re.search(r'\d+', entry_text)
                        if match:
                            fig_num = match.group()
                            bookmark = f"figura_{fig_num}"
                            writer.create_hyperlink(
                                writer.doc.paragraphs[para_idx],
                                entry_text,
                                bookmark
                            )
                            links_created += 1
            
            elif index_section.type == 'tables':
                for entry_text, page_num in index_section.entries:
                    para_idx = writer.find_paragraph_by_text(entry_text, min_similarity=0.4)
                    if para_idx >= 0:
                        import re
                        match = re.search(r'\d+', entry_text)
                        if match:
                            table_num = match.group()
                            bookmark = f"tabla_{table_num}"
                            writer.create_hyperlink(
                                writer.doc.paragraphs[para_idx],
                                entry_text,
                                bookmark
                            )
                            links_created += 1
        
        self._log(f"  ✓ {links_created} hyperlinks creados")
    
    def _log(self, message: str):
        """Helper para logging condicional."""
        if self.verbose:
            print(message)
