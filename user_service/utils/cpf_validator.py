"""
Validador de CPF - Servidor
Sistema de validação completa de CPF brasileiro
"""

import re
from typing import Union


class CPFValidator:
    """
    Classe para validação de CPF brasileiro
    
    Implementa todas as regras de validação:
    - Formato (11 dígitos)
    - Dígitos verificadores
    - CPFs inválidos conhecidos
    """
    
    # CPFs inválidos conhecidos (todos os dígitos iguais)
    INVALID_CPFS = {
        '00000000000', '11111111111', '22222222222', '33333333333',
        '44444444444', '55555555555', '66666666666', '77777777777',
        '88888888888', '99999999999'
    }
    
    @staticmethod
    def clean_cpf(cpf: str) -> str:
        """
        Remove formatação do CPF (pontos, hífens, espaços)
        
        Args:
            cpf: CPF com ou sem formatação
            
        Returns:
            CPF apenas com números
        """
        if not cpf:
            return ""
        
        # Remove tudo que não for dígito
        return re.sub(r'\D', '', str(cpf))
    
    @staticmethod
    def format_cpf(cpf: str) -> str:
        """
        Formata CPF no padrão XXX.XXX.XXX-XX
        
        Args:
            cpf: CPF apenas com números
            
        Returns:
            CPF formatado ou string vazia se inválido
        """
        clean = CPFValidator.clean_cpf(cpf)
        
        if len(clean) != 11:
            return ""
        
        return f"{clean[:3]}.{clean[3:6]}.{clean[6:9]}-{clean[9:]}"
    
    @staticmethod
    def calculate_check_digit(cpf_digits: str, position: int) -> int:
        """
        Calcula dígito verificador do CPF
        
        Args:
            cpf_digits: Primeiros 9 ou 10 dígitos do CPF
            position: Posição do dígito (10 ou 11)
            
        Returns:
            Dígito verificador calculado
        """
        total = 0
        
        for i, digit in enumerate(cpf_digits):
            total += int(digit) * (position - i)
        
        remainder = total % 11
        
        return 0 if remainder < 2 else 11 - remainder
    
    @staticmethod
    def validate_cpf(cpf: Union[str, int]) -> bool:
        """
        Valida CPF brasileiro completo
        
        Args:
            cpf: CPF para validação
            
        Returns:
            True se CPF válido, False caso contrário
        """
        # Limpa e converte para string
        clean_cpf = CPFValidator.clean_cpf(str(cpf))
        
        # Verifica se tem 11 dígitos
        if len(clean_cpf) != 11:
            return False
        
        # Verifica se não é um CPF inválido conhecido
        if clean_cpf in CPFValidator.INVALID_CPFS:
            return False
        
        # Calcula primeiro dígito verificador
        first_digit = CPFValidator.calculate_check_digit(clean_cpf[:9], 10)
        
        if int(clean_cpf[9]) != first_digit:
            return False
        
        # Calcula segundo dígito verificador
        second_digit = CPFValidator.calculate_check_digit(clean_cpf[:10], 11)
        
        if int(clean_cpf[10]) != second_digit:
            return False
        
        return True
    
    @staticmethod
    def validate_and_format(cpf: Union[str, int]) -> tuple[bool, str]:
        """
        Valida CPF e retorna formatado se válido
        
        Args:
            cpf: CPF para validação
            
        Returns:
            Tupla (is_valid, formatted_cpf)
        """
        is_valid = CPFValidator.validate_cpf(cpf)
        
        if is_valid:
            clean_cpf = CPFValidator.clean_cpf(str(cpf))
            formatted = CPFValidator.format_cpf(clean_cpf)
            return True, formatted
        
        return False, ""
    
    @staticmethod
    def generate_error_message(cpf: str) -> str:
        """
        Gera mensagem de erro específica para CPF inválido
        
        Args:
            cpf: CPF que falhou na validação
            
        Returns:
            Mensagem de erro detalhada
        """
        clean_cpf = CPFValidator.clean_cpf(cpf)
        
        if not clean_cpf:
            return "CPF é obrigatório"
        
        if len(clean_cpf) != 11:
            return "CPF deve conter exatamente 11 dígitos"
        
        if clean_cpf in CPFValidator.INVALID_CPFS:
            return "CPF inválido: todos os dígitos são iguais"
        
        return "CPF inválido: dígitos verificadores incorretos"


# Função de conveniência para uso direto
def validate_cpf(cpf: Union[str, int]) -> bool:
    """
    Função de conveniência para validação rápida de CPF
    
    Args:
        cpf: CPF para validação
        
    Returns:
        True se válido, False caso contrário
    """
    return CPFValidator.validate_cpf(cpf)


# Função para validação com formatação
def validate_and_format_cpf(cpf: Union[str, int]) -> tuple[bool, str]:
    """
    Função de conveniência para validação e formatação
    
    Args:
        cpf: CPF para validação
        
    Returns:
        Tupla (is_valid, formatted_cpf)
    """
    return CPFValidator.validate_and_format(cpf)