"""
MasterAtPDF Engine: Text Matcher

Búsqueda de texto optimizada con fuzzy matching avanzado.
Mucho más preciso que búsqueda simple.
"""

from typing import Optional, List, Tuple
from difflib import SequenceMatcher
import re


class TextMatcher:
    """
    Motor de búsqueda de texto con múltiples estrategias.
    
    Estrategias:
    1. Exact match
    2. Normalized match (sin espacios/puntuación)
    3. Word-based similarity
    4. Fuzzy sequence matching
    5. Partial match
    """
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza texto para comparación."""
        # Lowercase
        text = text.lower()
        # Remover múltiples espacios
        text = re.sub(r'\s+', ' ', text)
        # Remover puntuación común
        text = re.sub(r'[.:;,!?(){}[\]]', '', text)
        # Strip
        return text.strip()
    
    @staticmethod
    def extract_words(text: str) -> set:
        """Extrae palabras significativas."""
        normalized = TextMatcher.normalize_text(text)
        words = set(normalized.split())
        # Filtrar palabras muy cortas
        return {w for w in words if len(w) > 2}
    
    @staticmethod
    def word_similarity(text1: str, text2: str) -> float:
        """
        Calcula similitud basada en palabras compartidas.
        
        Returns:
            Score 0-1 (1 = identical)
        """
        words1 = TextMatcher.extract_words(text1)
        words2 = TextMatcher.extract_words(text2)
        
        if not words1 or not words2:
            return 0.0
        
        common = words1 & words2
        return len(common) / len(words1)
    
    @staticmethod
    def sequence_similarity(text1: str, text2: str) -> float:
        """
        Calcula similitud de secuencia (Levenshtein-like).
        
        Returns:
            Score 0-1
        """
        norm1 = TextMatcher.normalize_text(text1)
        norm2 = TextMatcher.normalize_text(text2)
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    @staticmethod
    def combined_similarity(text1: str, text2: str) -> float:
        """
        Combina múltiples métricas para mejor precisión.
        
        Returns:
            Score 0-1
        """
        # Pesos para cada métrica
        word_sim = TextMatcher.word_similarity(text1, text2)
        seq_sim = TextMatcher.sequence_similarity(text1, text2)
        
        # Weighted average (palabras más importante)
        return (word_sim * 0.7) + (seq_sim * 0.3)
    
    @staticmethod
    def find_best_match(search_text: str, candidates: List[str], 
                       min_score: float = 0.6) -> Optional[int]:
        """
        Encuentra el mejor match en una lista de candidatos.
        
        Args:
            search_text: Texto a buscar
            candidates: Lista de textos candidatos
            min_score: Score mínimo para considerar match
            
        Returns:
            Índice del mejor match o None
        """
        best_idx = None
        best_score = min_score
        
        for idx, candidate in enumerate(candidates):
            score = TextMatcher.combined_similarity(search_text, candidate)
            if score > best_score:
                best_score = score
                best_idx = idx
        
        return best_idx
    
    @staticmethod
    def find_all_matches(search_text: str, candidates: List[str],
                        min_score: float = 0.6) -> List[Tuple[int, float]]:
        """
        Encuentra todos los matches por encima del threshold.
        
        Returns:
            Lista de (índice, score) ordenada por score descendente
        """
        matches = []
        
        for idx, candidate in enumerate(candidates):
            score = TextMatcher.combined_similarity(search_text, candidate)
            if score >= min_score:
                matches.append((idx, score))
        
        # Ordenar por score descendente
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    @staticmethod
    def partial_match(search_text: str, candidate: str, min_ratio: float = 0.8) -> bool:
        """
        Verifica si search_text está contenido parcialmente en candidate.
        
        Args:
            search_text: Texto a buscar
            candidate: Texto donde buscar
            min_ratio: Ratio mínimo de palabras que deben estar
            
        Returns:
            True si hay match parcial
        """
        search_words = TextMatcher.extract_words(search_text)
        candidate_words = TextMatcher.extract_words(candidate)
        
        if not search_words:
            return False
        
        common = search_words & candidate_words
        ratio = len(common) / len(search_words)
        
        return ratio >= min_ratio
