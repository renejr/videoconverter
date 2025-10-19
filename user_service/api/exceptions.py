"""
Exceções customizadas para as APIs
Sistema de Identidade e Transações - Domínio A

Este módulo define exceções customizadas e handlers
para tratamento padronizado de erros nas APIs.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError
import logging

# Configuração de logging
logger = logging.getLogger(__name__)


class BaseAPIException(HTTPException):
    """Exceção base para todas as exceções da API"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class UserNotFoundError(BaseAPIException):
    """Exceção para usuário não encontrado"""
    
    def __init__(self, user_id: Optional[str] = None):
        detail = f"Usuário {user_id} não encontrado" if user_id else "Usuário não encontrado"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="USER_NOT_FOUND"
        )


class UserAlreadyExistsError(BaseAPIException):
    """Exceção para usuário já existente"""
    
    def __init__(self, field: str = "email"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Usuário com este {field} já existe",
            error_code="USER_ALREADY_EXISTS"
        )


class InvalidCredentialsError(BaseAPIException):
    """Exceção para credenciais inválidas"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            error_code="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"}
        )


class InactiveUserError(BaseAPIException):
    """Exceção para usuário inativo"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
            error_code="INACTIVE_USER"
        )


class EmailNotVerifiedError(BaseAPIException):
    """Exceção para email não verificado"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não verificado",
            error_code="EMAIL_NOT_VERIFIED"
        )


class InsufficientPermissionsError(BaseAPIException):
    """Exceção para permissões insuficientes"""
    
    def __init__(self, required_permission: Optional[str] = None):
        detail = "Permissões insuficientes"
        if required_permission:
            detail += f" - requer: {required_permission}"
        
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="INSUFFICIENT_PERMISSIONS"
        )


class TokenExpiredError(BaseAPIException):
    """Exceção para token expirado"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            error_code="TOKEN_EXPIRED",
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidTokenError(BaseAPIException):
    """Exceção para token inválido"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            error_code="INVALID_TOKEN",
            headers={"WWW-Authenticate": "Bearer"}
        )


class SessionExpiredError(BaseAPIException):
    """Exceção para sessão expirada"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada",
            error_code="SESSION_EXPIRED"
        )


class RateLimitExceededError(BaseAPIException):
    """Exceção para limite de requisições excedido"""
    
    def __init__(self, retry_after: Optional[int] = None):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Limite de requisições excedido",
            error_code="RATE_LIMIT_EXCEEDED",
            headers=headers
        )


class DatabaseError(BaseAPIException):
    """Exceção para erros de banco de dados"""
    
    def __init__(self, detail: str = "Erro interno do servidor"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR"
        )


class ValidationError(BaseAPIException):
    """Exceção para erros de validação"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        if field:
            detail = f"Erro de validação no campo '{field}': {detail}"
        
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )


class BusinessRuleError(BaseAPIException):
    """Exceção para violação de regras de negócio"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BUSINESS_RULE_VIOLATION"
        )


# Handlers de exceção
async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """
    Handler para exceções da API base
    
    Args:
        request: Objeto Request do FastAPI
        exc: Exceção capturada
        
    Returns:
        JSONResponse: Resposta JSON padronizada
    """
    logger.warning(
        f"API Exception: {exc.error_code} - {exc.detail} - "
        f"Path: {request.url.path} - Method: {request.method}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "status_code": exc.status_code
            }
        },
        headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler para erros de validação do Pydantic
    
    Args:
        request: Objeto Request do FastAPI
        exc: Exceção de validação
        
    Returns:
        JSONResponse: Resposta JSON padronizada
    """
    logger.warning(f"Validation Error: {exc.errors()} - Path: {request.url.path}")
    
    # Formatar erros de validação de forma mais amigável
    formatted_errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Dados de entrada inválidos",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "details": formatted_errors
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler para erros do SQLAlchemy
    
    Args:
        request: Objeto Request do FastAPI
        exc: Exceção do SQLAlchemy
        
    Returns:
        JSONResponse: Resposta JSON padronizada
    """
    logger.error(f"Database Error: {str(exc)} - Path: {request.url.path}")
    
    # Tratar diferentes tipos de erro do SQLAlchemy
    if isinstance(exc, IntegrityError):
        # Erro de integridade (chave duplicada, constraint violation, etc.)
        detail = "Violação de integridade dos dados"
        
        # Tentar extrair informação mais específica do erro
        error_msg = str(exc.orig).lower()
        if "duplicate entry" in error_msg:
            detail = "Registro duplicado"
        elif "foreign key constraint" in error_msg:
            detail = "Violação de chave estrangeira"
        elif "not null constraint" in error_msg:
            detail = "Campo obrigatório não informado"
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "INTEGRITY_ERROR",
                    "message": detail,
                    "status_code": status.HTTP_409_CONFLICT
                }
            }
        )
    
    # Outros erros do SQLAlchemy
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Erro interno do servidor",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler genérico para exceções não tratadas
    
    Args:
        request: Objeto Request do FastAPI
        exc: Exceção capturada
        
    Returns:
        JSONResponse: Resposta JSON padronizada
    """
    logger.error(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)} - "
        f"Path: {request.url.path} - Method: {request.method}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Erro interno do servidor",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        }
    )


# Função para registrar todos os handlers
def register_exception_handlers(app):
    """
    Registra todos os handlers de exceção na aplicação FastAPI
    
    Args:
        app: Instância da aplicação FastAPI
    """
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)