# Docker Deployment Guide 🐳

## Prerequisites
- Docker Engine installed.

## 1. Build Image

From the project root (where `Dockerfile` is located):

```bash
docker build -t masteratpdf:v1 .
```

This will:
- Use `python:3.10-slim` base.
- Install system libs (`libgl1`, `libglib`).
- Install Python dependencies (`requirements.txt`).
- Copy source code.

## 2. Run Container

Run the container exposing port 8000:

```bash
docker run -d -p 8000:8000 --name pdf-engine masteratpdf:v1
```

## 3. Environment Variables (Optional)

You can configure the engine using environment variables (planned feature):
- `MAX_WORKERS`: For parallel processing (default 4).
- `VERBOSE`: `true` or `false`.

```bash
docker run -d -p 8000:8000 -e VERBOSE=false masteratpdf:v1
```

## 4. Verify Deployment

Visit: `http://localhost:8000/docs` to see the auto-generated Swagger UI.

## 5. Production Notes

- **Volume Mapping**: For analyzing large files or saving logs, map a volume:
  ```bash
  docker run -v $(pwd)/logs:/app/logs masteratpdf:v1
  ```
- **Resources**: PDF conversion is CPU and RAM intensive. Ensure the container has access to at least 2 CPUs and 4GB RAM for optimal performance on large files (>100 pages).
