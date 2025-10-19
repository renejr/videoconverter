"""
Endpoints de Autenticação - API v1
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os endpoints relacionados à
autenticação, autorização e gerenciamento de sessões.
"""

from typing import List
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.dependencies import (
    DatabaseSession,
    CurrentUser,
    OptionalUser,
    rate_limit_dependency,
    create_access_token
)
from api.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    EmailNotVerifiedError,
    SessionExpiredError,
    TokenExpiredError
)
from models.user import User
from models.user_session import UserSession
from schemas.auth import (
    LoginSchema,
    LoginResponseSchema,
    RegisterSchema,
    PasswordChangeSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    EmailVerificationSchema,
    EmailVerificationRequestSchema,
    TwoFactorSetupSchema,
    TwoFactorSetupResponseSchema,
    TwoFactorVerifySchema,
    TwoFactorDisableSchema,
    RefreshTokenSchema,
    LogoutSchema,
    SessionSchema,
    ActiveSessionsResponseSchema,
    RevokeSessionSchema,
    SecurityEventSchema,
    SecurityLogResponseSchema
)
from schemas.user import UserResponseSchema
from services.auth_service import AuthService
from services.user_service import UserService

# Configuração do router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    dependencies=[Depends(rate_limit_dependency)]
)

# Instâncias dos serviços
auth_service = AuthService()
user_service = UserService()


@router.post(
    "/register",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
    description="Registra um novo usuário no sistema e envia email de verificação"
)
async def register(
    user_data: RegisterSchema,
    request: Request,
    db: DatabaseSession
) -> UserResponseSchema:
    """
    Registra um novo usuário no sistema
    
    Args:
        user_data: Dados do usuário para registro
        request: Objeto de requisição HTTP
        db: Sessão do banco de dados
        
    Returns:
        UserResponseSchema: Dados do usuário criado
        
    Raises:
        UserAlreadyExistsError: Se email ou CPF já existir
        ValidationError: Se os dados forem inválidos
    """
    # Obter informações do cliente
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    # Converter RegisterSchema para UserCreateSchema
    from schemas.user import UserCreateSchema
    user_create_data = UserCreateSchema(
        email=user_data.email,
        password=user_data.password,
        confirm_password=user_data.confirm_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        accept_terms=user_data.accept_terms,
        accept_privacy=user_data.accept_privacy,
        marketing_consent=user_data.marketing_consent,
        # CPF não está presente no RegisterSchema, então não incluímos
    )
    
    # Registrar usuário usando o serviço de autenticação
    new_user = await auth_service.register_user(db, user_create_data, client_ip, user_agent)
    
    return UserResponseSchema.from_orm(new_user)


@router.post(
    "/login",
    response_model=LoginResponseSchema,
    summary="Fazer login",
    description="Autentica um usuário e retorna tokens de acesso"
)
async def login(
    login_data: LoginSchema,
    request: Request,
    db: DatabaseSession
) -> LoginResponseSchema:
    """
    Autentica um usuário no sistema
    
    Args:
        login_data: Dados de login (email e senha)
        request: Objeto Request para obter informações do cliente
        db: Sessão do banco de dados
        
    Returns:
        LoginResponseSchema: Tokens de acesso e informações do usuário
        
    Raises:
        InvalidCredentialsError: Se as credenciais forem inválidas
        InactiveUserError: Se o usuário estiver inativo
    """
    # Obter informações do cliente
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    # Autenticar usuário usando o serviço
    auth_result = await auth_service.authenticate_user(
        db, login_data.email, login_data.password, client_ip, user_agent
    )
    
    return auth_result


@router.post(
    "/login/oauth2",
    response_model=LoginResponseSchema,
    summary="Login OAuth2 (compatibilidade)",
    description="Endpoint compatível com OAuth2PasswordRequestForm"
)
async def login_oauth2(
    request: Request,
    db: DatabaseSession,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> LoginResponseSchema:
    """
    Login compatível com OAuth2PasswordRequestForm
    
    Args:
        form_data: Dados do formulário OAuth2
        request: Objeto Request
        db: Sessão do banco de dados
        
    Returns:
        LoginResponseSchema: Tokens de acesso e informações do usuário
    """
    # Converter para LoginSchema
    login_data = LoginSchema(
        email=form_data.username,
        password=form_data.password
    )
    
    return await login(login_data, request, db)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Fazer logout",
    description="Invalida a sessão atual do usuário"
)
async def logout(
    logout_data: LogoutSchema,
    current_user: CurrentUser,
    db: DatabaseSession
) -> None:
    """
    Faz logout do usuário atual
    
    Args:
        logout_data: Dados do logout
        current_user: Usuário autenticado
        db: Sessão do banco de dados
    """
    await auth_service.logout_user(db, current_user.id, logout_data.session_id)


@router.post(
    "/refresh",
    response_model=LoginResponseSchema,
    summary="Renovar token",
    description="Renova o token de acesso usando o refresh token"
)
async def refresh_token(
    refresh_data: RefreshTokenSchema,
    db: DatabaseSession
) -> LoginResponseSchema:
    """
    Renova o token de acesso
    
    Args:
        refresh_data: Dados do refresh token
        db: Sessão do banco de dados
        
    Returns:
        LoginResponseSchema: Novos tokens de acesso
        
    Raises:
        TokenExpiredError: Se o refresh token estiver expirado
        InvalidTokenError: Se o refresh token for inválido
    """
    return await auth_service.refresh_access_token(db, refresh_data.refresh_token)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Alterar senha",
    description="Altera a senha do usuário autenticado"
)
async def change_password(
    password_data: PasswordChangeSchema,
    current_user: CurrentUser,
    db: DatabaseSession
) -> None:
    """
    Altera a senha do usuário
    
    Args:
        password_data: Dados da alteração de senha
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Raises:
        InvalidCredentialsError: Se a senha atual estiver incorreta
    """
    await auth_service.change_password(
        db, current_user, password_data.current_password, password_data.new_password
    )


@router.post(
    "/reset-password/request",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Solicitar reset de senha",
    description="Envia email com link para reset de senha"
)
async def request_password_reset(
    reset_request: PasswordResetRequestSchema,
    db: DatabaseSession
) -> None:
    """
    Solicita reset de senha
    
    Args:
        reset_request: Dados da solicitação de reset
        db: Sessão do banco de dados
    """
    await auth_service.request_password_reset(db, reset_request.email)


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Resetar senha",
    description="Reseta a senha usando o token recebido por email"
)
async def reset_password(
    reset_data: PasswordResetSchema,
    db: DatabaseSession
) -> None:
    """
    Reseta a senha do usuário
    
    Args:
        reset_data: Dados do reset de senha
        db: Sessão do banco de dados
        
    Raises:
        InvalidTokenError: Se o token for inválido ou expirado
    """
    await auth_service.reset_password(db, reset_data.token, reset_data.new_password)


@router.post(
    "/verify-email/request",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Solicitar verificação de email",
    description="Reenvia email de verificação"
)
async def request_email_verification(
    verification_request: EmailVerificationRequestSchema,
    db: DatabaseSession
) -> None:
    """
    Solicita nova verificação de email
    
    Args:
        verification_request: Dados da solicitação
        db: Sessão do banco de dados
    """
    await auth_service.request_email_verification(db, verification_request.email)


@router.post(
    "/verify-email",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Verificar email",
    description="Verifica o email usando o token recebido"
)
async def verify_email(
    verification_data: EmailVerificationSchema,
    db: DatabaseSession
) -> None:
    """
    Verifica o email do usuário
    
    Args:
        verification_data: Dados da verificação
        db: Sessão do banco de dados
        
    Raises:
        InvalidTokenError: Se o token for inválido ou expirado
    """
    await auth_service.verify_email(db, verification_data.token)


@router.post(
    "/2fa/setup",
    response_model=TwoFactorSetupResponseSchema,
    summary="Configurar 2FA",
    description="Configura autenticação de dois fatores"
)
async def setup_two_factor(
    setup_data: TwoFactorSetupSchema,
    current_user: CurrentUser,
    db: DatabaseSession
) -> TwoFactorSetupResponseSchema:
    """
    Configura autenticação de dois fatores
    
    Args:
        setup_data: Dados da configuração 2FA
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        TwoFactorSetupResponseSchema: Dados da configuração 2FA
    """
    return await auth_service.setup_two_factor(db, current_user, setup_data.method)


@router.post(
    "/2fa/verify",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Verificar 2FA",
    description="Verifica código de autenticação de dois fatores"
)
async def verify_two_factor(
    verify_data: TwoFactorVerifySchema,
    current_user: CurrentUser,
    db: DatabaseSession
) -> None:
    """
    Verifica código 2FA
    
    Args:
        verify_data: Dados da verificação 2FA
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Raises:
        InvalidCredentialsError: Se o código estiver incorreto
    """
    await auth_service.verify_two_factor(db, current_user, verify_data.code)


@router.post(
    "/2fa/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desabilitar 2FA",
    description="Desabilita autenticação de dois fatores"
)
async def disable_two_factor(
    disable_data: TwoFactorDisableSchema,
    current_user: CurrentUser,
    db: DatabaseSession
) -> None:
    """
    Desabilita autenticação de dois fatores
    
    Args:
        disable_data: Dados da desabilitação
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Raises:
        InvalidCredentialsError: Se a senha estiver incorreta
    """
    await auth_service.disable_two_factor(db, current_user, disable_data.password)


@router.get(
    "/sessions",
    response_model=ActiveSessionsResponseSchema,
    summary="Listar sessões ativas",
    description="Lista todas as sessões ativas do usuário"
)
async def get_active_sessions(
    current_user: CurrentUser,
    db: DatabaseSession
) -> ActiveSessionsResponseSchema:
    """
    Lista sessões ativas do usuário
    
    Args:
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        ActiveSessionsResponseSchema: Lista de sessões ativas
    """
    sessions = await auth_service.get_user_sessions(db, current_user.id)
    
    # Converter dicionários para SessionSchema
    session_schemas = [SessionSchema(**session) for session in sessions]
    
    return ActiveSessionsResponseSchema(
        sessions=session_schemas,
        total=len(session_schemas)
    )


@router.post(
    "/sessions/{session_id}/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revogar sessão",
    description="Revoga uma sessão específica"
)
async def revoke_session(
    session_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
) -> None:
    """
    Revoga uma sessão específica
    
    Args:
        session_id: ID da sessão a ser revogada
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Raises:
        UserNotFoundError: Se a sessão não for encontrada
        InsufficientPermissionsError: Se a sessão não pertencer ao usuário
    """
    await auth_service.revoke_session(db, current_user.id, session_id)


@router.post(
    "/sessions/revoke-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revogar todas as sessões",
    description="Revoga todas as sessões do usuário exceto a atual"
)
async def revoke_all_sessions(
    current_user: CurrentUser,
    db: DatabaseSession
) -> None:
    """
    Revoga todas as sessões do usuário exceto a atual
    
    Args:
        current_user: Usuário autenticado
        db: Sessão do banco de dados
    """
    await auth_service.revoke_all_sessions(db, current_user.id)


@router.get(
    "/security-log",
    response_model=SecurityLogResponseSchema,
    summary="Log de segurança",
    description="Retorna o log de eventos de segurança do usuário"
)
async def get_security_log(
    current_user: CurrentUser,
    db: DatabaseSession
) -> SecurityLogResponseSchema:
    """
    Obtém o log de eventos de segurança
    
    Args:
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        SecurityLogResponseSchema: Log de eventos de segurança
    """
    events = await auth_service.get_security_events(db, current_user.id)
    
    return SecurityLogResponseSchema(
        events=[SecurityEventSchema.from_orm(event) for event in events]
    )


@router.get(
    "/me",
    response_model=UserResponseSchema,
    summary="Informações do usuário autenticado",
    description="Retorna informações básicas do usuário autenticado"
)
async def get_authenticated_user(
    current_user: CurrentUser
) -> UserResponseSchema:
    """
    Obtém informações do usuário autenticado
    
    Args:
        current_user: Usuário autenticado
        
    Returns:
        UserResponseSchema: Informações do usuário
    """
    return UserResponseSchema.from_orm(current_user)