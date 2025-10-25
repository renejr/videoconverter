/**
 * Validador de Idade - Cliente (JavaScript)
 * Sistema de validação de idade mínima (18 anos) para cadastro
 */

/**
 * Idade mínima permitida para cadastro
 */
export const MINIMUM_AGE = 18;

/**
 * Idade máxima razoável (para detectar datas inválidas)
 */
export const MAXIMUM_AGE = 120;

/**
 * Calcula idade exata baseada na data de nascimento
 * @param {Date|string} birthDate - Data de nascimento
 * @returns {number} Idade em anos
 */
export function calculateAge(birthDate) {
    const birth = new Date(birthDate);
    const today = new Date();
    
    // Verifica se a data é válida
    if (isNaN(birth.getTime())) {
        throw new Error('Data de nascimento inválida');
    }
    
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    // Ajusta se ainda não fez aniversário este ano
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    
    return age;
}

/**
 * Verifica se a pessoa é maior de idade
 * @param {Date|string} birthDate - Data de nascimento
 * @returns {boolean} True se maior de idade
 */
export function isAdult(birthDate) {
    try {
        const age = calculateAge(birthDate);
        return age >= MINIMUM_AGE;
    } catch (error) {
        return false;
    }
}

/**
 * Valida data de nascimento completa
 * @param {Date|string} birthDate - Data de nascimento
 * @returns {object} Resultado da validação
 */
export function validateBirthDate(birthDate) {
    const result = {
        isValid: false,
        age: null,
        errorMessage: '',
        isAdult: false
    };
    
    if (!birthDate) {
        result.errorMessage = 'Data de nascimento é obrigatória';
        return result;
    }
    
    const birth = new Date(birthDate);
    const today = new Date();
    
    // Verifica se a data é válida
    if (isNaN(birth.getTime())) {
        result.errorMessage = 'Data de nascimento inválida';
        return result;
    }
    
    // Verifica se não é uma data futura
    if (birth > today) {
        result.errorMessage = 'Data de nascimento não pode ser no futuro';
        return result;
    }
    
    try {
        const age = calculateAge(birth);
        result.age = age;
        
        // Verifica idade máxima razoável
        if (age > MAXIMUM_AGE) {
            result.errorMessage = `Idade não pode ser superior a ${MAXIMUM_AGE} anos`;
            return result;
        }
        
        // Verifica idade mínima
        if (age < MINIMUM_AGE) {
            result.errorMessage = `Você deve ter pelo menos ${MINIMUM_AGE} anos para se cadastrar`;
            return result;
        }
        
        result.isValid = true;
        result.isAdult = true;
        
    } catch (error) {
        result.errorMessage = 'Erro ao calcular idade';
    }
    
    return result;
}

/**
 * Calcula data mínima de nascimento para idade mínima
 * @returns {Date} Data mínima de nascimento
 */
export function getMinimumBirthDate() {
    const today = new Date();
    const minDate = new Date(today);
    minDate.setFullYear(today.getFullYear() - MINIMUM_AGE);
    return minDate;
}

/**
 * Calcula data máxima de nascimento para idade máxima
 * @returns {Date} Data máxima de nascimento
 */
export function getMaximumBirthDate() {
    const today = new Date();
    const maxDate = new Date(today);
    maxDate.setFullYear(today.getFullYear() - MAXIMUM_AGE);
    return maxDate;
}

/**
 * Formata data mínima para input HTML
 * @returns {string} Data no formato YYYY-MM-DD
 */
export function getMinimumBirthDateForInput() {
    const minDate = getMinimumBirthDate();
    return minDate.toISOString().split('T')[0];
}

/**
 * Formata data máxima para input HTML
 * @returns {string} Data no formato YYYY-MM-DD
 */
export function getMaximumBirthDateForInput() {
    const maxDate = getMaximumBirthDate();
    return maxDate.toISOString().split('T')[0];
}

/**
 * Obtém informações sobre idade e restrições
 * @param {Date|string} birthDate - Data de nascimento (opcional)
 * @returns {object} Informações sobre idade
 */
export function getAgeInfo(birthDate = null) {
    const info = {
        minimumAge: MINIMUM_AGE,
        maximumAge: MAXIMUM_AGE,
        minimumBirthDate: getMinimumBirthDate(),
        maximumBirthDate: getMaximumBirthDate(),
        minimumBirthDateForInput: getMinimumBirthDateForInput(),
        maximumBirthDateForInput: getMaximumBirthDateForInput()
    };
    
    if (birthDate) {
        const validation = validateBirthDate(birthDate);
        info.currentAge = validation.age;
        info.isValid = validation.isValid;
        info.isAdult = validation.isAdult;
        info.errorMessage = validation.errorMessage;
    }
    
    return info;
}

/**
 * Hook para validação de idade em React
 * @param {string} birthDate - Data de nascimento
 * @returns {object} Estado de validação
 */
export function useAgeValidation(birthDate) {
    const validation = validateBirthDate(birthDate);
    const ageInfo = getAgeInfo(birthDate);
    
    return {
        ...validation,
        ...ageInfo,
        yearsUntilAdult: validation.age !== null && validation.age < MINIMUM_AGE 
            ? MINIMUM_AGE - validation.age 
            : 0
    };
}

/**
 * Validador para formulários (compatível com react-hook-form)
 * @param {string} birthDate - Data de nascimento
 * @returns {boolean|string} True se válido, mensagem de erro se inválido
 */
export function birthDateValidator(birthDate) {
    if (!birthDate) return 'Data de nascimento é obrigatória';
    
    const validation = validateBirthDate(birthDate);
    
    return validation.isValid || validation.errorMessage;
}

/**
 * Formata idade para exibição
 * @param {number} age - Idade em anos
 * @returns {string} Idade formatada
 */
export function formatAge(age) {
    if (age === null || age === undefined) return '';
    
    if (age === 1) return '1 ano';
    
    return `${age} anos`;
}

/**
 * Calcula anos restantes até a maioridade
 * @param {Date|string} birthDate - Data de nascimento
 * @returns {number} Anos restantes (0 se já for maior de idade)
 */
export function yearsUntilAdult(birthDate) {
    try {
        const age = calculateAge(birthDate);
        return Math.max(0, MINIMUM_AGE - age);
    } catch (error) {
        return MINIMUM_AGE;
    }
}

// Exportação default para uso direto
export default {
    calculateAge,
    isAdult,
    validate: validateBirthDate,
    getMinimumBirthDate,
    getMaximumBirthDate,
    getMinimumBirthDateForInput,
    getMaximumBirthDateForInput,
    getAgeInfo,
    useValidation: useAgeValidation,
    validator: birthDateValidator,
    formatAge,
    yearsUntilAdult,
    MINIMUM_AGE,
    MAXIMUM_AGE
};