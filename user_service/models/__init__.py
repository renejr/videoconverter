"""
Modelos de dados - Domínio A
Sistema de Identidade e Transações para Plataforma VOD

Este módulo contém todos os modelos SQLAlchemy para o Domínio A,
incluindo usuários, credenciais, planos, assinaturas, pagamentos,
faturas e sessões de usuário.
"""

# Importa a base do SQLAlchemy
from database.connection import Base

# Importa todos os modelos
from .user import User
from .credential import Credential
from .plan import Plan, PlanType, BillingCycle
from .subscription import Subscription, SubscriptionStatus, CancellationReason
from .payment import Payment, PaymentStatus, PaymentMethod, PaymentType
from .invoice import Invoice, InvoiceStatus, InvoiceType
from .user_session import UserSession

# Lista de todos os modelos para facilitar importações
__all__ = [
    # Base
    'Base',
    
    # Modelos principais
    'User',
    'Credential',
    'Plan',
    'Subscription',
    'Payment',
    'Invoice',
    'UserSession',
    
    # Enums do Plan
    'PlanType',
    'BillingCycle',
    
    # Enums do Subscription
    'SubscriptionStatus',
    'CancellationReason',
    
    # Enums do Payment
    'PaymentStatus',
    'PaymentMethod',
    'PaymentType',
    
    # Enums do Invoice
    'InvoiceStatus',
    'InvoiceType',
]

# Metadados dos modelos para facilitar operações em lote
MODEL_REGISTRY = {
    'user': User,
    'credential': Credential,
    'plan': Plan,
    'subscription': Subscription,
    'payment': Payment,
    'invoice': Invoice,
    'user_session': UserSession,
}

# Ordem de criação das tabelas (respeitando dependências)
TABLE_CREATION_ORDER = [
    User,           # Tabela base - sem dependências
    Credential,     # Depende de User
    Plan,           # Tabela independente
    Subscription,   # Depende de User e Plan
    Payment,        # Depende de User e Subscription
    Invoice,        # Depende de User, Subscription e Payment
    UserSession,    # Depende de User
]

# Ordem de exclusão das tabelas (inversa da criação)
TABLE_DELETION_ORDER = list(reversed(TABLE_CREATION_ORDER))


def get_model_by_name(model_name: str):
    """
    Obtém um modelo pelo nome
    
    Args:
        model_name (str): Nome do modelo
        
    Returns:
        Model: Classe do modelo SQLAlchemy
        
    Raises:
        KeyError: Se o modelo não for encontrado
    """
    if model_name not in MODEL_REGISTRY:
        raise KeyError(f"Modelo '{model_name}' não encontrado. Modelos disponíveis: {list(MODEL_REGISTRY.keys())}")
    
    return MODEL_REGISTRY[model_name]


def get_all_models():
    """
    Retorna todos os modelos registrados
    
    Returns:
        list: Lista de classes de modelos
    """
    return list(MODEL_REGISTRY.values())


def get_model_table_name(model_class):
    """
    Obtém o nome da tabela de um modelo
    
    Args:
        model_class: Classe do modelo SQLAlchemy
        
    Returns:
        str: Nome da tabela
    """
    return model_class.__tablename__


def get_model_relationships(model_class):
    """
    Obtém os relacionamentos de um modelo
    
    Args:
        model_class: Classe do modelo SQLAlchemy
        
    Returns:
        dict: Dicionário com os relacionamentos
    """
    relationships = {}
    
    # Itera sobre os atributos da classe
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name)
        
        # Verifica se é um relacionamento SQLAlchemy
        if hasattr(attr, 'property') and hasattr(attr.property, 'mapper'):
            relationships[attr_name] = {
                'target_model': attr.property.mapper.class_,
                'target_table': attr.property.mapper.class_.__tablename__,
                'relationship_type': type(attr.property).__name__
            }
    
    return relationships


# Função para validar integridade dos modelos
def validate_models():
    """
    Valida a integridade dos modelos e relacionamentos
    
    Returns:
        dict: Resultado da validação
    """
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'models_count': len(MODEL_REGISTRY),
        'tables_count': len(TABLE_CREATION_ORDER)
    }
    
    try:
        # Verifica se todos os modelos têm __tablename__
        for name, model in MODEL_REGISTRY.items():
            if not hasattr(model, '__tablename__'):
                validation_result['errors'].append(f"Modelo '{name}' não possui __tablename__")
                validation_result['valid'] = False
        
        # Verifica se a ordem de criação está correta
        if len(TABLE_CREATION_ORDER) != len(MODEL_REGISTRY):
            validation_result['warnings'].append("Número de modelos na ordem de criação difere do registro")
        
        # Adiciona informações sobre relacionamentos
        for name, model in MODEL_REGISTRY.items():
            relationships = get_model_relationships(model)
            if relationships:
                validation_result[f'{name}_relationships'] = relationships
    
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append(f"Erro durante validação: {str(e)}")
    
    return validation_result


# Executa validação na importação (apenas em desenvolvimento)
import os
if os.getenv('ENVIRONMENT', 'development') == 'development':
    _validation = validate_models()
    if not _validation['valid']:
        print("⚠️  Avisos na validação dos modelos:")
        for error in _validation['errors']:
            print(f"   - {error}")
        for warning in _validation['warnings']:
            print(f"   - {warning}")
    else:
        print(f"✅ Modelos validados com sucesso! ({_validation['models_count']} modelos, {_validation['tables_count']} tabelas)")