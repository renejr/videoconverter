"""
Serviço de Usuários - User Service
Sistema de Identidade e Transações - Domínio A

Este módulo contém a lógica de negócio para
operações relacionadas aos usuários.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from passlib.context import CryptContext
import secrets

from models.user import User
from models.credential import Credential
from schemas.user import (
    UserCreateSchema,
    UserUpdateSchema,
    UserSearchSchema,
    UserStatsSchema
)
from api.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    InactiveUserError,
    BusinessRuleError
)
from utils.validators import validate_cpf, validate_cnpj, validate_email, validate_phone
from utils.formatters import format_cpf, format_cnpj, format_phone

# Configuração para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """
    Serviço para gerenciamento de usuários
    
    Este serviço contém toda a lógica de negócio relacionada
    aos usuários, incluindo criação, atualização, busca e validações.
    """
    
    def __init__(self):
        """
        Inicializa o serviço de usuários
        """
        self.pwd_context = pwd_context
    
    async def create_user(
        self,
        db: Session,
        user_data: UserCreateSchema,
        created_by_id: Optional[int] = None
    ) -> User:
        """
        Cria um novo usuário
        
        Args:
            db: Sessão do banco de dados
            user_data: Dados do usuário a ser criado
            created_by_id: ID do usuário que está criando (para auditoria)
            
        Returns:
            User: Usuário criado
            
        Raises:
            UserAlreadyExistsError: Se o usuário já existir
            BusinessRuleError: Se houver violação de regra de negócio
        """
        # Verificar se email já existe
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise UserAlreadyExistsError(f"Email {user_data.email} já está em uso")
        
        # Verificar se CPF já existe (se fornecido)
        formatted_cpf = None
        if hasattr(user_data, 'cpf') and user_data.cpf:
            # Validar formato do CPF
            if not validate_cpf(user_data.cpf):
                raise BusinessRuleError("CPF inválido")
            
            # Formatar CPF
            formatted_cpf = format_cpf(user_data.cpf)
            
            # Verificar se CPF já existe (assumindo que o modelo User tem campo cpf)
            # Como o modelo atual não tem CPF, vamos pular esta verificação por enquanto
        
        # Validar telefone (se fornecido)
        formatted_phone = None
        if user_data.phone:
            if not validate_phone(user_data.phone):
                raise BusinessRuleError("Telefone inválido")
            formatted_phone = format_phone(user_data.phone)
        
        # Gerar salt e hash da senha
        salt = secrets.token_hex(32)
        hashed_password = self.pwd_context.hash(user_data.password)
        
        # Criar usuário
        new_user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=formatted_phone,
            date_of_birth=getattr(user_data, 'date_of_birth', None),
            country_code=getattr(user_data, 'country', 'BR'),
            language_preference=getattr(user_data, 'language', 'pt-BR'),
            timezone=getattr(user_data, 'timezone', 'America/Sao_Paulo'),
            is_active=True,
            is_verified=False
        )
        
        db.add(new_user)
        db.flush()  # Para obter o ID do usuário
        
        # Criar credencial
        new_credential = Credential(
            user_id=new_user.id,
            password_hash=hashed_password,
            salt=salt,
            failed_login_attempts=0,
            two_factor_enabled=False
        )
        
        db.add(new_credential)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    async def get_user_by_id(self, db: Session, user_id: int) -> User:
        """
        Busca usuário por ID
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário encontrado
            
        Raises:
            UserNotFoundError: Se usuário não for encontrado
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(f"Usuário com ID {user_id} não encontrado")
        
        return user
    
    async def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Busca usuário por email incluindo credencial
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            
        Returns:
            Optional[User]: Usuário encontrado ou None (com credencial carregada)
        """
        from sqlalchemy.orm import joinedload
        return db.query(User).options(joinedload(User.credential)).filter(User.email == email).first()
    
    async def update_user(
        self,
        db: Session,
        user_id: int,
        user_data: UserUpdateSchema,
        updated_by_id: Optional[int] = None
    ) -> User:
        """
        Atualiza dados do usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário a ser atualizado
            user_data: Dados para atualização
            updated_by_id: ID do usuário que está atualizando
            
        Returns:
            User: Usuário atualizado
            
        Raises:
            UserNotFoundError: Se usuário não for encontrado
            UserAlreadyExistsError: Se email ou CPF já existir
            BusinessRuleError: Se houver violação de regra de negócio
        """
        # Buscar usuário
        user = await self.get_user_by_id(db, user_id)
        
        # Verificar se email já existe (se sendo alterado)
        if user_data.email and user_data.email != user.email:
            existing_user = db.query(User).filter(
                and_(User.email == user_data.email, User.id != user_id)
            ).first()
            if existing_user:
                raise UserAlreadyExistsError(f"Email {user_data.email} já está em uso")
        
        # Verificar se CPF já existe (se sendo alterado)
        if user_data.cpf and user_data.cpf != user.cpf:
            if not validate_cpf(user_data.cpf):
                raise BusinessRuleError("CPF inválido")
            
            formatted_cpf = format_cpf(user_data.cpf)
            existing_cpf = db.query(User).filter(
                and_(User.cpf == formatted_cpf, User.id != user_id)
            ).first()
            if existing_cpf:
                raise UserAlreadyExistsError(f"CPF {formatted_cpf} já está em uso")
        
        # Validar telefone (se fornecido)
        if user_data.phone:
            if not validate_phone(user_data.phone):
                raise BusinessRuleError("Telefone inválido")
            user_data.phone = format_phone(user_data.phone)
        
        # Atualizar campos
        update_data = user_data.dict(exclude_unset=True)
        
        # Formatar CPF se fornecido
        if "cpf" in update_data and update_data["cpf"]:
            update_data["cpf"] = format_cpf(update_data["cpf"])
        
        # Atualizar campos de auditoria
        update_data["updated_at"] = datetime.utcnow()
        update_data["updated_by_id"] = updated_by_id
        
        # Aplicar atualizações
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    async def deactivate_user(
        self,
        db: Session,
        user_id: int,
        deactivated_by_id: Optional[int] = None
    ) -> User:
        """
        Desativa um usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário a ser desativado
            deactivated_by_id: ID do usuário que está desativando
            
        Returns:
            User: Usuário desativado
            
        Raises:
            UserNotFoundError: Se usuário não for encontrado
        """
        user = await self.get_user_by_id(db, user_id)
        
        user.is_active = False
        user.deactivated_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        user.updated_by_id = deactivated_by_id
        
        db.commit()
        db.refresh(user)
        
        return user
    
    async def reactivate_user(
        self,
        db: Session,
        user_id: int,
        reactivated_by_id: Optional[int] = None
    ) -> User:
        """
        Reativa um usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário a ser reativado
            reactivated_by_id: ID do usuário que está reativando
            
        Returns:
            User: Usuário reativado
            
        Raises:
            UserNotFoundError: Se usuário não for encontrado
        """
        user = await self.get_user_by_id(db, user_id)
        
        user.is_active = True
        user.deactivated_at = None
        user.updated_at = datetime.utcnow()
        user.updated_by_id = reactivated_by_id
        
        db.commit()
        db.refresh(user)
        
        return user
    
    async def list_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        user_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        email_verified: Optional[bool] = None
    ) -> List[User]:
        """
        Lista usuários com filtros e paginação
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros para pular
            limit: Limite de registros por página
            search: Termo de busca (nome ou email)
            user_type: Filtro por tipo de usuário
            is_active: Filtro por status ativo
            email_verified: Filtro por email verificado
            
        Returns:
            List[User]: Lista de usuários
        """
        query = db.query(User)
        
        # Aplicar filtros
        if search:
            search_filter = or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if user_type:
            query = query.filter(User.user_type == user_type)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if email_verified is not None:
            query = query.filter(User.email_verified == email_verified)
        
        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(desc(User.created_at))
        
        # Aplicar paginação
        return query.offset(skip).limit(limit).all()
    
    async def search_users(
        self,
        db: Session,
        search_params: UserSearchSchema
    ) -> List[User]:
        """
        Busca avançada de usuários
        
        Args:
            db: Sessão do banco de dados
            search_params: Parâmetros de busca
            
        Returns:
            List[User]: Lista de usuários encontrados
        """
        query = db.query(User)
        
        # Aplicar filtros de busca
        if search_params.name:
            query = query.filter(User.full_name.ilike(f"%{search_params.name}%"))
        
        if search_params.email:
            query = query.filter(User.email.ilike(f"%{search_params.email}%"))
        
        if search_params.cpf:
            formatted_cpf = format_cpf(search_params.cpf)
            query = query.filter(User.cpf == formatted_cpf)
        
        if search_params.phone:
            formatted_phone = format_phone(search_params.phone)
            query = query.filter(User.phone == formatted_phone)
        
        if search_params.user_type:
            query = query.filter(User.user_type == search_params.user_type)
        
        if search_params.is_active is not None:
            query = query.filter(User.is_active == search_params.is_active)
        
        if search_params.email_verified is not None:
            query = query.filter(User.email_verified == search_params.email_verified)
        
        if search_params.created_after:
            query = query.filter(User.created_at >= search_params.created_after)
        
        if search_params.created_before:
            query = query.filter(User.created_at <= search_params.created_before)
        
        # Ordenar resultados
        if search_params.order_by:
            if search_params.order_by == "name":
                query = query.order_by(User.full_name)
            elif search_params.order_by == "email":
                query = query.order_by(User.email)
            elif search_params.order_by == "created_at":
                query = query.order_by(desc(User.created_at))
        else:
            query = query.order_by(desc(User.created_at))
        
        # Aplicar paginação
        return query.offset(search_params.skip).limit(search_params.limit).all()
    
    async def get_user_stats(self, db: Session) -> UserStatsSchema:
        """
        Obtém estatísticas dos usuários
        
        Args:
            db: Sessão do banco de dados
            
        Returns:
            UserStatsSchema: Estatísticas dos usuários
        """
        # Total de usuários
        total_users = db.query(func.count(User.id)).scalar()
        
        # Usuários ativos
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        
        # Usuários com email verificado
        verified_users = db.query(func.count(User.id)).filter(User.email_verified == True).scalar()
        
        # Usuários criados nos últimos 30 dias
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = db.query(func.count(User.id)).filter(
            User.created_at >= thirty_days_ago
        ).scalar()
        
        # Usuários por tipo
        user_types = db.query(
            User.user_type,
            func.count(User.id).label('count')
        ).group_by(User.user_type).all()
        
        user_types_dict = {user_type: count for user_type, count in user_types}
        
        return UserStatsSchema(
            total_users=total_users,
            active_users=active_users,
            inactive_users=total_users - active_users,
            verified_users=verified_users,
            unverified_users=total_users - verified_users,
            recent_users=recent_users,
            user_types=user_types_dict
        )
    
    async def verify_user_password(
        self,
        db: Session,
        user_id: int,
        password: str
    ) -> bool:
        """
        Verifica se a senha do usuário está correta
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            password: Senha a ser verificada
            
        Returns:
            bool: True se a senha estiver correta
            
        Raises:
            UserNotFoundError: Se usuário não for encontrado
        """
        user = await self.get_user_by_id(db, user_id)
        return self.pwd_context.verify(password, user.password_hash)
    
    async def update_user_password(
        self,
        db: Session,
        user_id: int,
        new_password: str,
        updated_by_id: Optional[int] = None
    ) -> User:
        """
        Atualiza a senha do usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            new_password: Nova senha
            updated_by_id: ID do usuário que está atualizando
            
        Returns:
            User: Usuário atualizado
            
        Raises:
            UserNotFoundError: Se usuário não for encontrado
        """
        user = await self.get_user_by_id(db, user_id)
        
        # Hash da nova senha
        hashed_password = self.pwd_context.hash(new_password)
        
        user.password_hash = hashed_password
        user.password_changed_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        user.updated_by_id = updated_by_id
        
        db.commit()
        db.refresh(user)
        
        return user