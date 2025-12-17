"""
MasterAtPDF Engine: Performance Optimizer

Optimizaciones de performance para procesamiento rápido.
"""

from multiprocessing import Pool, cpu_count
from functools import lru_cache
from typing import List, Callable, Any
import time
import logging

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    Optimizaciones de performance.
    
    Características:
    - Procesamiento paralelo de páginas
    - Caché de resultados
    - Batch processing
    """
    
    @staticmethod
    def parallel_process_pages(pages: List, process_func: Callable, 
                               max_workers: int = None) -> List:
        """
        Procesa páginas en paralelo.
        
        Args:
            pages: Lista de páginas a procesar
            process_func: Función para procesar cada página
            max_workers: Número de workers (default: CPU count)
            
        Returns:
            Lista de resultados
        """
        if max_workers is None:
            max_workers = max(1, cpu_count() - 1)  # Dejar 1 CPU libre
        
        logger.info(f"Procesamiento paralelo: {len(pages)} páginas, {max_workers} workers")
        
        start = time.time()
        
        with Pool(max_workers) as pool:
            results = pool.map(process_func, pages)
        
        elapsed = time.time() - start
        logger.info(f"Procesamiento completado en {elapsed:.2f}s")
        
        return results
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def cached_text_normalize(text: str) -> str:
        """
        Normalización de texto con caché.
        Evita procesar el mismo texto múltiples veces.
        """
        import re
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def batch_process(items: List[Any], batch_size: int, 
                     process_func: Callable) -> List:
        """
        Procesa items en batches para mejor uso de memoria.
        
        Args:
            items: Items a procesar
            batch_size: Tamaño de batch
            process_func: Función para procesar batch
            
        Returns:
            Lista de resultados
        """
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = process_func(batch)
            results.extend(batch_results)
        
        return results


class PerformanceMonitor:
    """Monitor de performance para profiling."""
    
    def __init__(self):
        self.timings = {}
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        logger.info(f"Tiempo total: {elapsed:.2f}s")
    
    def time_section(self, name: str):
        """Context manager para medir secciones."""
        class SectionTimer:
            def __init__(self, monitor, section_name):
                self.monitor = monitor
                self.name = section_name
            
            def __enter__(self):
                self.start = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.time() - self.start
                self.monitor.timings[self.name] = elapsed
                logger.debug(f"{self.name}: {elapsed:.2f}s")
        
        return SectionTimer(self, name)
    
    def print_report(self):
        """Imprime reporte de tiempos."""
        print("\n⏱️  Performance Report:")
        for name, duration in sorted(self.timings.items(), key=lambda x: x[1], reverse=True):
            print(f"  {name}: {duration:.2f}s")
