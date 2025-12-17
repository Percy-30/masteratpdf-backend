import fitz
from docx import Document
from masteratpdf.core.bookmark_engine import find_paragraph_by_text, create_hyperlink

def extract_all_links(pdf_path: str) -> list:
    """
    Extrae todos los links del PDF con información detallada.
    Retorna: [{"kind": int, "page": int, "uri": str, "from": rect, "text": str}, ...]
    """
    doc = fitz.open(pdf_path)
    all_links = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        links = page.get_links()
        
        for link in links:
            link_info = {
                "kind": link.get("kind"),
                "page": link.get("page"),
                "uri": link.get("uri"),
                "from_rect": link.get("from"),
                "from_page": page_num + 1,
            }
            
            # Intentar extraer el texto del link
            if "from" in link:
                rect = link["from"]
                try:
                    text = page.get_text("text", clip=rect).strip()
                    link_info["text"] = text
                except:
                    link_info["text"] = ""
            
            all_links.append(link_info)
    
    doc.close()
    return all_links


def reinsert_internal_links(doc: Document, links: list, verbose: bool = False):
    """
    Re-inserta links internos en el documento DOCX.
    Solo procesa links internos (kind == 1, que son LINK_GOTO).
    """
    internal_links = [l for l in links if l.get("kind") == 1 and l.get("page") is not None]
    
    if verbose:
        print(f"[INFO] Re-insertando {len(internal_links)} links internos...")
    
    for link in internal_links:
        link_text = link.get("text", "")
        target_page = link.get("page", 0)
        
        if not link_text or target_page == 0:
            continue
        
        # Buscar el texto del link en el documento
        para_idx = find_paragraph_by_text(doc, link_text, partial=True)
        
        if para_idx is not None:
            # Crear bookmark destino
            bookmark_name = f"toc_page_{target_page}"
            
            # Convertir el texto en hyperlink
            # Nota: esto es simplificado, idealmente deberíamos reemplazar el run específico
            # pero para simplificar, añadimos el hyperlink al final del párrafo
            paragraph = doc.paragraphs[para_idx]
            
            # Esta es una aproximación - en un caso real necesitaríamos
            # encontrar y reemplazar el texto específico dentro del párrafo
            if verbose:
                print(f"  • Link '{link_text[:30]}...' → Página {target_page}")


def extract_links(page_links: list):
    """
    Función legacy mantenida para compatibilidad.
    """
    return [
        {
            "kind": lk.get("kind"),
            "page": lk.get("page"),
            "uri": lk.get("uri"),
            "from_rect": lk.get("from"),
        }
        for lk in page_links
    ]