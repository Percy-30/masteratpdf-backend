"""
MasterAtPDF: Figure Matcher
Asocia imágenes extraídas con sus captions detectados espacialmente.
"""

import math

class FigureMatcher:
    def __init__(self, vertical_threshold=50):
        self.vertical_threshold = vertical_threshold

    def match_figures(self, image_data, classified_blocks):
        """
        Asocia imágenes con bloques de texto (Captions).
        
        Args:
            image_data: List[dict] {'page', 'bbox', 'path', ...}
            classified_blocks: List[dict] {'bbox', 'label', 'text', 'page'}
        
        Returns:
            List[dict]: [{'image': img_data, 'caption': block_data}, ...]
        """
        matches = []
        
        # Agrupar por páginas
        images_by_page = {}
        for img in image_data:
            p = img['page']
            if p not in images_by_page: images_by_page[p] = []
            images_by_page[p].append(img)
            
        blocks_by_page = {}
        for blk in classified_blocks:
            p = blk.get('page', 0) # Asumimos que blocks tienen campo page
            if p not in blocks_by_page: blocks_by_page[p] = []
            blocks_by_page[p].append(blk)
            
        # Matching por página
        for page, images in images_by_page.items():
            blocks = blocks_by_page.get(page, [])
            captions = [b for b in blocks if "CAPTION" in b['label']]
            
            for img in images:
                best_caption = None
                min_dist = float('inf')
                
                img_rect = img['bbox'] # [x0, y0, x1, y1]
                img_bottom = img_rect[3]
                img_center_x = (img_rect[0] + img_rect[2]) / 2
                
                for cap in captions:
                    cap_rect = cap['bbox']
                    cap_top = cap_rect[1]
                    cap_center_x = (cap_rect[0] + cap_rect[2]) / 2
                    
                    # Distancia vertical (caption debajo de imagen)
                    v_dist = cap_top - img_bottom
                    
                    # Check 1: Está debajo?
                    if 0 < v_dist < self.vertical_threshold:
                        # Check 2: Alineación horizontal (centrado relativo)
                        # Permitir desviación de hasta 100 pts
                        if abs(img_center_x - cap_center_x) < 100:
                            if v_dist < min_dist:
                                min_dist = v_dist
                                best_caption = cap
                
                if best_caption:
                    matches.append({
                        'type': 'figure_with_caption',
                        'image': img,
                        'caption': best_caption,
                        'confidence': 1.0 if best_caption['label'] == 'CAPTION' else 0.7
                    })
                    # Eliminar caption usado para evitar duplicados? 
                    # Idealmente sí, pero una imagen podría tener varios subcaptions.
                    # Por ahora simple greedy.
                    
        return matches
