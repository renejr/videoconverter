"""
Endpoints da API v1
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os endpoints REST organizados por funcionalidade.
"""

# Importações dos routers de cada endpoint
from .users import router as users_router
from .auth import router as auth_router

__all__ = [
    "users_router",
    "auth_router"
]