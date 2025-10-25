"""
Validador de Idade - Servidor
Sistema de validação de idade mínima (18 anos)
"""

from datetime import date, datetime
from typing import Union


class AgeValidator:
    """
    Classe para validação de idade mínima
    
    Implementa validação de idade baseada na data de nascimento
    considerando anos bissextos e diferentes formatos de data
    """
    
    MINIMUM_AGE = 18
    
    @staticmethod
    def calculate_age(birth_date: Union[date, str]) -> int:
        """
        Calcula idade exata baseada na data de nascimento
        
        Args:
            birth_date: Data de nascimento (date object ou string YYYY-MM-DD)
            
        Returns:
            Idade em anos completos
        """
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Formato de data inválido. Use YYYY-MM-DD")
        
        if not isinstance(birth_date, date):
            raise TypeError("Data de nascimento deve ser um objeto date ou string")
        
        today = date.today()
        
        # Calcula idade considerando se já fez aniversário este ano
        age = today.year - birth_date.year
        
        # Se ainda não fez aniversário este ano, subtrai 1
        if today.month < birth_date.month or \
           (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return age
    
    @staticmethod
    def is_adult(birth_date: Union[date, str]) -> bool:
        """
        Verifica se a pessoa é maior de idade (18+ anos)
        
        Args:
            birth_date: Data de nascimento
            
        Returns:
            True se maior de idade, False caso contrário
        """
        try:
            age = AgeValidator.calculate_age(birth_date)
            return age >= AgeValidator.MINIMUM_AGE
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_birth_date(birth_date: Union[date, str]) -> tuple[bool, str]:
        """
        Valida data de nascimento completa
        
        Args:
            birth_date: Data de nascimento para validação
            
        Returns:
            Tupla (is_valid, error_message)
        """
        if not birth_date:
            return False, "Data de nascimento é obrigatória"
        
        try:
            # Converte string para date se necessário
            if isinstance(birth_date, str):
                parsed_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            else:
                parsed_date = birth_date
            
            # Verifica se a data não é futura
            today = date.today()
            if parsed_date > today:
                return False, "Data de nascimento não pode ser futura"
            
            # Verifica se a data não é muito antiga (mais de 120 anos)
            max_age_date = date(today.year - 120, today.month, today.day)
            if parsed_date < max_age_date:
                return False, "Data de nascimento inválida (muito antiga)"
            
            # Verifica idade mínima
            age = AgeValidator.calculate_age(parsed_date)
            if age < AgeValidator.MINIMUM_AGE:
                years_missing = AgeValidator.MINIMUM_AGE - age
                return False, f"Idade mínima: {AgeValidator.MINIMUM_AGE} anos. Faltam {years_missing} ano(s)"
            
            return True, ""
            
        except ValueError:
            return False, "Formato de data inválido. Use YYYY-MM-DD"
        except Exception as e:
            return False, f"Erro na validação da data: {str(e)}"
    
    @staticmethod
    def get_minimum_birth_date() -> date:
        """
        Retorna a data de nascimento mínima permitida
        
        Returns:
            Data mínima para ter 18 anos hoje
        """
        today = date.today()
        return date(today.year - AgeValidator.MINIMUM_AGE, today.month, today.day)
    
    @staticmethod
    def format_minimum_date_for_input() -> str:
        """
        Retorna data mínima formatada para input HTML date
        
        Returns:
            String no formato YYYY-MM-DD
        """
        min_date = AgeValidator.get_minimum_birth_date()
        return min_date.strftime('%Y-%m-%d')
    
    @staticmethod
    def get_age_info(birth_date: Union[date, str]) -> dict:
        """
        Retorna informações completas sobre a idade
        
        Args:
            birth_date: Data de nascimento
            
        Returns:
            Dicionário com informações da idade
        """
        try:
            age = AgeValidator.calculate_age(birth_date)
            is_adult = age >= AgeValidator.MINIMUM_AGE
            
            return {
                'age': age,
                'is_adult': is_adult,
                'minimum_age': AgeValidator.MINIMUM_AGE,
                'years_to_minimum': max(0, AgeValidator.MINIMUM_AGE - age),
                'valid': is_adult
            }
        except Exception as e:
            return {
                'age': None,
                'is_adult': False,
                'minimum_age': AgeValidator.MINIMUM_AGE,
                'years_to_minimum': None,
                'valid': False,
                'error': str(e)
            }


# Funções de conveniência para uso direto
def validate_age(birth_date: Union[date, str]) -> bool:
    """
    Função de conveniência para validação rápida de idade
    
    Args:
        birth_date: Data de nascimento
        
    Returns:
        True se maior de idade, False caso contrário
    """
    return AgeValidator.is_adult(birth_date)


def calculate_age(birth_date: Union[date, str]) -> int:
    """
    Função de conveniência para cálculo de idade
    
    Args:
        birth_date: Data de nascimento
        
    Returns:
        Idade em anos
    """
    return AgeValidator.calculate_age(birth_date)