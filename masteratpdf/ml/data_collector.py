"""
MasterAtPDF: Data Collector
Recolecta pares de Imagen-Caption para entrenamiento de Deep Learning.
"""

import os
import json
import shutil
from PIL import Image

class DataCollector:
    def __init__(self, output_dir="training_data"):
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        self.labels_file = os.path.join(output_dir, "labels.json")
        
        os.makedirs(self.images_dir, exist_ok=True)
        self.dataset = []
        
    def collect_pair(self, image_data, caption_block, label="figure_caption"):
        """
        Guarda un par imagen-caption.
        Args:
            image_data: dict con path, bbox, etc.
            caption_block: dict con text, bbox.
        """
        # Generar ID único
        img_filename = os.path.basename(image_data['path'])
        saved_img_path = os.path.join(self.images_dir, img_filename)
        
        # Copiar imagen si no existe
        if not os.path.exists(saved_img_path):
            shutil.copy2(image_data['path'], saved_img_path)
            
        entry = {
            "image_file": img_filename,
            "caption": caption_block['text'],
            "caption_bbox": caption_block['bbox'],
            "image_bbox": image_data['bbox'],
            "page": image_data['page'],
            "label": label
        }
        
        self.dataset.append(entry)
        self._save_labels()
        
    def _save_labels(self):
        with open(self.labels_file, "w", encoding="utf-8") as f:
            json.dump(self.dataset, f, indent=2, ensure_ascii=False)
            
    def get_stats(self):
        return len(self.dataset)
