# Popopo
Test de Imaginologia

## Ejecución

Backend (FastAPI) + frontend (React/Vite). 

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
cd backend && ../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

O usar `./run.sh`.

Variables de entorno opcionales:
- `SECRET_KEY`
- `ADMIN_EMAILS` (coma separada, default admin@example.com)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `FRONTEND_URL`

Credenciales por defecto: admin@example.com / admin123
