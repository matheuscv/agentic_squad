from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.usuarios import router as usuarios_router
from app.routers.contatos import router as contatos_router

app = FastAPI(
    title="API Manutenção de Contatos",
    version="1.0.0",
    description="Backend para gerenciamento de contatos de clientes.",
)

# CORS: permite apenas a origem do frontend em desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers de autenticação e usuários (TASK-03)
app.include_router(auth_router)
app.include_router(usuarios_router)

app.include_router(contatos_router)


@app.get("/", tags=["health"])
def health_check():
    """Endpoint de verificação de saúde da API."""
    return {"status": "ok", "version": app.version}
