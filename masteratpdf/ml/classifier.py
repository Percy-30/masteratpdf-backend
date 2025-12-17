"""
MasterAtPDF: Structure Classifier
Clasifica bloques de PDF usando reglas heurísticas (y posteriormente ML).
"""

from .feature_extractor import FeatureExtractor

class StructureClassifier:
    def __init__(self, model_path=None):
        self.feature_extractor = FeatureExtractor()
        self.model = None
        if model_path and os.path.exists(model_path):
            try:
                import pickle
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print("🧠 Modelo ML cargado exitosamente.")
            except Exception as e:
                print(f"⚠️ Error cargando modelo ML: {e}")

    def classify_block(self, block, page_width, page_height, avg_body_size=11):
        """
        Clasifica un bloque en: BODY, TITLE, CAPTION, HEADER, FOOTER
        """
        features = self.feature_extractor.extract_features(block, page_width, page_height)
        
        # Reglas Heurísticas
        
        # 1. HEADER / FOOTER (Posición vertical extrema)
        if features['normalized_y'] < 0.05:
            return "HEADER"
        if features['normalized_y'] > 0.93:
            return "FOOTER"
            
        # 2. CAPTION (Empieza con Figura/Tabla, tamaño pequeño, centrado)
        # Excluir entradas de índice (contienen "...")
        text_preview = block.get('lines', [{}])[0].get('spans', [{}])[0].get('text', '')
        has_dots = '...' in text_preview or '......' in text_preview
        
        if (features['starts_figure'] or features['starts_table']) and not has_dots:
            # Verificar tamaño: usualmente menor o igual al body
            if features['avg_font_size'] <= avg_body_size + 1:
                return "CAPTION"
                
        # 3. TITLE (Fuente grande, negrita, centrado)
        if features['avg_font_size'] > avg_body_size * 1.2 and features['is_bold']:
            return "TITLE"
            
        # 4. CAPTION (Sin keyword pero centrado y pequeño debajo de imagen - TODO: necesita contexto de imagen)
        if features['is_centered'] and features['avg_font_size'] < avg_body_size and features['word_count'] < 20:
            return "POTENTIAL_CAPTION"
            
        # Default
        return "BODY"

    def predict_page(self, page_blocks, page_width, page_height):
        """
        Clasifica todos los bloques de una página.
        """
        # Calcular tamaño fuente promedio del cuerpo (moda)
        all_sizes = []
        for b in page_blocks:
            for l in b.get('lines', []):
                for s in l['spans']:
                    all_sizes.append(s['size'])
        
        avg_body_size = max(set(all_sizes), key=all_sizes.count) if all_sizes else 11
        
        results = []
        for block in page_blocks:
            label = self.classify_block(block, page_width, page_height, avg_body_size)
            results.append({
                'bbox': block['bbox'],
                'label': label,
                'text': block.get('lines', [{}])[0].get('spans', [{}])[0].get('text', '')[:20] + "..."
            })
            
        return results
