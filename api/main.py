"""
MasterAtPDF: API REST with FastAPI

Endpoint web para conversión PDF → DOCX
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os
from pathlib import Path
import shutil

# Import converter
# Import verified core module
import sys
# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from masteratpdf.core.docx_builder import build_docx_professional


# Crear app
app = FastAPI(
    title="MasterAtPDF API",
    description="Conversión PDF a DOCX de alta calidad con índices navegables",
    version="1.0.0"
)

# CORS para permitir requests desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint raíz - información de la API."""
    return {
        "name": "MasterAtPDF API",
        "version": "1.0.0",
        "description": "Conversión PDF → DOCX con índices navegables",
        "endpoints": {
            "/convert": "POST - Convierte PDF a DOCX",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API funcionando correctamente"}


@app.post("/convert")
async def convert_pdf_to_docx(file: UploadFile = File(...)):
    """
    Convierte PDF a DOCX con todas las características avanzadas.
    
    Args:
        file: Archivo PDF (multipart/form-data)
        
    Returns:
        Archivo DOCX descargable
    """
    
    # Validar que sea PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Guardar PDF subido
        pdf_path = os.path.join(temp_dir, file.filename)
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Generar nombre de salida
        output_filename = file.filename.replace('.pdf', '_converted.docx')
        output_path = os.path.join(temp_dir, output_filename)
        
        # Convertir
        # Convertir usando el engine profesional verificado
        build_docx_professional(pdf_path, output_path, verbose=True)
        
        # Devolver archivo
        return FileResponse(
            output_path,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=output_filename,
            background=None  # No eliminar hasta después de enviarlo
        )
        
    except Exception as e:
        # Limpiar en caso de error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Error en conversión: {str(e)}")
    
    finally:
        # Limpiar archivos temporales (después de un tiempo)
        # En producción, usar un cleanup job
        pass


if __name__ == "__main__":
    print("="*70)
    print("🚀 MasterAtPDF API Server")
    print("="*70)
    print("\n📡 Iniciando servidor en http://localhost:8000")
    print("\n📖 Documentación en http://localhost:8000/docs")
    print("\n🔧 Endpoints:")
    print("  • GET  /         - Info API")
    print("  • GET  /health   - Health check")
    print("  • POST /convert  - Convertir PDF → DOCX")
    print("\n💡 Ejemplo de uso:")
    print("  curl -X POST http://localhost:8000/convert \\")
    print("       -F 'file=@documento.pdf' \\")
    print("       --output documento.docx")
    print("\n" + "="*70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
