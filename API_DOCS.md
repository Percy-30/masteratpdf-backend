# API Documentation 🔌

## Base URL
`http://localhost:8000`

The API is built using **FastAPI** and supports asynchronous processing.

---

## Endpoints

### 1. Health Check
Checks if the service is running.

- **URL**: `/`
- **Method**: `GET`
- **Response**:
  ```json
  {"status": "ok", "service": "MasterAtPDF Engine"}
  ```

### 2. Convert PDF
Uploads a PDF and returns the converted DOCX file.

- **URL**: `/convert`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: The PDF file to convert (binary).
- **Response**: Binary stream (DOCX file).

**Example (cURL)**:
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/tesis.pdf" \
  --output thesis_converted.docx
```

**Example (Python)**:
```python
import requests

url = "http://localhost:8000/convert"
files = {'file': open('tesis.pdf', 'rb')}
response = requests.post(url, files=files)

with open('result.docx', 'wb') as f:
    f.write(response.content)
```

### 3. Analyze Structure (Upcoming)
Returns a JSON analysis of the PDF structure (indices, figures, tables).

- **URL**: `/analyze`
- **Method**: `POST`
- **Status**: *Beta / In Development*

---

## Error Handling

- **400 Bad Request**: Invalid file typ or corrupt PDF.
- **500 Internal Server Error**: Conversion engine failure. Logs are printed to stdout/Docker logs.
