/**
 * Validador de CPF - Cliente (JavaScript)
 * Sistema de validação completa de CPF brasileiro
 */

/**
 * CPFs inválidos conhecidos (todos os dígitos iguais)
 */
const INVALID_CPFS = new Set([
    '00000000000', '11111111111', '22222222222', '33333333333',
    '44444444444', '55555555555', '66666666666', '77777777777',
    '88888888888', '99999999999'
]);

/**
 * Remove formatação do CPF (pontos, hífens, espaços)
 * @param {string} cpf - CPF com ou sem formatação
 * @returns {string} CPF apenas com números
 */
export function cleanCPF(cpf) {
    if (!cpf) return '';
    
    // Remove tudo que não for dígito
    return cpf.toString().replace(/\D/g, '');
}

/**
 * Formata CPF no padrão XXX.XXX.XXX-XX
 * @param {string} cpf - CPF apenas com números
 * @returns {string} CPF formatado ou string vazia se inválido
 */
export function formatCPF(cpf) {
    const clean = cleanCPF(cpf);
    
    if (clean.length !== 11) return '';
    
    return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6, 9)}-${clean.slice(9)}`;
}

/**
 * Calcula dígito verificador do CPF
 * @param {string} cpfDigits - Primeiros 9 ou 10 dígitos do CPF
 * @param {number} position - Posição do dígito (10 ou 11)
 * @returns {number} Dígito verificador calculado
 */
function calculateCheckDigit(cpfDigits, position) {
    let total = 0;
    
    for (let i = 0; i < cpfDigits.length; i++) {
        total += parseInt(cpfDigits[i]) * (position - i);
    }
    
    const remainder = total % 11;
    
    return remainder < 2 ? 0 : 11 - remainder;
}

/**
 * Valida CPF brasileiro completo
 * @param {string|number} cpf - CPF para validação
 * @returns {boolean} True se CPF válido, False caso contrário
 */
export function validateCPF(cpf) {
    // Limpa e converte para string
    const cleanCpf = cleanCPF(cpf.toString());
    
    // Verifica se tem 11 dígitos
    if (cleanCpf.length !== 11) return false;
    
    // Verifica se não é um CPF inválido conhecido
    if (INVALID_CPFS.has(cleanCpf)) return false;
    
    // Calcula primeiro dígito verificador
    const firstDigit = calculateCheckDigit(cleanCpf.slice(0, 9), 10);
    
    if (parseInt(cleanCpf[9]) !== firstDigit) return false;
    
    // Calcula segundo dígito verificador
    const secondDigit = calculateCheckDigit(cleanCpf.slice(0, 10), 11);
    
    if (parseInt(cleanCpf[10]) !== secondDigit) return false;
    
    return true;
}

/**
 * Valida CPF e retorna formatado se válido
 * @param {string|number} cpf - CPF para validação
 * @returns {object} {isValid: boolean, formatted: string}
 */
export function validateAndFormatCPF(cpf) {
    const isValid = validateCPF(cpf);
    
    if (isValid) {
        const cleanCpf = cleanCPF(cpf.toString());
        const formatted = formatCPF(cleanCpf);
        return { isValid: true, formatted };
    }
    
    return { isValid: false, formatted: '' };
}

/**
 * Gera mensagem de erro específica para CPF inválido
 * @param {string} cpf - CPF que falhou na validação
 * @returns {string} Mensagem de erro detalhada
 */
export function generateCPFErrorMessage(cpf) {
    const cleanCpf = cleanCPF(cpf);
    
    if (!cleanCpf) {
        return 'CPF é obrigatório';
    }
    
    if (cleanCpf.length !== 11) {
        return 'CPF deve conter exatamente 11 dígitos';
    }
    
    if (INVALID_CPFS.has(cleanCpf)) {
        return 'CPF inválido: todos os dígitos são iguais';
    }
    
    return 'CPF inválido: dígitos verificadores incorretos';
}

/**
 * Aplica máscara de CPF em tempo real
 * @param {string} value - Valor atual do input
 * @returns {string} Valor com máscara aplicada
 */
export function applyCPFMask(value) {
    const clean = cleanCPF(value);
    
    if (clean.length <= 3) return clean;
    if (clean.length <= 6) return `${clean.slice(0, 3)}.${clean.slice(3)}`;
    if (clean.length <= 9) return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6)}`;
    
    return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6, 9)}-${clean.slice(9, 11)}`;
}

/**
 * Hook para validação de CPF em React
 * @param {string} cpf - CPF para validação
 * @returns {object} Estado de validação
 */
export function useCPFValidation(cpf) {
    const isValid = validateCPF(cpf);
    const errorMessage = isValid ? '' : generateCPFErrorMessage(cpf);
    const formatted = isValid ? formatCPF(cpf) : '';
    
    return {
        isValid,
        errorMessage,
        formatted,
        clean: cleanCPF(cpf)
    };
}

/**
 * Validador para formulários (compatível com react-hook-form)
 * @param {string} cpf - CPF para validação
 * @returns {boolean|string} True se válido, mensagem de erro se inválido
 */
export function cpfValidator(cpf) {
    if (!cpf) return 'CPF é obrigatório';
    
    const isValid = validateCPF(cpf);
    
    return isValid || generateCPFErrorMessage(cpf);
}

// Exportação default para uso direto
export default {
    validate: validateCPF,
    format: formatCPF,
    clean: cleanCPF,
    mask: applyCPFMask,
    validateAndFormat: validateAndFormatCPF,
    generateErrorMessage: generateCPFErrorMessage,
    validator: cpfValidator,
    useValidation: useCPFValidation
};