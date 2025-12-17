# MasterAtPDF API - Client Example

## Test API con curl

```bash
# Health check
curl http://localhost:8000/health

# Convertir PDF
curl -X POST http://localhost:8000/convert \
     -F 'file=@tesis.pdf' \
     --output tesis_converted.docx
```

## Test con Python

```python
import requests

url = "http://localhost:8000/convert"

with open("tesis.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)
    
with open("output.docx", "wb") as f:
    f.write(response.content)
```

## Frontend JavaScript

```javascript
// Upload PDF
const formData = new FormData();
formData.append('file', pdfFile);

fetch('http://localhost:8000/convert', {
  method: 'POST',
  body: formData
})
.then(res => res.blob())
.then(blob => {
  // Download DOCX
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'converted.docx';
  a.click();
});
```

## Iniciar servidor

```bash
cd d:/PROYECTOS/PYTHON/masteratpdf-backend
python api/main.py
```

API disponible en: http://localhost:8000
Documentación: http://localhost:8000/docs
