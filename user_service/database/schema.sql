-- =====================================================
-- ESQUEMA MYSQL COMPLETO - DOMÍNIO A
-- Sistema de Identidade e Transações para Plataforma VOD
-- =====================================================

-- Criação do banco de dados
CREATE DATABASE IF NOT EXISTS vod_users 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE vod_users;

-- =====================================================
-- TABELA: users
-- Armazena informações básicas dos usuários
-- =====================================================
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    country_code CHAR(2) DEFAULT 'BR',
    language_preference CHAR(5) DEFAULT 'pt-BR',
    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    
    -- Índices para otimização de consultas
    INDEX idx_email (email),
    INDEX idx_active_verified (is_active, is_verified),
    INDEX idx_created_at (created_at),
    INDEX idx_last_login (last_login_at)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Tabela principal de usuários - informações básicas e perfil';

-- =====================================================
-- TABELA: credentials
-- Armazena credenciais de autenticação dos usuários
-- =====================================================
CREATE TABLE credentials (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255) NULL,
    recovery_codes JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Chave estrangeira
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Índices
    INDEX idx_user_id (user_id),
    INDEX idx_password_changed (password_changed_at),
    INDEX idx_locked_until (locked_until)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Credenciais de autenticação e segurança dos usuários';

-- =====================================================
-- TABELA: plans
-- Define os planos de assinatura disponíveis
-- =====================================================
CREATE TABLE plans (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2) NOT NULL,
    price_yearly DECIMAL(10,2),
    currency CHAR(3) DEFAULT 'BRL',
    max_concurrent_streams INT DEFAULT 1,
    max_devices INT DEFAULT 2,
    video_quality ENUM('SD', 'HD', 'FHD', '4K') DEFAULT 'HD',
    download_enabled BOOLEAN DEFAULT FALSE,
    ads_enabled BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    trial_days INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices
    INDEX idx_active (is_active),
    INDEX idx_price_monthly (price_monthly),
    INDEX idx_name (name)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Planos de assinatura disponíveis na plataforma';

-- =====================================================
-- TABELA: subscriptions
-- Gerencia as assinaturas ativas dos usuários
-- =====================================================
CREATE TABLE subscriptions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    plan_id BIGINT UNSIGNED NOT NULL,
    status ENUM('active', 'cancelled', 'suspended', 'expired', 'trial') DEFAULT 'trial',
    billing_cycle ENUM('monthly', 'yearly') DEFAULT 'monthly',
    start_date DATE NOT NULL,
    end_date DATE,
    trial_end_date DATE,
    auto_renew BOOLEAN DEFAULT TRUE,
    cancellation_reason TEXT NULL,
    cancelled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Chaves estrangeiras
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE RESTRICT,
    
    -- Índices
    INDEX idx_user_id (user_id),
    INDEX idx_plan_id (plan_id),
    INDEX idx_status (status),
    INDEX idx_end_date (end_date),
    INDEX idx_trial_end (trial_end_date),
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Assinaturas dos usuários e seus status';

-- =====================================================
-- TABELA: payments
-- Registra todos os pagamentos realizados
-- =====================================================
CREATE TABLE payments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    subscription_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency CHAR(3) DEFAULT 'BRL',
    payment_method ENUM('credit_card', 'debit_card', 'pix', 'boleto', 'paypal') NOT NULL,
    payment_provider VARCHAR(50) NOT NULL,
    provider_transaction_id VARCHAR(255),
    status ENUM('pending', 'processing', 'completed', 'failed', 'refunded', 'cancelled') DEFAULT 'pending',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    processed_at TIMESTAMP NULL,
    failure_reason TEXT NULL,
    refund_amount DECIMAL(10,2) DEFAULT 0.00,
    refunded_at TIMESTAMP NULL,
    metadata JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Chaves estrangeiras
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Índices
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_payment_date (payment_date),
    INDEX idx_due_date (due_date),
    INDEX idx_provider_transaction (provider_transaction_id),
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Registro de todos os pagamentos e transações financeiras';

-- =====================================================
-- TABELA: invoices
-- Faturas geradas para os usuários
-- =====================================================
CREATE TABLE invoices (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    subscription_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    payment_id BIGINT UNSIGNED NULL,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    currency CHAR(3) DEFAULT 'BRL',
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('draft', 'sent', 'paid', 'overdue', 'cancelled') DEFAULT 'draft',
    paid_at TIMESTAMP NULL,
    pdf_url VARCHAR(500) NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Chaves estrangeiras
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL,
    
    -- Índices
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_user_id (user_id),
    INDEX idx_payment_id (payment_id),
    INDEX idx_invoice_number (invoice_number),
    INDEX idx_status (status),
    INDEX idx_due_date (due_date),
    INDEX idx_issue_date (issue_date),
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Faturas geradas para cobrança dos usuários';

-- =====================================================
-- TABELA: user_sessions
-- Controla sessões ativas dos usuários
-- =====================================================
CREATE TABLE user_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255) NOT NULL UNIQUE,
    device_info JSON NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Chave estrangeira
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Índices
    INDEX idx_user_id (user_id),
    INDEX idx_session_token (session_token),
    INDEX idx_refresh_token (refresh_token),
    INDEX idx_expires_at (expires_at),
    INDEX idx_last_activity (last_activity),
    INDEX idx_user_active (user_id, is_active)
) ENGINE=InnoDB 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci
  COMMENT='Sessões ativas dos usuários para controle de autenticação';

-- =====================================================
-- INSERÇÃO DE DADOS INICIAIS
-- =====================================================

-- Planos básicos da plataforma
INSERT INTO plans (name, description, price_monthly, price_yearly, max_concurrent_streams, max_devices, video_quality, download_enabled, ads_enabled, trial_days) VALUES
('Básico', 'Plano básico com qualidade SD e anúncios', 19.90, 199.00, 1, 2, 'SD', FALSE, TRUE, 7),
('Padrão', 'Plano padrão com qualidade HD sem anúncios', 29.90, 299.00, 2, 4, 'HD', TRUE, FALSE, 7),
('Premium', 'Plano premium com qualidade 4K e múltiplos dispositivos', 49.90, 499.00, 4, 8, '4K', TRUE, FALSE, 14);

-- =====================================================
-- TRIGGERS PARA AUDITORIA E INTEGRIDADE
-- =====================================================

-- Trigger para atualizar last_login_at automaticamente
DELIMITER //
CREATE TRIGGER update_last_login 
AFTER INSERT ON user_sessions
FOR EACH ROW
BEGIN
    UPDATE users 
    SET last_login_at = NEW.created_at 
    WHERE id = NEW.user_id;
END//
DELIMITER ;

-- Trigger para calcular total_amount nas invoices
DELIMITER //
CREATE TRIGGER calculate_invoice_total 
BEFORE INSERT ON invoices
FOR EACH ROW
BEGIN
    SET NEW.total_amount = NEW.amount + NEW.tax_amount;
END//

CREATE TRIGGER update_invoice_total 
BEFORE UPDATE ON invoices
FOR EACH ROW
BEGIN
    SET NEW.total_amount = NEW.amount + NEW.tax_amount;
END//
DELIMITER ;

-- =====================================================
-- VIEWS PARA CONSULTAS OTIMIZADAS
-- =====================================================

-- View para usuários ativos com suas assinaturas
CREATE VIEW active_users_with_subscriptions AS
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.is_active,
    u.created_at as user_created_at,
    s.id as subscription_id,
    s.status as subscription_status,
    s.start_date,
    s.end_date,
    p.name as plan_name,
    p.price_monthly,
    p.video_quality
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status IN ('active', 'trial')
LEFT JOIN plans p ON s.plan_id = p.id
WHERE u.is_active = TRUE;

-- View para relatório financeiro
CREATE VIEW financial_summary AS
SELECT 
    DATE_FORMAT(p.payment_date, '%Y-%m') as month_year,
    COUNT(*) as total_payments,
    SUM(CASE WHEN p.status = 'completed' THEN p.amount ELSE 0 END) as revenue,
    SUM(CASE WHEN p.status = 'failed' THEN p.amount ELSE 0 END) as failed_amount,
    AVG(CASE WHEN p.status = 'completed' THEN p.amount ELSE NULL END) as avg_payment
FROM payments p
GROUP BY DATE_FORMAT(p.payment_date, '%Y-%m')
ORDER BY month_year DESC;

-- =====================================================
-- COMENTÁRIOS FINAIS
-- =====================================================
/*
Este esquema implementa o Domínio A conforme especificado no documento:

1. CARACTERÍSTICAS IMPLEMENTADAS:
   - Garantias ACID através do InnoDB
   - Relacionamentos bem definidos com chaves estrangeiras
   - Índices otimizados para padrões de leitura intensiva
   - Estrutura normalizada para integridade de dados

2. SEGURANÇA:
   - Senhas com hash e salt
   - Controle de sessões
   - Auditoria através de timestamps
   - Suporte a 2FA

3. ESCALABILIDADE:
   - Índices compostos para consultas complexas
   - Views para consultas frequentes
   - Triggers para manutenção automática

4. FLEXIBILIDADE:
   - Campos JSON para metadados
   - Enums para status controlados
   - Suporte a múltiplas moedas e idiomas
*/