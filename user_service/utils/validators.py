"""
Validadores - User Service
Sistema de Identidade e Transações - Domínio A

Este módulo contém funções de validação para
diferentes tipos de dados utilizados no sistema.
"""

import re
from typing import Optional
from datetime import datetime, date


def validate_cpf(cpf: str) -> bool:
    """
    Valida um número de CPF brasileiro
    
    Args:
        cpf: String contendo o CPF a ser validado
        
    Returns:
        bool: True se o CPF for válido, False caso contrário
    """
    if not cpf:
        return False
    
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula o primeiro dígito verificador
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum1 % 11)
    if digit1 >= 10:
        digit1 = 0
    
    # Verifica o primeiro dígito
    if int(cpf[9]) != digit1:
        return False
    
    # Calcula o segundo dígito verificador
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum2 % 11)
    if digit2 >= 10:
        digit2 = 0
    
    # Verifica o segundo dígito
    return int(cpf[10]) == digit2


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida um número de CNPJ brasileiro
    
    Args:
        cnpj: String contendo o CNPJ a ser validado
        
    Returns:
        bool: True se o CNPJ for válido, False caso contrário
    """
    if not cnpj:
        return False
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Calcula o primeiro dígito verificador
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    digit1 = 11 - (sum1 % 11)
    if digit1 >= 10:
        digit1 = 0
    
    # Verifica o primeiro dígito
    if int(cnpj[12]) != digit1:
        return False
    
    # Calcula o segundo dígito verificador
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    digit2 = 11 - (sum2 % 11)
    if digit2 >= 10:
        digit2 = 0
    
    # Verifica o segundo dígito
    return int(cnpj[13]) == digit2


def validate_phone(phone: str) -> bool:
    """
    Valida um número de telefone brasileiro
    
    Args:
        phone: String contendo o telefone a ser validado
        
    Returns:
        bool: True se o telefone for válido, False caso contrário
    """
    if not phone:
        return False
    
    # Remove caracteres não numéricos
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Verifica se tem 10 ou 11 dígitos (com DDD)
    if len(phone) not in [10, 11]:
        return False
    
    # Verifica se o DDD é válido (11 a 99)
    ddd = int(phone[:2])
    if ddd < 11 or ddd > 99:
        return False
    
    # Para celular (11 dígitos), o terceiro dígito deve ser 9
    if len(phone) == 11 and phone[2] != '9':
        return False
    
    # Para telefone fixo (10 dígitos), o terceiro dígito deve ser 2, 3, 4 ou 5
    if len(phone) == 10 and phone[2] not in ['2', '3', '4', '5']:
        return False
    
    return True


def validate_email(email: str) -> bool:
    """
    Valida um endereço de email
    
    Args:
        email: String contendo o email a ser validado
        
    Returns:
        bool: True se o email for válido, False caso contrário
    """
    if not email:
        return False
    
    # Padrão regex para validação de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> dict:
    """
    Valida a força de uma senha
    
    Args:
        password: String contendo a senha a ser validada
        
    Returns:
        dict: Dicionário com informações sobre a validação
    """
    if not password:
        return {
            "valid": False,
            "score": 0,
            "errors": ["Senha é obrigatória"]
        }
    
    errors = []
    score = 0
    
    # Verifica comprimento mínimo
    if len(password) < 8:
        errors.append("Senha deve ter pelo menos 8 caracteres")
    else:
        score += 1
    
    # Verifica se tem letras minúsculas
    if not re.search(r'[a-z]', password):
        errors.append("Senha deve conter pelo menos uma letra minúscula")
    else:
        score += 1
    
    # Verifica se tem letras maiúsculas
    if not re.search(r'[A-Z]', password):
        errors.append("Senha deve conter pelo menos uma letra maiúscula")
    else:
        score += 1
    
    # Verifica se tem números
    if not re.search(r'[0-9]', password):
        errors.append("Senha deve conter pelo menos um número")
    else:
        score += 1
    
    # Verifica se tem caracteres especiais
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Senha deve conter pelo menos um caractere especial")
    else:
        score += 1
    
    # Verifica comprimento ideal
    if len(password) >= 12:
        score += 1
    
    return {
        "valid": len(errors) == 0,
        "score": score,
        "errors": errors,
        "strength": get_password_strength_label(score)
    }


def get_password_strength_label(score: int) -> str:
    """
    Retorna o rótulo da força da senha baseado na pontuação
    
    Args:
        score: Pontuação da senha (0-6)
        
    Returns:
        str: Rótulo da força da senha
    """
    if score <= 2:
        return "Muito fraca"
    elif score <= 3:
        return "Fraca"
    elif score <= 4:
        return "Média"
    elif score <= 5:
        return "Forte"
    else:
        return "Muito forte"


def validate_birth_date(birth_date: date) -> bool:
    """
    Valida uma data de nascimento
    
    Args:
        birth_date: Data de nascimento a ser validada
        
    Returns:
        bool: True se a data for válida, False caso contrário
    """
    if not birth_date:
        return False
    
    today = date.today()
    
    # Verifica se a data não é no futuro
    if birth_date > today:
        return False
    
    # Calcula a idade
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    # Verifica se a idade é razoável (entre 0 e 150 anos)
    return 0 <= age <= 150


def validate_cep(cep: str) -> bool:
    """
    Valida um CEP brasileiro
    
    Args:
        cep: String contendo o CEP a ser validado
        
    Returns:
        bool: True se o CEP for válido, False caso contrário
    """
    if not cep:
        return False
    
    # Remove caracteres não numéricos
    cep = re.sub(r'[^0-9]', '', cep)
    
    # Verifica se tem 8 dígitos
    if len(cep) != 8:
        return False
    
    # Verifica se não são todos zeros
    if cep == '00000000':
        return False
    
    return True


def validate_credit_card(card_number: str) -> bool:
    """
    Valida um número de cartão de crédito usando o algoritmo de Luhn
    
    Args:
        card_number: String contendo o número do cartão
        
    Returns:
        bool: True se o cartão for válido, False caso contrário
    """
    if not card_number:
        return False
    
    # Remove espaços e hífens
    card_number = re.sub(r'[\s-]', '', card_number)
    
    # Verifica se contém apenas dígitos
    if not card_number.isdigit():
        return False
    
    # Verifica se tem entre 13 e 19 dígitos
    if len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # Algoritmo de Luhn
    def luhn_checksum(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10
    
    return luhn_checksum(card_number) == 0


def validate_cvv(cvv: str, card_number: Optional[str] = None) -> bool:
    """
    Valida um código CVV de cartão de crédito
    
    Args:
        cvv: String contendo o CVV
        card_number: Número do cartão (opcional, para validação específica)
        
    Returns:
        bool: True se o CVV for válido, False caso contrário
    """
    if not cvv:
        return False
    
    # Remove espaços
    cvv = cvv.strip()
    
    # Verifica se contém apenas dígitos
    if not cvv.isdigit():
        return False
    
    # Verifica se tem 3 ou 4 dígitos
    if len(cvv) not in [3, 4]:
        return False
    
    # Se o número do cartão for fornecido, faz validação específica
    if card_number:
        # Remove caracteres não numéricos do cartão
        card_number = re.sub(r'[^0-9]', '', card_number)
        
        # American Express usa CVV de 4 dígitos
        if card_number.startswith(('34', '37')) and len(cvv) != 4:
            return False
        
        # Outros cartões usam CVV de 3 dígitos
        elif not card_number.startswith(('34', '37')) and len(cvv) != 3:
            return False
    
    return True