# 🤝 Contribuindo para o Video Converter

Obrigado por considerar contribuir para o Video Converter! Este documento fornece diretrizes e informações sobre como contribuir efetivamente para o projeto.

## 📋 Índice
- [Código de Conduta](#código-de-conduta)
- [Como Posso Contribuir?](#como-posso-contribuir)
- [Configuração do Ambiente de Desenvolvimento](#configuração-do-ambiente-de-desenvolvimento)
- [Processo de Desenvolvimento](#processo-de-desenvolvimento)
- [Diretrizes de Código](#diretrizes-de-código)
- [Testes](#testes)
- [Documentação](#documentação)
- [Processo de Pull Request](#processo-de-pull-request)

## 📜 Código de Conduta

Este projeto adere ao [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). Ao participar, você deve seguir este código. Por favor, reporte comportamentos inaceitáveis para [renejr@example.com].

## 🚀 Como Posso Contribuir?

### 🐛 Reportando Bugs
- Use o template de [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- Verifique se o bug já não foi reportado
- Inclua informações detalhadas do sistema e passos para reproduzir
- Adicione logs e screenshots quando possível

### 💡 Sugerindo Funcionalidades
- Use o template de [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
- Explique claramente o problema que a funcionalidade resolveria
- Descreva a solução proposta em detalhes
- Considere alternativas e impactos

### 🔧 Contribuindo com Código
- Correções de bugs
- Novas funcionalidades
- Melhorias de performance
- Refatoração de código
- Melhorias na documentação

### 📚 Melhorando a Documentação
- Correções de typos
- Esclarecimentos
- Exemplos adicionais
- Traduções

## 🛠️ Configuração do Ambiente de Desenvolvimento

### Pré-requisitos
- Python 3.8 ou superior
- Git
- FFmpeg (será instalado automaticamente)

### Configuração Inicial
```bash
# 1. Fork o repositório no GitHub
# 2. Clone seu fork
git clone https://github.com/SEU_USERNAME/videoconverter.git
cd videoconverter

# 3. Crie um ambiente virtual
python -m venv venv

# 4. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 5. Instale as dependências
pip install -r requirements.txt

# 6. Instale dependências de desenvolvimento
pip install pytest pytest-cov flake8 black bandit safety

# 7. Configure o remote upstream
git remote add upstream https://github.com/renejr/videoconverter.git
```

### Verificação da Instalação
```bash
# Execute os testes
pytest

# Verifique o linting
flake8 .

# Verifique a formatação
black --check .

# Execute a aplicação
python main_tkinter.py
```

## 🔄 Processo de Desenvolvimento

### 1. Criando uma Branch
```bash
# Atualize sua branch main
git checkout main
git pull upstream main

# Crie uma nova branch para sua funcionalidade/correção
git checkout -b feature/nome-da-funcionalidade
# ou
git checkout -b bugfix/nome-do-bug
```

### 2. Fazendo Mudanças
- Faça commits pequenos e focados
- Use mensagens de commit descritivas
- Siga as convenções de código do projeto

### 3. Testando
```bash
# Execute todos os testes
pytest

# Execute testes com cobertura
pytest --cov=core --cov=gui --cov=utils

# Teste manualmente a aplicação
python main_tkinter.py
```

### 4. Preparando para o Pull Request
```bash
# Formate o código
black .

# Verifique o linting
flake8 .

# Execute verificações de segurança
bandit -r .
safety check

# Atualize sua branch com as mudanças mais recentes
git fetch upstream
git rebase upstream/main
```

## 📝 Diretrizes de Código

### Estilo de Código
- Seguimos o [PEP 8](https://pep8.org/) para Python
- Use [Black](https://black.readthedocs.io/) para formatação automática
- Máximo de 88 caracteres por linha (configuração do Black)

### Convenções de Nomenclatura
- **Variáveis e funções**: `snake_case`
- **Classes**: `PascalCase`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Arquivos**: `snake_case.py`

### Estrutura de Código
```python
"""
Docstring do módulo explicando seu propósito.
"""

import os
import sys
from typing import Optional, List

# Imports de terceiros
import tkinter as tk
from tkinter import ttk

# Imports locais
from core.video_converter import VideoConverter
from utils.config import Config


class ExampleClass:
    """
    Docstring da classe explicando seu propósito.
    
    Args:
        param1: Descrição do parâmetro
        param2: Descrição do parâmetro
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        self.param1 = param1
        self.param2 = param2
    
    def example_method(self, input_value: str) -> bool:
        """
        Docstring do método explicando seu propósito.
        
        Args:
            input_value: Descrição do parâmetro
            
        Returns:
            Descrição do retorno
            
        Raises:
            ValueError: Quando input_value é inválido
        """
        if not input_value:
            raise ValueError("input_value não pode estar vazio")
        
        # Lógica do método
        return True
```

### Comentários
- Use docstrings para módulos, classes e funções
- Comentários em linha apenas quando necessário para clarificar lógica complexa
- Mantenha comentários atualizados com o código

## 🧪 Testes

### Estrutura de Testes
```
tests/
├── test_core/
│   ├── test_video_converter.py
│   └── test_queue_manager.py
├── test_gui/
│   └── test_main_window.py
├── test_utils/
│   ├── test_config.py
│   └── test_validators.py
└── conftest.py
```

### Escrevendo Testes
```python
import pytest
from unittest.mock import Mock, patch

from core.video_converter import VideoConverter


class TestVideoConverter:
    """Testes para a classe VideoConverter."""
    
    def setup_method(self):
        """Configuração executada antes de cada teste."""
        self.converter = VideoConverter()
    
    def test_validate_input_file_valid(self):
        """Testa validação com arquivo válido."""
        # Arrange
        valid_file = "test.mp4"
        
        # Act
        result = self.converter.validate_input_file(valid_file)
        
        # Assert
        assert result is True
    
    @patch('os.path.exists')
    def test_validate_input_file_not_exists(self, mock_exists):
        """Testa validação com arquivo inexistente."""
        # Arrange
        mock_exists.return_value = False
        invalid_file = "nonexistent.mp4"
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            self.converter.validate_input_file(invalid_file)
```

### Executando Testes
```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/test_core/test_video_converter.py

# Com cobertura
pytest --cov=core --cov-report=html

# Testes em modo verbose
pytest -v

# Parar no primeiro erro
pytest -x
```

## 📚 Documentação

### Docstrings
- Use o formato Google/NumPy para docstrings
- Documente todos os parâmetros, retornos e exceções
- Inclua exemplos quando apropriado

### README e Documentação
- Mantenha o README.md atualizado
- Adicione exemplos de uso para novas funcionalidades
- Documente mudanças breaking no changelog

## 🔀 Processo de Pull Request

### Antes de Submeter
- [ ] Código formatado com Black
- [ ] Linting passou (flake8)
- [ ] Todos os testes passam
- [ ] Cobertura de testes mantida ou melhorada
- [ ] Documentação atualizada
- [ ] Changelog atualizado (se aplicável)

### Submetendo o PR
1. **Push sua branch**:
   ```bash
   git push origin feature/nome-da-funcionalidade
   ```

2. **Crie o Pull Request** no GitHub usando o template

3. **Preencha o template** completamente:
   - Descrição clara das mudanças
   - Link para issues relacionadas
   - Tipo de mudança
   - Como foi testado
   - Screenshots (se aplicável)

4. **Aguarde a revisão**:
   - Responda aos comentários construtivamente
   - Faça mudanças solicitadas
   - Mantenha a discussão focada e respeitosa

### Processo de Revisão
- Pelo menos um maintainer deve aprovar o PR
- Todos os checks do CI devem passar
- Conflitos devem ser resolvidos
- O código deve seguir as diretrizes do projeto

### Após a Aprovação
- O PR será merged pelo maintainer
- A branch será deletada automaticamente
- Você pode deletar sua branch local:
  ```bash
  git checkout main
  git pull upstream main
  git branch -d feature/nome-da-funcionalidade
  ```

## 🏷️ Convenções de Commit

Use mensagens de commit claras e descritivas:

```
tipo(escopo): descrição breve

Descrição mais detalhada se necessário.

Fixes #123
```

### Tipos de Commit
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Mudanças na documentação
- `style`: Formatação, ponto e vírgula, etc
- `refactor`: Refatoração de código
- `test`: Adição ou correção de testes
- `chore`: Tarefas de manutenção

### Exemplos
```
feat(converter): adiciona suporte para codec AV1

Implementa suporte completo para codec AV1 incluindo:
- Detecção automática de suporte
- Configurações otimizadas
- Testes unitários

Fixes #45

fix(gui): corrige travamento ao cancelar conversão

O botão cancelar agora para corretamente o processo
de conversão sem causar travamento da interface.

Fixes #67

docs(readme): atualiza instruções de instalação

Adiciona instruções específicas para macOS e Linux.
```

## 🆘 Precisa de Ajuda?

- **Documentação**: Consulte o [README.md](README.md)
- **Issues**: Procure em [Issues existentes](https://github.com/renejr/videoconverter/issues)
- **Discussões**: Use [GitHub Discussions](https://github.com/renejr/videoconverter/discussions)
- **Suporte**: Crie uma [Support Question](.github/ISSUE_TEMPLATE/support_question.md)

## 🙏 Reconhecimentos

Obrigado a todos os contribuidores que ajudam a tornar o Video Converter melhor!

---

**Lembre-se**: Contribuições de todos os tipos são bem-vindas, desde correções de typos até grandes funcionalidades. Não hesite em contribuir!