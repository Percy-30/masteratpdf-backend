
from fastapi import FastAPI, UploadFile, File
import shutil
import os

app = FastAPI()

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    """
    Endpoint para convertir PDF a Word.
    """
    file_location = f"temp/{file.filename}"
    
    # Asegurar directorio temporal
    os.makedirs("temp", exist_ok=True)
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    # TODO: Llamar al pipeline de conversión (Core)
    
    return {"info": f"file '{file.filename}' processed"}
