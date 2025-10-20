"""
Endpoints de Usuários - API v1
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os endpoints relacionados ao
gerenciamento de usuários (CRUD e operações especiais).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from api.dependencies import (
    DatabaseSession,
    CurrentUser,
    AdminUser,
    PaginationParams,
    rate_limit_dependency
)
from api.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    InsufficientPermissionsError,
    BusinessRuleError
)
from models.user import User
from schemas.user import (
    UserCreateSchema,
    UserUpdateSchema,
    UserResponseSchema,
    UserDetailSchema,
    UserListSchema,
    UserSearchSchema,
    UserStatsSchema,
    UserDeactivateSchema,
    UserReactivateSchema
)
from services.user_service import UserService

# Configuração do router
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(rate_limit_dependency)]
)

# Instância do serviço de usuários
user_service = UserService()


@router.post(
    "/",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo usuário",
    description="Cria um novo usuário no sistema com validação completa de dados"
)
async def create_user(
    user_data: UserCreateSchema,
    db: DatabaseSession
) -> UserResponseSchema:
    """
    Cria um novo usuário no sistema
    
    Args:
        user_data: Dados do usuário a ser criado
        db: Sessão do banco de dados
        
    Returns:
        UserResponseSchema: Dados do usuário criado
        
    Raises:
        UserAlreadyExistsError: Se email ou CPF já existir
        ValidationError: Se os dados forem inválidos
    """
    # Verificar se email já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise UserAlreadyExistsError("email")
    
    # Verificar se CPF já existe (se fornecido)
    if user_data.cpf:
        existing_cpf = db.query(User).filter(User.cpf == user_data.cpf).first()
        if existing_cpf:
            raise UserAlreadyExistsError("CPF")
    
    # Criar usuário usando o serviço
    new_user = await user_service.create_user(db, user_data)
    
    return UserResponseSchema.from_orm(new_user)


@router.get(
    "/me",
    response_model=UserDetailSchema,
    summary="Obter perfil do usuário logado",
    description="Retorna o perfil completo do usuário autenticado"
)
async def get_current_user_profile(
    current_user: CurrentUser
) -> UserDetailSchema:
    """
    Obtém o perfil completo do usuário autenticado
    
    Args:
        current_user: Usuário autenticado
        
    Returns:
        UserDetailSchema: Perfil completo do usuário
    """
    return UserDetailSchema.from_orm(current_user)


@router.get(
    "/{user_id}",
    response_model=UserDetailSchema,
    summary="Obter usuário por ID",
    description="Retorna os dados de um usuário específico (requer permissões)"
)
async def get_user_by_id(
    user_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
) -> UserDetailSchema:
    """
    Obtém um usuário específico por ID
    
    Args:
        user_id: ID do usuário
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        UserDetailSchema: Dados do usuário
        
    Raises:
        UserNotFoundError: Se o usuário não for encontrado
        InsufficientPermissionsError: Se não tiver permissão
    """
    # Verificar se é o próprio usuário ou se é admin
    if current_user.id != user_id and not current_user.is_admin:
        raise InsufficientPermissionsError("Acesso aos dados de outros usuários")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError(user_id)
    
    return UserDetailSchema.from_orm(user)


@router.put(
    "/{user_id}",
    response_model=UserResponseSchema,
    summary="Atualizar usuário",
    description="Atualiza os dados de um usuário específico"
)
async def update_user(
    user_id: str,
    user_data: UserUpdateSchema,
    current_user: CurrentUser,
    db: DatabaseSession
) -> UserResponseSchema:
    """
    Atualiza os dados de um usuário
    
    Args:
        user_id: ID do usuário
        user_data: Dados a serem atualizados
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        UserResponseSchema: Dados atualizados do usuário
        
    Raises:
        UserNotFoundError: Se o usuário não for encontrado
        InsufficientPermissionsError: Se não tiver permissão
        UserAlreadyExistsError: Se email/CPF já existir
    """
    # Verificar se é o próprio usuário ou se é admin
    if current_user.id != user_id and not current_user.is_admin:
        raise InsufficientPermissionsError("Alteração de dados de outros usuários")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError(user_id)
    
    # Verificar conflitos de email
    if user_data.email and user_data.email != user.email:
        existing_email = db.query(User).filter(
            and_(User.email == user_data.email, User.id != user_id)
        ).first()
        if existing_email:
            raise UserAlreadyExistsError("email")
    
    # Verificar conflitos de CPF
    if user_data.cpf and user_data.cpf != user.cpf:
        existing_cpf = db.query(User).filter(
            and_(User.cpf == user_data.cpf, User.id != user_id)
        ).first()
        if existing_cpf:
            raise UserAlreadyExistsError("CPF")
    
    # Atualizar usuário usando o serviço
    updated_user = await user_service.update_user(db, user, user_data)
    
    return UserResponseSchema.from_orm(updated_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar usuário",
    description="Desativa um usuário (soft delete)"
)
async def deactivate_user(
    user_id: str,
    deactivation_data: UserDeactivateSchema,
    current_user: CurrentUser,
    db: DatabaseSession
) -> None:
    """
    Desativa um usuário (soft delete)
    
    Args:
        user_id: ID do usuário
        deactivation_data: Dados da desativação
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Raises:
        UserNotFoundError: Se o usuário não for encontrado
        InsufficientPermissionsError: Se não tiver permissão
        BusinessRuleError: Se tentar desativar a si mesmo
    """
    # Verificar permissões
    if current_user.id != user_id and not current_user.is_admin:
        raise InsufficientPermissionsError("Desativação de outros usuários")
    
    # Impedir auto-desativação de admins
    if current_user.id == user_id and current_user.is_admin:
        raise BusinessRuleError("Administradores não podem desativar a própria conta")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError(user_id)
    
    # Desativar usuário usando o serviço
    await user_service.deactivate_user(db, user, deactivation_data.reason)


@router.post(
    "/{user_id}/reactivate",
    response_model=UserResponseSchema,
    summary="Reativar usuário",
    description="Reativa um usuário previamente desativado"
)
async def reactivate_user(
    user_id: str,
    reactivation_data: UserReactivateSchema,
    admin_user: AdminUser,
    db: DatabaseSession
) -> UserResponseSchema:
    """
    Reativa um usuário previamente desativado
    
    Args:
        user_id: ID do usuário
        reactivation_data: Dados da reativação
        admin_user: Usuário administrador
        db: Sessão do banco de dados
        
    Returns:
        UserResponseSchema: Dados do usuário reativado
        
    Raises:
        UserNotFoundError: Se o usuário não for encontrado
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError(user_id)
    
    # Reativar usuário usando o serviço
    reactivated_user = await user_service.reactivate_user(db, user, reactivation_data.reason)
    
    return UserResponseSchema.from_orm(reactivated_user)


@router.get(
    "/",
    response_model=List[UserListSchema],
    summary="Listar usuários",
    description="Lista usuários com filtros e paginação (requer permissões de admin)"
)
async def list_users(
    admin_user: AdminUser,
    db: DatabaseSession,
    pagination: PaginationParams,
    search: Optional[str] = Query(None, description="Busca por nome ou email"),
    status_filter: Optional[str] = Query(None, description="Filtro por status (active/inactive)"),
    email_verified: Optional[bool] = Query(None, description="Filtro por email verificado"),
    created_after: Optional[str] = Query(None, description="Filtro por data de criação (YYYY-MM-DD)"),
    created_before: Optional[str] = Query(None, description="Filtro por data de criação (YYYY-MM-DD)")
) -> List[UserListSchema]:
    """
    Lista usuários com filtros e paginação
    
    Args:
        admin_user: Usuário administrador
        db: Sessão do banco de dados
        pagination: Parâmetros de paginação
        search: Termo de busca
        status_filter: Filtro por status
        email_verified: Filtro por email verificado
        created_after: Data mínima de criação
        created_before: Data máxima de criação
        
    Returns:
        List[UserListSchema]: Lista de usuários
    """
    page, size = pagination
    offset = (page - 1) * size
    
    # Construir query base
    query = db.query(User)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    if status_filter:
        if status_filter.lower() == "active":
            query = query.filter(User.is_active == True)
        elif status_filter.lower() == "inactive":
            query = query.filter(User.is_active == False)
    
    if email_verified is not None:
        query = query.filter(User.email_verified == email_verified)
    
    if created_after:
        query = query.filter(User.created_at >= created_after)
    
    if created_before:
        query = query.filter(User.created_at <= created_before)
    
    # Aplicar paginação e ordenação
    users = query.order_by(User.created_at.desc()).offset(offset).limit(size).all()
    
    return [UserListSchema.from_orm(user) for user in users]


@router.get(
    "/search",
    response_model=List[UserListSchema],
    summary="Buscar usuários",
    description="Busca avançada de usuários com múltiplos critérios"
)
async def search_users(
    search_params: UserSearchSchema,
    admin_user: AdminUser,
    db: DatabaseSession,
    pagination: PaginationParams
) -> List[UserListSchema]:
    """
    Busca avançada de usuários
    
    Args:
        search_params: Parâmetros de busca
        admin_user: Usuário administrador
        db: Sessão do banco de dados
        pagination: Parâmetros de paginação
        
    Returns:
        List[UserListSchema]: Lista de usuários encontrados
    """
    page, size = pagination
    
    # Usar o serviço para busca avançada
    users = await user_service.search_users(db, search_params, page, size)
    
    return [UserListSchema.from_orm(user) for user in users]


@router.get(
    "/stats",
    response_model=UserStatsSchema,
    summary="Estatísticas de usuários",
    description="Retorna estatísticas gerais dos usuários"
)
async def get_user_stats(
    admin_user: AdminUser,
    db: DatabaseSession
) -> UserStatsSchema:
    """
    Obtém estatísticas gerais dos usuários
    
    Args:
        admin_user: Usuário administrador
        db: Sessão do banco de dados
        
    Returns:
        UserStatsSchema: Estatísticas dos usuários
    """
    stats = await user_service.get_user_stats(db)
    return stats