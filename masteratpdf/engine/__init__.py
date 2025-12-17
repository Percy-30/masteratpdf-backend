"""MasterAtPDF Engine - Native PDF to DOCX conversion."""

from .pdf_reader import PDFReader, Block
from .coordinate_mapper import CoordinateMapper, PDFRect, DOCXPosition
from .structure_analyzer import StructureAnalyzer, IndexSection, DocumentElement
from .docx_writer import DOCXWriter
from .pipeline import ConversionPipeline

__all__ = [
    'PDFReader',
    'Block',
    'CoordinateMapper',
    'PDFRect',
    'DOCXPosition',
    'StructureAnalyzer',
    'IndexSection',
    'DocumentElement',
    'DOCXWriter',
    'ConversionPipeline',
]

