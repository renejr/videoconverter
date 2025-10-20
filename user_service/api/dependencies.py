"""
Dependências comuns para as APIs
Sistema de Identidade e Transações - Domínio A

Este módulo contém todas as dependências reutilizáveis
para injeção nas rotas da API FastAPI.
"""

from typing import Generator, Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging

from database.connection import get_database_session
from config.settings import settings
from models.user import User
from models.user_session import UserSession

# Configuração de logging
logger = logging.getLogger(__name__)

# Configuração do esquema de autenticação Bearer
security = HTTPBearer()


class AuthenticationError(HTTPException):
    """Exceção customizada para erros de autenticação"""
    def __init__(self, detail: str = "Não foi possível validar as credenciais"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Exceção customizada para erros de autorização"""
    def __init__(self, detail: str = "Permissões insuficientes"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def get_db() -> Generator[Session, None, None]:
    """
    Dependência para obter sessão do banco de dados
    
    Yields:
        Session: Sessão do SQLAlchemy
    """
    yield from get_database_session()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT de acesso
    
    Args:
        data: Dados a serem codificados no token
        expires_delta: Tempo de expiração customizado
        
    Returns:
        str: Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verifica e decodifica um token JWT
    
    Args:
        token: Token JWT a ser verificado
        
    Returns:
        dict: Payload decodificado do token
        
    Raises:
        AuthenticationError: Se o token for inválido
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Token inválido")
            
        return payload
        
    except JWTError as e:
        logger.warning(f"Erro ao verificar token JWT: {str(e)}")
        raise AuthenticationError("Token inválido")


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db)
) -> User:
    """
    Obtém o usuário atual baseado no token JWT
    
    Args:
        credentials: Credenciais Bearer do cabeçalho Authorization
        db: Sessão do banco de dados
        
    Returns:
        User: Usuário autenticado
        
    Raises:
        AuthenticationError: Se o token for inválido ou usuário não encontrado
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Token inválido")
    
    # Busca o usuário no banco de dados
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise AuthenticationError("Usuário não encontrado")
    
    # Verifica se o usuário está ativo
    if not user.is_active:
        raise AuthenticationError("Usuário inativo")
    
    # Verifica se a sessão ainda é válida
    session_id = payload.get("session_id")
    if session_id:
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).first()
        
        if not session or session.is_expired():
            raise AuthenticationError("Sessão expirada")
        
        # Atualiza última atividade da sessão
        session.update_last_activity()
        db.commit()
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Obtém o usuário atual e verifica se está ativo
    
    Args:
        current_user: Usuário atual
        
    Returns:
        User: Usuário ativo
        
    Raises:
        AuthenticationError: Se o usuário estiver inativo
    """
    if not current_user.is_active:
        raise AuthenticationError("Usuário inativo")
    
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Requer que o usuário atual seja administrador
    
    Args:
        current_user: Usuário atual
        
    Returns:
        User: Usuário administrador
        
    Raises:
        AuthorizationError: Se o usuário não for administrador
    """
    if not current_user.is_admin:
        raise AuthorizationError("Acesso restrito a administradores")
    
    return current_user


def require_verified_email(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Requer que o usuário tenha email verificado
    
    Args:
        current_user: Usuário atual
        
    Returns:
        User: Usuário com email verificado
        
    Raises:
        AuthorizationError: Se o email não estiver verificado
    """
    if not current_user.email_verified:
        raise AuthorizationError("Email não verificado")
    
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Obtém o usuário atual de forma opcional (para endpoints públicos)
    
    Args:
        credentials: Credenciais Bearer opcionais
        db: Sessão do banco de dados
        
    Returns:
        Optional[User]: Usuário autenticado ou None
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except AuthenticationError:
        return None


def rate_limit_dependency(request: Request) -> None:
    """
    Dependência para rate limiting básico
    
    Args:
        request: Objeto Request do FastAPI
        
    Raises:
        HTTPException: Se o limite de requisições for excedido
    """
    # Implementação básica de rate limiting
    # Em produção, usar Redis ou similar para armazenar contadores
    client_ip = request.client.host
    
    # Por enquanto, apenas log da requisição
    logger.info(f"Requisição de {client_ip} para {request.url.path}")
    
    # TODO: Implementar rate limiting real com Redis
    pass


def validate_pagination(
    page: int = 1,
    size: int = 10,
    max_size: int = 100
) -> tuple[int, int]:
    """
    Valida e normaliza parâmetros de paginação
    
    Args:
        page: Número da página (começa em 1)
        size: Tamanho da página
        max_size: Tamanho máximo permitido
        
    Returns:
        tuple[int, int]: Página e tamanho validados
        
    Raises:
        HTTPException: Se os parâmetros forem inválidos
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Número da página deve ser maior que 0"
        )
    
    if size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tamanho da página deve ser maior que 0"
        )
    
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tamanho da página não pode exceder {max_size}"
        )
    
    return page, size


def get_pagination_params(
    page: int = 1,
    size: int = 10
) -> tuple[int, int]:
    """
    Dependência para obter parâmetros de paginação validados
    
    Args:
        page: Número da página
        size: Tamanho da página
        
    Returns:
        tuple[int, int]: Página e tamanho validados
    """
    return validate_pagination(page, size)


# Aliases para facilitar o uso
CurrentUser = Annotated[User, Depends(get_current_active_user)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
AdminUser = Annotated[User, Depends(require_admin)]
VerifiedUser = Annotated[User, Depends(require_verified_email)]
DatabaseSession = Annotated[Session, Depends(get_db)]
PaginationParams = Annotated[tuple[int, int], Depends(get_pagination_params)]