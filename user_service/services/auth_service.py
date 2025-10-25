"""
Serviço de Autenticação - User Service
Sistema de Identidade e Transações - Domínio A

Este módulo contém a lógica de negócio para
operações relacionadas à autenticação e autorização.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import time
import uuid
import secrets
import logging
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from models.user import User
from schemas.auth import LoginResponseSchema
from schemas.user import UserCreateSchema
from api.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    InactiveUserError,
    TokenExpiredError
)
from config.settings import settings
from services.user_service import UserService
from events.publisher import event_publisher

# Configurar logging
logger = logging.getLogger(__name__)

# Configuração para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Serviço para autenticação e autorização
    
    Este serviço contém toda a lógica de negócio relacionada
    à autenticação, autorização e gerenciamento de sessões.
    """
    
    def __init__(self):
        """
        Inicializa o serviço de autenticação
        """
        self.pwd_context = pwd_context
        self.user_service = UserService()
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria um token de acesso JWT
        
        Args:
            data: Dados a serem incluídos no token
            expires_delta: Tempo de expiração do token
            
        Returns:
            str: Token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica e decodifica um token JWT
        
        Args:
            token: Token JWT a ser verificado
            
        Returns:
            Dict[str, Any]: Dados decodificados do token
            
        Raises:
            TokenExpiredError: Se o token estiver expirado
            InvalidCredentialsError: Se o token for inválido
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError:
            raise InvalidCredentialsError("Token inválido")
    
    async def authenticate_user(
        self,
        db: Session,
        email: str,
        password: str,
        client_ip: str = None,
        user_agent: str = None
    ) -> LoginResponseSchema:
        """
        Autentica um usuário
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            password: Senha do usuário
            client_ip: IP do cliente
            user_agent: User agent do cliente
            
        Returns:
            LoginResponseSchema: Dados de autenticação
            
        Raises:
            InvalidCredentialsError: Se as credenciais forem inválidas
            InactiveUserError: Se o usuário estiver inativo
        """
        # Buscar usuário por email
        user = await self.user_service.get_user_by_email(db, email)
        if not user:
            raise InvalidCredentialsError("Email ou senha incorretos")
        
        # Verificar se a credencial existe
        if not user.credential:
            raise InvalidCredentialsError("Email ou senha incorretos")
        
        # Verificar senha
        if not self.pwd_context.verify(password, user.credential.password_hash):
            raise InvalidCredentialsError("Email ou senha incorretos")
        
        # Verificar se o usuário está ativo
        if not user.is_active:
            raise InactiveUserError("Usuário inativo")
        
        # Criar token de acesso
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        # Atualizar último login
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        db.commit()
        
        return LoginResponseSchema(
            access_token=access_token,
            refresh_token="",  # TODO: Implementar refresh token
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            session_id="",  # TODO: Implementar session_id
            requires_2fa=False
        )
    
    async def register_user(
        self,
        db: Session,
        user_data: UserCreateSchema,
        client_ip: str = None,
        user_agent: str = None
    ) -> User:
        """
        Registra um novo usuário
        
        Args:
            db: Sessão do banco de dados
            user_data: Dados do usuário
            client_ip: IP do cliente
            user_agent: User agent do cliente
            
        Returns:
            User: Usuário criado
        """
        # Criar usuário usando o UserService
        new_user = await self.user_service.create_user(db, user_data)
        
        # TODO: Enviar email de verificação
        
        return new_user

    async def register_and_authenticate_user(
        self,
        db: Session,
        user_data: UserCreateSchema,
        client_ip: str = None,
        user_agent: str = None
    ) -> LoginResponseSchema:
        """
        Registra um novo usuário e retorna tokens de autenticação
        
        Args:
            db: Sessão do banco de dados
            user_data: Dados do usuário
            client_ip: IP do cliente
            user_agent: User agent do cliente
            
        Returns:
            LoginResponseSchema: Dados de autenticação com tokens
        """
        # Registrar usuário
        new_user = await self.register_user(db, user_data, client_ip, user_agent)
        
        # Gerar tokens de acesso para o usuário recém-criado
        access_token = self.create_access_token(data={"sub": str(new_user.id)})
        # Criar refresh token com tempo de expiração maior
        refresh_token_expires = timedelta(days=30)  # 30 dias
        refresh_token = self.create_access_token(
            data={"sub": str(new_user.id), "type": "refresh"}, 
            expires_delta=refresh_token_expires
        )
        
        # TODO: Implementar criação de sessão do usuário
        # await self.create_user_session(
        #     db, new_user.id, access_token, client_ip, user_agent
        # )
        
        # Retornar resposta de login
        return LoginResponseSchema(
            user={
                "id": new_user.id,
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "full_name": new_user.full_name,
                "is_active": new_user.is_active,
                "is_verified": new_user.is_verified,
                "is_premium": new_user.is_premium,
                "profile_completion": new_user.profile_completion,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None
            },
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            session_id=f"session_{new_user.id}_{int(time.time())}",  # Gerar session_id temporário
            requires_2fa=False
        )
    
    async def get_current_user(self, db: Session, token: str) -> User:
        """
        Obtém o usuário atual baseado no token
        
        Args:
            db: Sessão do banco de dados
            token: Token JWT
            
        Returns:
            User: Usuário autenticado
            
        Raises:
            InvalidCredentialsError: Se o token for inválido
            UserNotFoundError: Se o usuário não for encontrado
        """
        # Verificar token
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise InvalidCredentialsError("Token inválido")
        
        # Buscar usuário
        user = await self.user_service.get_user_by_id(db, int(user_id))
        
        return user
    
    async def change_password(
        self,
        db: Session,
        user: User,
        current_password: str,
        new_password: str
    ) -> None:
        """
        Altera a senha do usuário
        
        Args:
            db: Sessão do banco de dados
            user: Usuário
            current_password: Senha atual
            new_password: Nova senha
            
        Raises:
            InvalidCredentialsError: Se a senha atual estiver incorreta
        """
        # Verificar senha atual
        if not self.pwd_context.verify(current_password, user.password_hash):
            raise InvalidCredentialsError("Senha atual incorreta")
        
        # Atualizar senha
        await self.user_service.update_user_password(db, user.id, new_password)
    
    async def request_password_reset(
        self, 
        db: Session, 
        email: str, 
        client_ip: str = None, 
        user_agent: str = None
    ) -> None:
        """
        Solicita reset de senha
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            client_ip: IP do cliente que fez a solicitação
            user_agent: User agent do cliente
        """
        # Buscar usuário
        user = await self.user_service.get_user_by_email(db, email)
        if not user:
            # Não revelar se o email existe ou não
            return
        
        # Gerar token de reset
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Token válido por 1 hora
        
        # TODO: Salvar token no banco de dados (implementar tabela de tokens)
        
        # Construir URL de reset
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
        
        # Publicar evento PASSWORD_RESET_REQUESTED
        try:
            correlation_id = str(uuid.uuid4())
            await event_publisher.publish_password_reset_requested(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                reset_token=reset_token,
                reset_url=reset_url,
                expires_at=expires_at,
                ip_address=client_ip,
                user_agent=user_agent,
                language_preference=user.language_preference or 'pt-BR',
                correlation_id=correlation_id
            )
            logger.info(f"Evento PASSWORD_RESET_REQUESTED publicado para usuário {user.id} (correlation_id: {correlation_id})")
        except Exception as e:
            logger.error(f"Erro ao publicar evento PASSWORD_RESET_REQUESTED para usuário {user.id}: {str(e)}")
            # Não falhar a solicitação por erro no evento
    
    async def reset_password(self, db: Session, token: str, new_password: str) -> None:
        """
        Reseta a senha usando token
        
        Args:
            db: Sessão do banco de dados
            token: Token de reset
            new_password: Nova senha
        """
        # TODO: Implementar reset de senha com token
        pass
    
    async def request_email_verification(self, db: Session, email: str) -> None:
        """
        Solicita verificação de email
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
        """
        # Buscar usuário
        user = await self.user_service.get_user_by_email(db, email)
        if not user:
            # Não revelar se o email existe ou não
            return
        
        # Verificar se o email já está verificado
        if user.is_verified:
            return
        
        # Gerar token de verificação
        verification_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # Token válido por 24 horas
        
        # TODO: Salvar token no banco de dados (implementar tabela de tokens)
        
        # Construir URL de verificação
        verification_url = f"{settings.frontend_url}/verify-email?token={verification_token}"
        
        # Publicar evento EMAIL_VERIFICATION_REQUESTED
        try:
            correlation_id = str(uuid.uuid4())
            await event_publisher.publish_email_verification_requested(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                verification_token=verification_token,
                verification_url=verification_url,
                expires_at=expires_at,
                language_preference=user.language_preference or 'pt-BR',
                correlation_id=correlation_id
            )
            logger.info(f"Evento EMAIL_VERIFICATION_REQUESTED publicado para usuário {user.id} (correlation_id: {correlation_id})")
        except Exception as e:
            logger.error(f"Erro ao publicar evento EMAIL_VERIFICATION_REQUESTED para usuário {user.id}: {str(e)}")
            # Não falhar a solicitação por erro no evento
    
    async def verify_email(self, db: Session, token: str) -> None:
        """
        Verifica email usando token
        
        Args:
            db: Sessão do banco de dados
            token: Token de verificação
        """
        # TODO: Implementar verificação de email
        pass
    
    async def logout_user(self, db: Session, user_id: int, session_id: str = None) -> None:
        """
        Faz logout do usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            session_id: ID da sessão (opcional)
        """
        # TODO: Implementar logout com invalidação de sessão
        pass
    
    async def refresh_access_token(self, db: Session, refresh_token: str) -> LoginResponseSchema:
        """
        Renova token de acesso
        
        Args:
            db: Sessão do banco de dados
            refresh_token: Token de refresh
            
        Returns:
            LoginResponseSchema: Novos tokens
        """
        # TODO: Implementar refresh token
        raise NotImplementedError("Refresh token não implementado ainda")
    
    async def setup_two_factor(self, db: Session, user: User, method: str) -> dict:
        """
        Configura autenticação de dois fatores
        
        Args:
            db: Sessão do banco de dados
            user: Usuário
            method: Método de 2FA
            
        Returns:
            dict: Dados da configuração 2FA
        """
        # TODO: Implementar 2FA
        raise NotImplementedError("2FA não implementado ainda")
    
    async def verify_two_factor(self, db: Session, user: User, code: str) -> None:
        """
        Verifica código 2FA
        
        Args:
            db: Sessão do banco de dados
            user: Usuário
            code: Código 2FA
        """
        # TODO: Implementar verificação 2FA
        pass
    
    async def disable_two_factor(self, db: Session, user: User, password: str) -> None:
        """
        Desabilita 2FA
        
        Args:
            db: Sessão do banco de dados
            user: Usuário
            password: Senha do usuário
        """
        # TODO: Implementar desabilitação 2FA
        pass
    
    async def get_user_sessions(self, db: Session, user_id: int) -> list:
        """
        Obtém sessões do usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            list: Lista de sessões
        """
        # Por enquanto, retornamos uma sessão fictícia baseada no usuário atual
        # TODO: Implementar sistema completo de gerenciamento de sessões
        from datetime import datetime, timedelta
        
        current_time = datetime.utcnow()
        
        # Criar uma sessão fictícia para o usuário atual
        session_data = {
            "session_id": f"session_{user_id}_{int(current_time.timestamp())}",
            "device_id": f"device_{user_id}",
            "device_name": "Navegador Web",
            "device_type": "web",
            "ip_address": "127.0.0.1",
            "location": "Local",
            "is_current": True,
            "created_at": current_time,
            "last_activity": current_time,
            "expires_at": current_time + timedelta(hours=24)
        }
        
        return [session_data]
    
    async def revoke_session(self, db: Session, user_id: int, session_id: str) -> None:
        """
        Revoga uma sessão
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            session_id: ID da sessão
        """
        # TODO: Implementar revogação de sessão
        pass
    
    async def revoke_all_sessions(self, db: Session, user_id: int) -> None:
        """
        Revoga todas as sessões do usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
        """
        # TODO: Implementar revogação de todas as sessões
        pass
    
    async def get_security_events(self, db: Session, user_id: int) -> list:
        """
        Obtém eventos de segurança do usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            list: Lista de eventos de segurança
        """
        # TODO: Implementar log de eventos de segurança
        return []