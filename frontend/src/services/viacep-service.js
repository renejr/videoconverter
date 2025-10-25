/**
 * Serviço ViaCEP - Cliente (JavaScript)
 * Integração com API ViaCEP para busca de endereços por CEP
 */

/**
 * URL base da API ViaCEP
 */
const VIACEP_BASE_URL = 'https://viacep.com.br/ws';

/**
 * Timeout padrão para requisições (em milissegundos)
 */
const DEFAULT_TIMEOUT = 10000;

/**
 * Estados brasileiros válidos
 */
export const BRAZILIAN_STATES = new Set([
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]);

/**
 * Classe para dados de endereço
 */
export class AddressData {
    constructor(data = {}) {
        this.cep = data.cep || '';
        this.logradouro = data.logradouro || '';
        this.complemento = data.complemento || '';
        this.bairro = data.bairro || '';
        this.localidade = data.localidade || '';
        this.uf = data.uf || '';
        this.ibge = data.ibge || '';
        this.gia = data.gia || '';
        this.ddd = data.ddd || '';
        this.siafi = data.siafi || '';
        this.erro = data.erro || false;
    }

    /**
     * Verifica se o endereço é válido
     * @returns {boolean} True se válido
     */
    isValid() {
        return !this.erro && this.cep && this.logradouro && this.bairro && this.localidade && this.uf;
    }

    /**
     * Formata endereço para exibição
     * @returns {string} Endereço formatado
     */
    getFormattedAddress() {
        if (!this.isValid()) return '';
        
        const parts = [this.logradouro, this.bairro, this.localidade, this.uf];
        return parts.filter(part => part).join(', ');
    }

    /**
     * Converte para objeto simples
     * @returns {object} Dados do endereço
     */
    toObject() {
        return {
            cep: this.cep,
            street: this.logradouro,
            complement: this.complemento,
            neighborhood: this.bairro,
            city: this.localidade,
            state: this.uf,
            ibge: this.ibge,
            ddd: this.ddd
        };
    }
}

/**
 * Remove formatação do CEP
 * @param {string} cep - CEP com ou sem formatação
 * @returns {string} CEP apenas com números
 */
export function cleanCEP(cep) {
    if (!cep) return '';
    return cep.toString().replace(/\D/g, '');
}

/**
 * Formata CEP no padrão XXXXX-XXX
 * @param {string} cep - CEP apenas com números
 * @returns {string} CEP formatado
 */
export function formatCEP(cep) {
    const clean = cleanCEP(cep);
    
    if (clean.length !== 8) return clean;
    
    return `${clean.slice(0, 5)}-${clean.slice(5)}`;
}

/**
 * Valida formato do CEP
 * @param {string} cep - CEP para validação
 * @returns {boolean} True se válido
 */
export function validateCEPFormat(cep) {
    const clean = cleanCEP(cep);
    
    // CEP deve ter exatamente 8 dígitos
    if (clean.length !== 8) return false;
    
    // CEP não pode ser todos zeros
    if (clean === '00000000') return false;
    
    // Verifica se é um número válido
    return /^\d{8}$/.test(clean);
}

/**
 * Aplica máscara de CEP em tempo real
 * @param {string} value - Valor atual do input
 * @returns {string} Valor com máscara aplicada
 */
export function applyCEPMask(value) {
    const clean = cleanCEP(value);
    
    if (clean.length <= 5) return clean;
    
    return `${clean.slice(0, 5)}-${clean.slice(5, 8)}`;
}

/**
 * Classe principal do serviço ViaCEP
 */
export class ViaCEPService {
    constructor(options = {}) {
        this.timeout = options.timeout || DEFAULT_TIMEOUT;
        this.baseUrl = options.baseUrl || VIACEP_BASE_URL;
    }

    /**
     * Busca endereço por CEP
     * @param {string} cep - CEP para busca
     * @returns {Promise<AddressData>} Dados do endereço
     */
    async fetchAddressByCEP(cep) {
        const cleanCep = cleanCEP(cep);
        
        if (!validateCEPFormat(cleanCep)) {
            throw new Error('CEP inválido: deve conter 8 dígitos');
        }

        const url = `${this.baseUrl}/${cleanCep}/json/`;
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.erro) {
                throw new Error('CEP não encontrado');
            }
            
            return new AddressData(data);
            
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Timeout: A busca por CEP demorou muito para responder');
            }
            
            if (error.message.includes('Failed to fetch')) {
                throw new Error('Erro de conexão: Verifique sua internet');
            }
            
            throw error;
        }
    }

    /**
     * Busca múltiplos CEPs
     * @param {string[]} ceps - Array de CEPs
     * @returns {Promise<AddressData[]>} Array de dados de endereço
     */
    async fetchMultipleCEPs(ceps) {
        const promises = ceps.map(cep => 
            this.fetchAddressByCEP(cep).catch(error => ({
                error: error.message,
                cep: cleanCEP(cep)
            }))
        );
        
        return Promise.all(promises);
    }

    /**
     * Busca endereço com retry automático
     * @param {string} cep - CEP para busca
     * @param {number} maxRetries - Número máximo de tentativas
     * @returns {Promise<AddressData>} Dados do endereço
     */
    async fetchAddressWithRetry(cep, maxRetries = 3) {
        let lastError;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await this.fetchAddressByCEP(cep);
            } catch (error) {
                lastError = error;
                
                if (attempt < maxRetries) {
                    // Aguarda antes de tentar novamente (backoff exponencial)
                    await new Promise(resolve => 
                        setTimeout(resolve, Math.pow(2, attempt) * 1000)
                    );
                }
            }
        }
        
        throw lastError;
    }
}

/**
 * Instância padrão do serviço
 */
export const viacepService = new ViaCEPService();

/**
 * Função de conveniência para busca rápida
 * @param {string} cep - CEP para busca
 * @returns {Promise<AddressData>} Dados do endereço
 */
export async function searchCEP(cep) {
    return viacepService.fetchAddressByCEP(cep);
}

/**
 * Hook para busca de CEP em React
 * @param {string} cep - CEP para busca
 * @returns {object} Estado da busca
 */
export function useCEPSearch(cep) {
    const [state, setState] = React.useState({
        loading: false,
        data: null,
        error: null,
        isValid: false
    });

    React.useEffect(() => {
        if (!cep || !validateCEPFormat(cep)) {
            setState({
                loading: false,
                data: null,
                error: null,
                isValid: false
            });
            return;
        }

        setState(prev => ({ ...prev, loading: true, error: null }));

        searchCEP(cep)
            .then(data => {
                setState({
                    loading: false,
                    data,
                    error: null,
                    isValid: data.isValid()
                });
            })
            .catch(error => {
                setState({
                    loading: false,
                    data: null,
                    error: error.message,
                    isValid: false
                });
            });
    }, [cep]);

    return state;
}

/**
 * Validador de CEP para formulários
 * @param {string} cep - CEP para validação
 * @returns {Promise<boolean|string>} True se válido, mensagem de erro se inválido
 */
export async function cepValidator(cep) {
    if (!cep) return 'CEP é obrigatório';
    
    if (!validateCEPFormat(cep)) {
        return 'CEP deve conter 8 dígitos';
    }
    
    try {
        const address = await searchCEP(cep);
        return address.isValid() || 'CEP não encontrado';
    } catch (error) {
        return `Erro ao validar CEP: ${error.message}`;
    }
}

/**
 * Gera mensagem de erro para CEP
 * @param {string} cep - CEP que falhou
 * @param {string} error - Erro ocorrido
 * @returns {string} Mensagem de erro
 */
export function generateCEPErrorMessage(cep, error) {
    const cleanCep = cleanCEP(cep);
    
    if (!cleanCep) {
        return 'CEP é obrigatório';
    }
    
    if (cleanCep.length !== 8) {
        return 'CEP deve conter exatamente 8 dígitos';
    }
    
    if (error.includes('não encontrado')) {
        return 'CEP não encontrado. Verifique se está correto';
    }
    
    if (error.includes('conexão')) {
        return 'Erro de conexão. Tente novamente';
    }
    
    if (error.includes('Timeout')) {
        return 'Busca demorou muito. Tente novamente';
    }
    
    return 'Erro ao buscar CEP. Tente novamente';
}

// Exportação default para uso direto
export default {
    service: viacepService,
    search: searchCEP,
    validate: validateCEPFormat,
    clean: cleanCEP,
    format: formatCEP,
    mask: applyCEPMask,
    validator: cepValidator,
    generateErrorMessage: generateCEPErrorMessage,
    useCEPSearch,
    AddressData,
    ViaCEPService,
    BRAZILIAN_STATES
};