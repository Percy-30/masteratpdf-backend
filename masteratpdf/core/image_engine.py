import os
import fitz
from PIL import Image
import io
import concurrent.futures

def _save_image_worker(pdf_path, xref, img_path):
    """
    Worker seguro que abre su propia instancia para extraer
    """
    try:
        # Check existencia antes de abrir (doble check por overhead)
        if os.path.exists(img_path): return
        
        doc = fitz.open(pdf_path)
        pix = fitz.Pixmap(doc, xref)
        
        if pix.n - pix.alpha > 3:  # CMYK -> RGB
            pix = fitz.Pixmap(fitz.csRGB, pix)
            
        img_bytes = pix.tobytes("png")
        Image.open(io.BytesIO(img_bytes)).save(img_path)
        doc.close()
    except Exception as e:
        print(f"[WARN] Failed to save image {xref}: {e}")

def extract_images_with_metadata(pdf_path: str, output_folder: str):
    """
    Extrae imágenes y retorna metadatos + coordenadas.
    Versión Optimizada: Recolección secuencial + Guardado paralelo.
    """
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_data = []
    tasks = []
    
    # 1. Fase rápida: Recolección de metadatos (Solo lectura de estructura)
    for page_num, page in enumerate(doc):
        for img in page.get_image_info(xrefs=True):
            xref = img["xref"]
            bbox = img["bbox"]
            filename = f"image_p{page_num+1}_{xref}.png"
            img_path = os.path.join(output_folder, filename)
            
            image_data.append({
                'page': page_num,
                'bbox': bbox,
                'path': img_path,
                'xref': xref,
                'width': bbox[2]-bbox[0],
                'height': bbox[3]-bbox[1]
            })
            
            if not os.path.exists(img_path):
                tasks.append((pdf_path, xref, img_path))
                
    doc.close()
    
    # 2. Fase pesada: Guardado en paralelo (I/O + Decode)
    if tasks:
        # Usamos 8 workers para maximizar I/O throughput
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(_save_image_worker, *t) for t in tasks]
            concurrent.futures.wait(futures)
            
    return image_data

# Alias for backward compatibility
def extract_images(pdf_path: str, output_folder: str):
    data = extract_images_with_metadata(pdf_path, output_folder)
    return [d['path'] for d in data]