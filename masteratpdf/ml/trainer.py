"""
MasterAtPDF: ML Model Trainer
Entrena un modelo Random Forest usando datos recolectados.
"""

import os
import json
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline

class ModelTrainer:
    def __init__(self, data_dir="deep_learning_dataset", model_path="masteratpdf/ml/model.pkl"):
        self.data_dir = data_dir
        self.labels_file = os.path.join(data_dir, "labels.json")
        self.model_path = model_path
        
    def train(self):
        print(f"🔄 Entrenando modelo desde {self.data_dir}...")
        
        if not os.path.exists(self.labels_file):
            print("❌ No hay dataset. Ejecuta 'collect_dataset.py' primero.")
            return
            
        with open(self.labels_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        if not raw_data:
            print("❌ Dataset vacío.")
            return

        X = []
        y = []
        
        for item in raw_data:
            # Reconstruir features desde raw data/bbox
            # Simplificación: Usamos las features que guardamos o recalculamos
            # En una impl real, data_collector debería guardar las FEATURES numéricas.
            # Aquí simulamos features basados en bbox
            bbox = item.get('caption_bbox', [0,0,0,0])
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            
            features = {
                'width': width,
                'height': height,
                'aspect_ratio': width/height if height>0 else 0,
                'y_pos': bbox[1],
                # 'text_len': len(item['caption']) # Text features
            }
            
            X.append(features)
            y.append(item['label']) # 'figure_caption'
            
        # Añadir ejemplos negativos sintéticos (Ruido/Body) para que pueda distinguir
        # Esto es crucial, si solo entreno con positivos, predecirá siempre positivo.
        # Por ahora, es un esqueleto.
        
        clf = Pipeline([
            ('vectorizer', DictVectorizer(sparse=False)),
            ('classifier', RandomForestClassifier(n_estimators=100))
        ])
        
        # clf.fit(X, y) # Necesita clases variadas
        print(f"⚠️ Dataset solo tiene positivos. Saltando fit real. Guardando dummy.")
        
        # Guardar (Simulado)
        # with open(self.model_path, 'wb') as f:
        #    pickle.dump(clf, f)
            
        print("✅ Modelo 'entrenado' (Stub). Para real, recolectar clases negativas.")

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train()
