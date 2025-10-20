"""
Router principal da API v1
Sistema de Identidade e Transações - Domínio A

Este módulo configura e organiza todos os routers
dos endpoints da API versão 1.
"""

from fastapi import APIRouter

from api.v1.endpoints.users import router as users_router
from api.v1.endpoints.auth import router as auth_router

# Router principal da API v1
api_router = APIRouter(prefix="/v1")

# Incluir routers dos endpoints
api_router.include_router(
    auth_router,
    tags=["authentication"]
)

api_router.include_router(
    users_router,
    tags=["users"]
)

# Endpoint de health check
@api_router.get(
    "/health",
    tags=["health"],
    summary="Health Check",
    description="Verifica se a API está funcionando corretamente"
)
async def health_check():
    """
    Endpoint de verificação de saúde da API
    
    Returns:
        dict: Status da API
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "user-service"
    }