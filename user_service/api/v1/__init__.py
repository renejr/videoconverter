"""
API v1 - Sistema de Identidade e Transações
Domínio A - Plataforma VOD

Este módulo contém a versão 1 da API REST para
gerenciamento de usuários, autenticação e transações.
"""

from .router import api_router

__all__ = ["api_router"]