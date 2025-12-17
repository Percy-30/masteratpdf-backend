"""
MasterAtPDF Engine: Native PDF Reader

Reemplaza pdf2docx con un parser nativo que preserva TODA la estructura.
Mantiene coordenadas exactas para bookmarks precisos.
"""

import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Block:
    """Representa un bloque de contenido con posición exacta."""
    type: str  # 'text', 'image', 'vector'
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    content: Any
    page_number: int
    
    @property
    def x0(self):
        return self.bbox[0]
    
    @property
    def y0(self):
        return self.bbox[1]
    
    @property
    def x1(self):
        return self.bbox[2]
    
    @property
    def y1(self):
        return self.bbox[3]


class PDFReader:
    """
    Lee PDF manteniendo TODA la información estructural.
    
    Ventajas sobre pdf2docx:
    - Coordenadas exactas preservadas
    - No pierde información
    - Control total del parsing
    - Mapeo preciso PDF → DOCX
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None
        
    def __enter__(self):
        self.doc = fitz.open(self.pdf_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.doc:
            self.doc.close()
    
    def read(self) -> Dict:
        """
        Lee TODO el PDF preservando estructura.
        
        Returns:
            {
                "pages": List[PageData],
                "toc": List[Tuple],
                "metadata": Dict,
                "links": List[Dict]
            }
        """
        if not self.doc:
            raise RuntimeError("PDFReader must be used as context manager")
        
        logger.info(f"Reading PDF: {self.pdf_path} ({len(self.doc)} pages)")
        
        return {
            "pages": [self._read_page(page) for page in self.doc],
            "toc": self.doc.get_toc(),
            "metadata": dict(self.doc.metadata),
            "links": self._extract_all_links()
        }
    
    def _read_page(self, page: fitz.Page) -> Dict:
        """
        Lee una página completa con coordenadas exactas.
        
        Returns:
            {
                "number": int,
                "size": (width, height),
                "blocks": List[Block],
                "images": List[Dict],
                "links": List[Dict],
                "drawings": List[Dict]
            }
        """
        page_num = page.number + 1
        logger.debug(f"Reading page {page_num}")
        
        # Extraer bloques con diccionario completo
        text_dict = page.get_text("dict")
        blocks = self._extract_blocks_from_dict(text_dict, page_num)
        
        return {
            "number": page_num,
            "size": (page.rect.width, page.rect.height),
            "rotation": page.rotation,
            "blocks": blocks,
            "images": self._extract_images(page, page_num),
            "links": page.get_links() if hasattr(page, 'get_links') else [],
            "drawings": page.get_drawings() if hasattr(page, 'get_drawings') else []
        }
    
    def _extract_blocks_from_dict(self, text_dict: Dict, page_num: int) -> List[Block]:
        """
        Extrae bloques de texto con toda su información estructural.
        """
        blocks = []
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                # Preservar TODA la información del bloque
                blocks.append(Block(
                    type="text",
                    bbox=tuple(block["bbox"]),
                    content={
                        "lines": block.get("lines", []),
                        "number": block.get("number"),
                    },
                    page_number=page_num
                ))
            elif block.get("type") == 1:  # Image block
                blocks.append(Block(
                    type="image",
                    bbox=tuple(block["bbox"]),
                    content={
                        "image": block.get("image"),
                        "width": block.get("width"),
                        "height": block.get("height")
                    },
                    page_number=page_num
                ))
        
        return blocks
    
    def _extract_images(self, page: fitz.Page, page_num: int) -> List[Dict]:
        """Extrae imágenes con metadata completa."""
        images = []
        
        for img_info in page.get_image_info(xrefs=True):
            images.append({
                "xref": img_info.get("xref"),
                "bbox": img_info.get("bbox"),
                "width": img_info.get("width"),
                "height": img_info.get("height"),
                "page": page_num
            })
        
        return images
    
    def _extract_all_links(self) -> List[Dict]:
        """Extrae TODOS los links del documento."""
        all_links = []
        
        for page in self.doc:
            links = page.get_links()
            for link in links:
                link["from_page"] = page.number + 1
                all_links.append(link)
        
        return all_links
    
    def get_page_count(self) -> int:
        """Retorna número de páginas."""
        return len(self.doc) if self.doc else 0
    
    def get_text_blocks_on_page(self, page_num: int) -> List[Block]:
        """Helper: obtiene solo bloques de texto de una página."""
        if not self.doc or page_num < 1 or page_num > len(self.doc):
            return []
        
        page = self.doc[page_num - 1]
        text_dict = page.get_text("dict")
        return self._extract_blocks_from_dict(text_dict, page_num)
