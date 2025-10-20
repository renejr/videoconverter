"""Schemas Pydantic para validação de dados
Sistema de Identidade e Transações - Domínio A

Este módulo centraliza todos os schemas Pydantic utilizados
para validação de dados de entrada e saída das APIs.
"""

# Imports dos schemas base
from .base import (
    BaseSchema,
    TimestampMixin,
    StatusEnum,
    GenderEnum,
    CountryCodeEnum,
    CurrencyEnum,
    validate_phone_number,
    validate_cpf,
    validate_password_strength
)

# Imports dos schemas de usuário
from .user import (
    UserBaseSchema,
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

# Imports dos schemas de autenticação
from .auth import (
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
    SecurityLogResponseSchema,
    AccountLockSchema,
    UnlockAccountSchema
)

# Imports dos schemas de planos
from .plan import (
    PlanBaseSchema,
    PlanCreateSchema,
    PlanUpdateSchema,
    PlanResponseSchema,
    PlanListSchema,
    PlanComparisonSchema,
    PlanSearchSchema,
    PlanStatsSchema,
    PlanRevenueSchema,
    PlanActivationSchema,
    PlanPromotionSchema
)

# Imports dos schemas de assinaturas
from .subscription import (
    SubscriptionBaseSchema,
    SubscriptionCreateSchema,
    SubscriptionUpdateSchema,
    SubscriptionResponseSchema,
    SubscriptionListSchema,
    SubscriptionCancelSchema,
    SubscriptionSuspendSchema,
    SubscriptionReactivateSchema,
    SubscriptionUpgradeSchema,
    SubscriptionRenewalSchema,
    SubscriptionSearchSchema,
    SubscriptionStatsSchema,
    SubscriptionRevenueSchema,
    SubscriptionEventSchema,
    SubscriptionNotificationSchema
)

# Imports dos schemas de pagamentos
from .payment import (
    PaymentBaseSchema,
    PaymentCreateSchema,
    PaymentUpdateSchema,
    PaymentResponseSchema,
    PaymentListSchema,
    PaymentRefundSchema,
    PaymentCaptureSchema,
    PaymentSearchSchema,
    PaymentStatsSchema,
    PaymentMethodSchema,
    PaymentWebhookSchema,
    PaymentReportSchema
)

# Imports dos schemas de faturas
from .invoice import (
    InvoiceBaseSchema,
    InvoiceCreateSchema,
    InvoiceUpdateSchema,
    InvoiceResponseSchema,
    InvoiceListSchema,
    InvoicePaySchema,
    InvoiceSendSchema,
    InvoiceCancelSchema,
    InvoiceSearchSchema,
    InvoiceStatsSchema,
    InvoiceReportSchema,
    InvoiceReminderSchema,
    InvoiceTemplateSchema
)

# Lista de todos os schemas disponíveis para importação
__all__ = [
    # Base schemas
    "BaseSchema",
    "TimestampMixin",
    "StatusEnum",
    "GenderEnum", 
    "CountryCodeEnum",
    "CurrencyEnum",
    "validate_phone_number",
    "validate_cpf",
    "validate_password_strength",
    
    # User schemas
    "UserBaseSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserResponseSchema",
    "UserDetailSchema",
    "UserListSchema",
    "UserSearchSchema",
    "UserStatsSchema",
    "UserDeactivateSchema",
    "UserReactivateSchema",
    
    # Auth schemas
    "LoginSchema",
    "LoginResponseSchema",
    "RegisterSchema",
    "PasswordChangeSchema",
    "PasswordResetRequestSchema",
    "PasswordResetSchema",
    "EmailVerificationSchema",
    "EmailVerificationRequestSchema",
    "TwoFactorSetupSchema",
    "TwoFactorSetupResponseSchema",
    "TwoFactorVerifySchema",
    "TwoFactorDisableSchema",
    "RefreshTokenSchema",
    "LogoutSchema",
    "SessionSchema",
    "ActiveSessionsResponseSchema",
    "RevokeSessionSchema",
    "SecurityEventSchema",
    "SecurityLogResponseSchema",
    "AccountLockSchema",
    "UnlockAccountSchema",
    
    # Plan schemas
    "PlanBaseSchema",
    "PlanCreateSchema",
    "PlanUpdateSchema",
    "PlanResponseSchema",
    "PlanListSchema",
    "PlanComparisonSchema",
    "PlanSearchSchema",
    "PlanStatsSchema",
    "PlanRevenueSchema",
    "PlanActivationSchema",
    "PlanPromotionSchema",
    
    # Subscription schemas
    "SubscriptionBaseSchema",
    "SubscriptionCreateSchema",
    "SubscriptionUpdateSchema",
    "SubscriptionResponseSchema",
    "SubscriptionListSchema",
    "SubscriptionCancelSchema",
    "SubscriptionSuspendSchema",
    "SubscriptionReactivateSchema",
    "SubscriptionUpgradeSchema",
    "SubscriptionRenewalSchema",
    "SubscriptionSearchSchema",
    "SubscriptionStatsSchema",
    "SubscriptionRevenueSchema",
    "SubscriptionEventSchema",
    "SubscriptionNotificationSchema",
    
    # Payment schemas
    "PaymentBaseSchema",
    "PaymentCreateSchema",
    "PaymentUpdateSchema",
    "PaymentResponseSchema",
    "PaymentListSchema",
    "PaymentRefundSchema",
    "PaymentCaptureSchema",
    "PaymentSearchSchema",
    "PaymentStatsSchema",
    "PaymentMethodSchema",
    "PaymentWebhookSchema",
    "PaymentReportSchema",
    
    # Invoice schemas
    "InvoiceBaseSchema",
    "InvoiceCreateSchema",
    "InvoiceUpdateSchema",
    "InvoiceResponseSchema",
    "InvoiceListSchema",
    "InvoicePaySchema",
    "InvoiceSendSchema",
    "InvoiceCancelSchema",
    "InvoiceSearchSchema",
    "InvoiceStatsSchema",
    "InvoiceReportSchema",
    "InvoiceReminderSchema",
    "InvoiceTemplateSchema"
]

# Registry de schemas por categoria para facilitar o uso
SCHEMA_REGISTRY = {
    "base": {
        "BaseSchema": BaseSchema,
        "TimestampMixin": TimestampMixin,
    },
    "user": {
        "UserBaseSchema": UserBaseSchema,
        "UserCreateSchema": UserCreateSchema,
        "UserUpdateSchema": UserUpdateSchema,
        "UserResponseSchema": UserResponseSchema,
        "UserDetailSchema": UserDetailSchema,
        "UserListSchema": UserListSchema,
        "UserSearchSchema": UserSearchSchema,
        "UserStatsSchema": UserStatsSchema,
        "UserDeactivateSchema": UserDeactivateSchema,
        "UserReactivateSchema": UserReactivateSchema,
    },
    "auth": {
        "LoginSchema": LoginSchema,
        "LoginResponseSchema": LoginResponseSchema,
        "RegisterSchema": RegisterSchema,
        "PasswordChangeSchema": PasswordChangeSchema,
        "PasswordResetRequestSchema": PasswordResetRequestSchema,
        "PasswordResetSchema": PasswordResetSchema,
        "EmailVerificationSchema": EmailVerificationSchema,
        "EmailVerificationRequestSchema": EmailVerificationRequestSchema,
        "TwoFactorSetupSchema": TwoFactorSetupSchema,
        "TwoFactorSetupResponseSchema": TwoFactorSetupResponseSchema,
        "TwoFactorVerifySchema": TwoFactorVerifySchema,
        "TwoFactorDisableSchema": TwoFactorDisableSchema,
        "RefreshTokenSchema": RefreshTokenSchema,
        "LogoutSchema": LogoutSchema,
        "SessionSchema": SessionSchema,
        "ActiveSessionsResponseSchema": ActiveSessionsResponseSchema,
        "RevokeSessionSchema": RevokeSessionSchema,
        "SecurityEventSchema": SecurityEventSchema,
        "SecurityLogResponseSchema": SecurityLogResponseSchema,
        "AccountLockSchema": AccountLockSchema,
        "UnlockAccountSchema": UnlockAccountSchema,
    },
    "plan": {
        "PlanBaseSchema": PlanBaseSchema,
        "PlanCreateSchema": PlanCreateSchema,
        "PlanUpdateSchema": PlanUpdateSchema,
        "PlanResponseSchema": PlanResponseSchema,
        "PlanListSchema": PlanListSchema,
        "PlanComparisonSchema": PlanComparisonSchema,
        "PlanSearchSchema": PlanSearchSchema,
        "PlanStatsSchema": PlanStatsSchema,
        "PlanRevenueSchema": PlanRevenueSchema,
        "PlanActivationSchema": PlanActivationSchema,
        "PlanPromotionSchema": PlanPromotionSchema,
    },
    "subscription": {
        "SubscriptionBaseSchema": SubscriptionBaseSchema,
        "SubscriptionCreateSchema": SubscriptionCreateSchema,
        "SubscriptionUpdateSchema": SubscriptionUpdateSchema,
        "SubscriptionResponseSchema": SubscriptionResponseSchema,
        "SubscriptionListSchema": SubscriptionListSchema,
        "SubscriptionCancelSchema": SubscriptionCancelSchema,
        "SubscriptionSuspendSchema": SubscriptionSuspendSchema,
        "SubscriptionReactivateSchema": SubscriptionReactivateSchema,
        "SubscriptionUpgradeSchema": SubscriptionUpgradeSchema,
        "SubscriptionRenewalSchema": SubscriptionRenewalSchema,
        "SubscriptionSearchSchema": SubscriptionSearchSchema,
        "SubscriptionStatsSchema": SubscriptionStatsSchema,
        "SubscriptionRevenueSchema": SubscriptionRevenueSchema,
        "SubscriptionEventSchema": SubscriptionEventSchema,
        "SubscriptionNotificationSchema": SubscriptionNotificationSchema,
    },
    "payment": {
        "PaymentBaseSchema": PaymentBaseSchema,
        "PaymentCreateSchema": PaymentCreateSchema,
        "PaymentUpdateSchema": PaymentUpdateSchema,
        "PaymentResponseSchema": PaymentResponseSchema,
        "PaymentListSchema": PaymentListSchema,
        "PaymentRefundSchema": PaymentRefundSchema,
        "PaymentCaptureSchema": PaymentCaptureSchema,
        "PaymentSearchSchema": PaymentSearchSchema,
        "PaymentStatsSchema": PaymentStatsSchema,
        "PaymentMethodSchema": PaymentMethodSchema,
        "PaymentWebhookSchema": PaymentWebhookSchema,
        "PaymentReportSchema": PaymentReportSchema,
    },
    "invoice": {
        "InvoiceBaseSchema": InvoiceBaseSchema,
        "InvoiceCreateSchema": InvoiceCreateSchema,
        "InvoiceUpdateSchema": InvoiceUpdateSchema,
        "InvoiceResponseSchema": InvoiceResponseSchema,
        "InvoiceListSchema": InvoiceListSchema,
        "InvoicePaySchema": InvoicePaySchema,
        "InvoiceSendSchema": InvoiceSendSchema,
        "InvoiceCancelSchema": InvoiceCancelSchema,
        "InvoiceSearchSchema": InvoiceSearchSchema,
        "InvoiceStatsSchema": InvoiceStatsSchema,
        "InvoiceReportSchema": InvoiceReportSchema,
        "InvoiceReminderSchema": InvoiceReminderSchema,
        "InvoiceTemplateSchema": InvoiceTemplateSchema,
    }
}

# Funções utilitárias para trabalhar com schemas
def get_schema_by_name(schema_name: str):
    """
    Obtém um schema pelo nome
    
    Args:
        schema_name: Nome do schema
        
    Returns:
        Classe do schema ou None se não encontrado
    """
    for category_schemas in SCHEMA_REGISTRY.values():
        if schema_name in category_schemas:
            return category_schemas[schema_name]
    return None


def get_schemas_by_category(category: str):
    """
    Obtém todos os schemas de uma categoria
    
    Args:
        category: Nome da categoria (user, auth, plan, etc.)
        
    Returns:
        Dicionário com os schemas da categoria
    """
    return SCHEMA_REGISTRY.get(category, {})


def get_all_schemas():
    """
    Obtém todos os schemas disponíveis
    
    Returns:
        Dicionário com todos os schemas organizados por categoria
    """
    return SCHEMA_REGISTRY


def validate_schema_data(schema_class, data: dict):
    """
    Valida dados usando um schema específico
    
    Args:
        schema_class: Classe do schema Pydantic
        data: Dados a serem validados
        
    Returns:
        Instância validada do schema
        
    Raises:
        ValidationError: Se os dados não passarem na validação
    """
    return schema_class(**data)


def get_schema_fields(schema_class):
    """
    Obtém os campos de um schema
    
    Args:
        schema_class: Classe do schema Pydantic
        
    Returns:
        Dicionário com informações dos campos
    """
    return schema_class.__fields__


def get_schema_json_schema(schema_class):
    """
    Obtém o JSON Schema de um schema Pydantic
    
    Args:
        schema_class: Classe do schema Pydantic
        
    Returns:
        Dicionário com o JSON Schema
    """
    return schema_class.schema()


# Validação automática dos schemas em ambiente de desenvolvimento
import os
if os.getenv('ENVIRONMENT', 'development') == 'development':
    def validate_schemas():
        """Valida a integridade de todos os schemas"""
        errors = []
        
        for category, schemas in SCHEMA_REGISTRY.items():
            for schema_name, schema_class in schemas.items():
                try:
                    # Verifica se o schema tem os métodos necessários
                    if not hasattr(schema_class, '__fields__'):
                        errors.append(f"{category}.{schema_name}: Schema inválido - não possui __fields__")
                    
                    # Verifica se consegue gerar o JSON schema
                    try:
                        schema_class.schema()
                    except Exception as e:
                        errors.append(f"{category}.{schema_name}: Erro ao gerar JSON schema - {str(e)}")
                        
                except Exception as e:
                    errors.append(f"{category}.{schema_name}: Erro geral - {str(e)}")
        
        if errors:
            print("⚠️  Erros encontrados nos schemas:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ Todos os schemas validados com sucesso!")
    
    # Executa validação automaticamente
    validate_schemas()