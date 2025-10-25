"""
Template Model - Modelo de Templates
Notification Service - Plataforma VOD
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

from database.connection import Base


class Template(Base):
    """
    Modelo para templates de notificação
    """
    __tablename__ = "templates"
    
    # Identificação
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Conteúdo
    subject_template = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    
    # Configurações
    category = Column(String(50), nullable=False, default="general")
    language = Column(String(10), nullable=False, default="pt-BR")
    variables = Column(JSON, default=list)  # Lista de variáveis necessárias
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # Templates do sistema não podem ser deletados
    
    # Versionamento
    version = Column(String(20), default="1.0", nullable=False)
    parent_template_id = Column(Integer, nullable=True)  # Para versionamento
    
    # Metadados
    template_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}', version='{self.version}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o template para dicionário
        """
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "subject_template": self.subject_template,
            "html_content": self.html_content,
            "text_content": self.text_content,
            "category": self.category,
            "language": self.language,
            "variables": self.variables,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "version": self.version,
            "parent_template_id": self.parent_template_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def validate_variables(self, template_data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Valida se todas as variáveis necessárias estão presentes
        
        Returns:
            tuple[bool, list[str]]: (is_valid, missing_variables)
        """
        if not self.variables:
            return True, []
        
        missing_vars = []
        for var in self.variables:
            if var not in template_data:
                missing_vars.append(var)
        
        return len(missing_vars) == 0, missing_vars
    
    def get_preview_data(self) -> Dict[str, Any]:
        """
        Retorna dados de exemplo para preview do template
        """
        preview_data = {}
        
        if self.variables:
            for var in self.variables:
                # Dados de exemplo baseados no nome da variável
                if "name" in var.lower():
                    preview_data[var] = "João Silva"
                elif "email" in var.lower():
                    preview_data[var] = "joao@example.com"
                elif "platform" in var.lower():
                    preview_data[var] = "Plataforma VOD"
                elif "url" in var.lower():
                    preview_data[var] = "https://example.com"
                elif "amount" in var.lower():
                    preview_data[var] = "29.90"
                elif "date" in var.lower():
                    preview_data[var] = datetime.now().strftime("%d/%m/%Y")
                elif "time" in var.lower():
                    preview_data[var] = datetime.now().strftime("%H:%M")
                else:
                    preview_data[var] = f"[{var}]"
        
        return preview_data