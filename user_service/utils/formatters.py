"""
Formatadores - User Service
Sistema de Identidade e Transações - Domínio A

Este módulo contém funções para formatação de
diferentes tipos de dados utilizados no sistema.
"""

import re
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


def format_cpf(cpf: str) -> str:
    """
    Formata um CPF para o padrão XXX.XXX.XXX-XX
    
    Args:
        cpf: String contendo o CPF a ser formatado
        
    Returns:
        str: CPF formatado
    """
    if not cpf:
        return ""
    
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return cpf
    
    # Aplica a formatação
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def format_cnpj(cnpj: str) -> str:
    """
    Formata um CNPJ para o padrão XX.XXX.XXX/XXXX-XX
    
    Args:
        cnpj: String contendo o CNPJ a ser formatado
        
    Returns:
        str: CNPJ formatado
    """
    if not cnpj:
        return ""
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return cnpj
    
    # Aplica a formatação
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def format_phone(phone: str) -> str:
    """
    Formata um telefone brasileiro para o padrão (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
    
    Args:
        phone: String contendo o telefone a ser formatado
        
    Returns:
        str: Telefone formatado
    """
    if not phone:
        return ""
    
    # Remove caracteres não numéricos
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Formata conforme o número de dígitos
    if len(phone) == 11:  # Celular
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:  # Fixo
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    else:
        return phone


def format_cep(cep: str) -> str:
    """
    Formata um CEP para o padrão XXXXX-XXX
    
    Args:
        cep: String contendo o CEP a ser formatado
        
    Returns:
        str: CEP formatado
    """
    if not cep:
        return ""
    
    # Remove caracteres não numéricos
    cep = re.sub(r'[^0-9]', '', cep)
    
    # Verifica se tem 8 dígitos
    if len(cep) != 8:
        return cep
    
    # Aplica a formatação
    return f"{cep[:5]}-{cep[5:]}"


def format_currency(value: float, currency: str = "BRL") -> str:
    """
    Formata um valor monetário
    
    Args:
        value: Valor a ser formatado
        currency: Código da moeda (padrão: BRL)
        
    Returns:
        str: Valor formatado
    """
    if value is None:
        return ""
    
    if currency == "BRL":
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif currency == "USD":
        return f"$ {value:,.2f}"
    elif currency == "EUR":
        return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"{value:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formata um valor como porcentagem
    
    Args:
        value: Valor a ser formatado (0.15 = 15%)
        decimals: Número de casas decimais
        
    Returns:
        str: Valor formatado como porcentagem
    """
    if value is None:
        return ""
    
    percentage = value * 100
    return f"{percentage:.{decimals}f}%"


def format_date(date_value: date, format_type: str = "br") -> str:
    """
    Formata uma data
    
    Args:
        date_value: Data a ser formatada
        format_type: Tipo de formatação ("br", "us", "iso")
        
    Returns:
        str: Data formatada
    """
    if not date_value:
        return ""
    
    if format_type == "br":
        return date_value.strftime("%d/%m/%Y")
    elif format_type == "us":
        return date_value.strftime("%m/%d/%Y")
    elif format_type == "iso":
        return date_value.strftime("%Y-%m-%d")
    else:
        return str(date_value)


def format_datetime(datetime_value: datetime, format_type: str = "br") -> str:
    """
    Formata uma data e hora
    
    Args:
        datetime_value: Data e hora a ser formatada
        format_type: Tipo de formatação ("br", "us", "iso")
        
    Returns:
        str: Data e hora formatada
    """
    if not datetime_value:
        return ""
    
    if format_type == "br":
        return datetime_value.strftime("%d/%m/%Y %H:%M:%S")
    elif format_type == "us":
        return datetime_value.strftime("%m/%d/%Y %I:%M:%S %p")
    elif format_type == "iso":
        return datetime_value.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return str(datetime_value)


def format_credit_card(card_number: str, mask: bool = True) -> str:
    """
    Formata um número de cartão de crédito
    
    Args:
        card_number: Número do cartão
        mask: Se deve mascarar o número (mostrar apenas os últimos 4 dígitos)
        
    Returns:
        str: Número do cartão formatado
    """
    if not card_number:
        return ""
    
    # Remove caracteres não numéricos
    card_number = re.sub(r'[^0-9]', '', card_number)
    
    if mask:
        # Mostra apenas os últimos 4 dígitos
        if len(card_number) >= 4:
            masked = "*" * (len(card_number) - 4) + card_number[-4:]
            # Adiciona espaços a cada 4 dígitos
            return " ".join([masked[i:i+4] for i in range(0, len(masked), 4)])
        else:
            return "*" * len(card_number)
    else:
        # Adiciona espaços a cada 4 dígitos
        return " ".join([card_number[i:i+4] for i in range(0, len(card_number), 4)])


def format_file_size(size_bytes: int) -> str:
    """
    Formata um tamanho de arquivo em bytes para formato legível
    
    Args:
        size_bytes: Tamanho em bytes
        
    Returns:
        str: Tamanho formatado (ex: "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def format_duration(seconds: int) -> str:
    """
    Formata uma duração em segundos para formato legível
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        str: Duração formatada (ex: "1h 30m 45s")
    """
    if seconds < 0:
        return "0s"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_name(name: str) -> str:
    """
    Formata um nome próprio (primeira letra de cada palavra em maiúscula)
    
    Args:
        name: Nome a ser formatado
        
    Returns:
        str: Nome formatado
    """
    if not name:
        return ""
    
    # Lista de preposições que devem ficar em minúscula
    prepositions = ["de", "da", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos"]
    
    words = name.strip().lower().split()
    formatted_words = []
    
    for i, word in enumerate(words):
        if i == 0 or word not in prepositions:
            # Primeira palavra ou não é preposição
            formatted_words.append(word.capitalize())
        else:
            # É preposição e não é a primeira palavra
            formatted_words.append(word)
    
    return " ".join(formatted_words)


def format_document_number(document: str, document_type: str) -> str:
    """
    Formata um número de documento baseado no tipo
    
    Args:
        document: Número do documento
        document_type: Tipo do documento ("cpf", "cnpj", "rg", etc.)
        
    Returns:
        str: Documento formatado
    """
    if not document:
        return ""
    
    document_type = document_type.lower()
    
    if document_type == "cpf":
        return format_cpf(document)
    elif document_type == "cnpj":
        return format_cnpj(document)
    else:
        return document


def clean_string(text: str) -> str:
    """
    Remove caracteres especiais e espaços extras de uma string
    
    Args:
        text: Texto a ser limpo
        
    Returns:
        str: Texto limpo
    """
    if not text:
        return ""
    
    # Remove espaços extras
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove caracteres de controle
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text


def normalize_string(text: str) -> str:
    """
    Normaliza uma string removendo acentos e convertendo para minúscula
    
    Args:
        text: Texto a ser normalizado
        
    Returns:
        str: Texto normalizado
    """
    if not text:
        return ""
    
    import unicodedata
    
    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Converte para minúscula
    text = text.lower()
    
    return text