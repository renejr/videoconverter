"""
Serviço de Integração ViaCEP
Sistema de busca automática de endereços por CEP
"""

import re
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class AddressData:
    """
    Classe para representar dados de endereço do ViaCEP
    """
    cep: str
    logradouro: str
    complemento: str
    bairro: str
    localidade: str  # cidade
    uf: str  # estado
    ibge: str
    gia: str
    ddd: str
    siafi: str
    erro: bool = False


class ViaCEPService:
    """
    Serviço para integração com API ViaCEP
    
    Fornece métodos para busca de endereços por CEP
    com validação e tratamento de erros
    """
    
    BASE_URL = "https://viacep.com.br/ws"
    TIMEOUT = 10  # segundos
    
    @staticmethod
    def clean_cep(cep: str) -> str:
        """
        Remove formatação do CEP (hífens, espaços)
        
        Args:
            cep: CEP com ou sem formatação
            
        Returns:
            CEP apenas com números
        """
        if not cep:
            return ""
        
        # Remove tudo que não for dígito
        return re.sub(r'\D', '', str(cep))
    
    @staticmethod
    def format_cep(cep: str) -> str:
        """
        Formata CEP no padrão XXXXX-XXX
        
        Args:
            cep: CEP apenas com números
            
        Returns:
            CEP formatado ou string vazia se inválido
        """
        clean = ViaCEPService.clean_cep(cep)
        
        if len(clean) != 8:
            return ""
        
        return f"{clean[:5]}-{clean[5:]}"
    
    @staticmethod
    def validate_cep_format(cep: str) -> bool:
        """
        Valida formato do CEP (8 dígitos)
        
        Args:
            cep: CEP para validação
            
        Returns:
            True se formato válido, False caso contrário
        """
        clean_cep = ViaCEPService.clean_cep(cep)
        return len(clean_cep) == 8 and clean_cep.isdigit()
    
    @staticmethod
    async def fetch_address_by_cep(cep: str) -> Optional[AddressData]:
        """
        Busca endereço por CEP na API ViaCEP (assíncrono)
        
        Args:
            cep: CEP para busca
            
        Returns:
            AddressData se encontrado, None se erro
        """
        # Valida formato do CEP
        if not ViaCEPService.validate_cep_format(cep):
            return None
        
        clean_cep = ViaCEPService.clean_cep(cep)
        url = f"{ViaCEPService.BASE_URL}/{clean_cep}/json/"
        
        try:
            timeout = aiohttp.ClientTimeout(total=ViaCEPService.TIMEOUT)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verifica se o CEP foi encontrado
                        if 'erro' in data and data['erro']:
                            return None
                        
                        return AddressData(
                            cep=data.get('cep', ''),
                            logradouro=data.get('logradouro', ''),
                            complemento=data.get('complemento', ''),
                            bairro=data.get('bairro', ''),
                            localidade=data.get('localidade', ''),
                            uf=data.get('uf', ''),
                            ibge=data.get('ibge', ''),
                            gia=data.get('gia', ''),
                            ddd=data.get('ddd', ''),
                            siafi=data.get('siafi', '')
                        )
                    
                    return None
                    
        except asyncio.TimeoutError:
            print(f"Timeout ao buscar CEP {clean_cep}")
            return None
        except aiohttp.ClientError as e:
            print(f"Erro de conexão ao buscar CEP {clean_cep}: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado ao buscar CEP {clean_cep}: {e}")
            return None
    
    @staticmethod
    def fetch_address_by_cep_sync(cep: str) -> Optional[AddressData]:
        """
        Busca endereço por CEP na API ViaCEP (síncrono)
        
        Args:
            cep: CEP para busca
            
        Returns:
            AddressData se encontrado, None se erro
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            ViaCEPService.fetch_address_by_cep(cep)
        )
    
    @staticmethod
    async def validate_and_fetch_address(cep: str) -> tuple[bool, Optional[AddressData], str]:
        """
        Valida CEP e busca endereço com tratamento de erros
        
        Args:
            cep: CEP para validação e busca
            
        Returns:
            Tupla (is_valid, address_data, error_message)
        """
        if not cep:
            return False, None, "CEP é obrigatório"
        
        if not ViaCEPService.validate_cep_format(cep):
            return False, None, "CEP deve conter exatamente 8 dígitos"
        
        address_data = await ViaCEPService.fetch_address_by_cep(cep)
        
        if address_data is None:
            return False, None, "CEP não encontrado ou inválido"
        
        # Verifica se o endereço tem informações mínimas
        if not address_data.logradouro or not address_data.bairro or not address_data.localidade:
            return False, None, "CEP encontrado mas com informações incompletas"
        
        return True, address_data, ""
    
    @staticmethod
    def validate_and_fetch_address_sync(cep: str) -> tuple[bool, Optional[AddressData], str]:
        """
        Versão síncrona da validação e busca de endereço
        
        Args:
            cep: CEP para validação e busca
            
        Returns:
            Tupla (is_valid, address_data, error_message)
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            ViaCEPService.validate_and_fetch_address(cep)
        )
    
    @staticmethod
    def format_address_for_display(address_data: AddressData) -> str:
        """
        Formata endereço para exibição
        
        Args:
            address_data: Dados do endereço
            
        Returns:
            Endereço formatado para exibição
        """
        parts = []
        
        if address_data.logradouro:
            parts.append(address_data.logradouro)
        
        if address_data.bairro:
            parts.append(address_data.bairro)
        
        if address_data.localidade and address_data.uf:
            parts.append(f"{address_data.localidade}/{address_data.uf}")
        
        if address_data.cep:
            formatted_cep = ViaCEPService.format_cep(address_data.cep)
            if formatted_cep:
                parts.append(f"CEP: {formatted_cep}")
        
        return " - ".join(parts)


# Funções de conveniência para uso direto
async def get_address_by_cep(cep: str) -> Optional[AddressData]:
    """
    Função de conveniência para busca assíncrona de endereço
    
    Args:
        cep: CEP para busca
        
    Returns:
        AddressData se encontrado, None caso contrário
    """
    return await ViaCEPService.fetch_address_by_cep(cep)


def get_address_by_cep_sync(cep: str) -> Optional[AddressData]:
    """
    Função de conveniência para busca síncrona de endereço
    
    Args:
        cep: CEP para busca
        
    Returns:
        AddressData se encontrado, None caso contrário
    """
    return ViaCEPService.fetch_address_by_cep_sync(cep)