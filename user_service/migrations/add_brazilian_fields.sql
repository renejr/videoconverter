-- =====================================================
-- MIGRAÇÃO: Campos Brasileiros para Cadastro de Usuário
-- Data: 2024
-- Descrição: Adiciona campos específicos para usuários brasileiros
-- =====================================================

USE vod_users;

-- Adicionar campos específicos brasileiros
ALTER TABLE users 
ADD COLUMN cpf VARCHAR(11) NOT NULL UNIQUE COMMENT 'CPF do usuário (apenas números, validado)',
ADD COLUMN gender VARCHAR(20) NOT NULL COMMENT 'Gênero: Masculino, Feminino, Não-binário, Prefiro não informar';

-- Adicionar campos de endereço (integração ViaCEP)
ALTER TABLE users 
ADD COLUMN cep VARCHAR(8) NOT NULL COMMENT 'CEP (apenas números)',
ADD COLUMN address_street VARCHAR(255) NOT NULL COMMENT 'Logradouro (preenchido via ViaCEP)',
ADD COLUMN address_number VARCHAR(10) NOT NULL COMMENT 'Número da residência',
ADD COLUMN address_complement VARCHAR(100) NULL COMMENT 'Complemento do endereço (opcional)',
ADD COLUMN address_neighborhood VARCHAR(100) NOT NULL COMMENT 'Bairro (preenchido via ViaCEP)',
ADD COLUMN address_city VARCHAR(100) NOT NULL COMMENT 'Cidade (preenchido via ViaCEP)',
ADD COLUMN address_state VARCHAR(2) NOT NULL COMMENT 'Estado - sigla (preenchido via ViaCEP)';

-- Modificar campo date_of_birth para obrigatório (validação 18+)
ALTER TABLE users 
MODIFY COLUMN date_of_birth DATE NOT NULL COMMENT 'Data de nascimento (obrigatório - validação 18+)';

-- Adicionar índices para otimização
CREATE INDEX idx_cpf ON users(cpf);
CREATE INDEX idx_cep ON users(cep);
CREATE INDEX idx_gender ON users(gender);
CREATE INDEX idx_birth_date ON users(date_of_birth);

-- Adicionar constraint para validação de gênero
ALTER TABLE users 
ADD CONSTRAINT chk_gender 
CHECK (gender IN ('Masculino', 'Feminino', 'Não-binário', 'Prefiro não informar'));

-- Adicionar constraint para validação de estado brasileiro
ALTER TABLE users 
ADD CONSTRAINT chk_state 
CHECK (address_state IN (
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
));

-- Comentário da migração
ALTER TABLE users COMMENT = 'Tabela principal de usuários - informações básicas, perfil e dados brasileiros';

-- =====================================================
-- ROLLBACK (caso necessário)
-- =====================================================
/*
-- Para reverter esta migração:

ALTER TABLE users 
DROP CONSTRAINT chk_gender,
DROP CONSTRAINT chk_state;

DROP INDEX idx_cpf ON users;
DROP INDEX idx_cep ON users;
DROP INDEX idx_gender ON users;
DROP INDEX idx_birth_date ON users;

ALTER TABLE users 
DROP COLUMN cpf,
DROP COLUMN gender,
DROP COLUMN cep,
DROP COLUMN address_street,
DROP COLUMN address_number,
DROP COLUMN address_complement,
DROP COLUMN address_neighborhood,
DROP COLUMN address_city,
DROP COLUMN address_state;

ALTER TABLE users 
MODIFY COLUMN date_of_birth DATE NULL COMMENT 'Data de nascimento (opcional)';
*/