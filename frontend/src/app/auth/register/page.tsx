'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { isValidEmail, validatePassword } from '@/lib/utils'
import { Eye, EyeOff, Mail, Lock, User, Shield, Phone } from 'lucide-react'
import type { PasswordValidation } from '@/types'
import { validateAndFormatCPF, formatCPF, applyCPFMask } from '@/utils/cpf-validator'
import { validateBirthDate, calculateAge } from '@/utils/age-validator'
import { ViaCEPService, formatCEP, applyCEPMask, validateCEPFormat } from '@/services/viacep-service'

/**
 * Página de registro de novo usuário
 * Inclui validação completa de formulário e verificação de força da senha
 */
export default function RegisterPage() {
  const { register, user, isLoading } = useAuth()
  const router = useRouter()

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirm_password: '',
    first_name: '',
    last_name: '',
    phone: '',
    cpf: '',
    date_of_birth: '',
    gender: 'M' as 'M' | 'F' | 'O',
    cep: '',
    address_street: '',
    address_number: '',
    address_complement: '',
    address_neighborhood: '',
    address_city: '',
    address_state: '',
    accept_terms: false,
    accept_privacy: false
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [passwordValidation, setPasswordValidation] = useState<PasswordValidation | null>(null)
  const [passwordStrength, setPasswordStrength] = useState<PasswordValidation | null>(null)
  const [isLoadingCEP, setIsLoadingCEP] = useState(false)
  const [addressData, setAddressData] = useState<any>(null)

  // Redireciona se já estiver logado
  useEffect(() => {
    if (user && !isLoading) {
      router.push('/dashboard')
    }
  }, [user, isLoading, router])

  // Valida força da senha em tempo real
  useEffect(() => {
    if (formData.password) {
      const strength = validatePassword(formData.password)
      setPasswordStrength(strength)
    } else {
      setPasswordStrength(null)
    }
  }, [formData.password])

  /**
   * Valida campos do formulário
   */
  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    // Email
    if (!formData.email) {
      newErrors.email = 'Email é obrigatório'
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = 'Email inválido'
    }

    // Primeiro nome
    if (!formData.first_name) {
      newErrors.first_name = 'Primeiro nome é obrigatório'
    } else if (formData.first_name.length < 2) {
      newErrors.first_name = 'Primeiro nome deve ter pelo menos 2 caracteres'
    }

    // Sobrenome
    if (!formData.last_name) {
      newErrors.last_name = 'Sobrenome é obrigatório'
    } else if (formData.last_name.length < 2) {
      newErrors.last_name = 'Sobrenome deve ter pelo menos 2 caracteres'
    }

    // Validação de CPF
    if (!formData.cpf) {
      newErrors.cpf = 'CPF é obrigatório'
    } else {
      const cpfValidation = validateAndFormatCPF(formData.cpf) as { isValid: boolean; formatted: string }
      if (!cpfValidation.isValid) {
        newErrors.cpf = 'CPF inválido'
      }
    }

    // Validação de data de nascimento
    if (!formData.date_of_birth) {
      newErrors.date_of_birth = 'Data de nascimento é obrigatória'
    } else {
      const ageValidation = validateBirthDate(formData.date_of_birth) as { isValid: boolean; age: number | null; errorMessage: string; isAdult: boolean }
      if (!ageValidation.isValid) {
        newErrors.date_of_birth = ageValidation.errorMessage || 'Data de nascimento inválida'
      }
    }

    // Validação de gênero
    if (!formData.gender) {
      newErrors.gender = 'Gênero é obrigatório'
    }

    // Validação de CEP
    if (!formData.cep) {
      newErrors.cep = 'CEP é obrigatório'
    } else if (!validateCEPFormat(formData.cep)) {
      newErrors.cep = 'CEP inválido'
    }

    // Validação de endereço
    if (!formData.address_street.trim()) {
      newErrors.address_street = 'Logradouro é obrigatório'
    }

    if (!formData.address_number.trim()) {
      newErrors.address_number = 'Número é obrigatório'
    }

    if (!formData.address_neighborhood.trim()) {
      newErrors.address_neighborhood = 'Bairro é obrigatório'
    }

    if (!formData.address_city.trim()) {
      newErrors.address_city = 'Cidade é obrigatória'
    }

    if (!formData.address_state.trim()) {
      newErrors.address_state = 'Estado é obrigatório'
    }

    // Senha
    if (!formData.password) {
      newErrors.password = 'Senha é obrigatória'
    } else {
      const passwordValidation = validatePassword(formData.password)
      if (!passwordValidation.isValid) {
        newErrors.password = 'Senha deve ter pelo menos 8 caracteres, incluindo maiúscula, minúscula e número'
      }
    }

    // Confirmação de senha
    if (!formData.confirm_password) {
      newErrors.confirm_password = 'Confirmação de senha é obrigatória'
    } else if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = 'Senhas não coincidem'
    }

    // Termos de uso
    if (!formData.accept_terms) {
      newErrors.accept_terms = 'Você deve aceitar os termos de uso'
    }

    // Política de privacidade
    if (!formData.accept_privacy) {
      newErrors.accept_privacy = 'Você deve aceitar a política de privacidade'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Função para buscar endereço por CEP
  const handleCEPSearch = async (cep: string) => {
    if (!validateCEPFormat(cep)) return

    setIsLoadingCEP(true)
    try {
      const viaCEPService = new ViaCEPService()
      const addressData = await viaCEPService.fetchAddressByCEP(cep)
      
      if (addressData && !addressData.erro) {
        setAddressData(addressData)
        setFormData(prev => ({
          ...prev,
          address_street: addressData.logradouro || '',
          address_neighborhood: addressData.bairro || '',
          address_city: addressData.localidade || '',
          address_state: addressData.uf || ''
        }))
        
        // Limpa erros de endereço se foram preenchidos automaticamente
        setErrors(prev => {
          const newErrors = { ...prev }
          if (addressData.logradouro) delete newErrors.address_street
          if (addressData.bairro) delete newErrors.address_neighborhood
          if (addressData.localidade) delete newErrors.address_city
          if (addressData.uf) delete newErrors.address_state
          return newErrors
        })
      }
    } catch (error) {
      console.error('Erro ao buscar CEP:', error)
    } finally {
      setIsLoadingCEP(false)
    }
  }

  /**
   * Manipula mudanças nos campos do formulário
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    let formattedValue: string | boolean = value

    // Para checkboxes, usa o valor checked
    if (type === 'checkbox') {
      formattedValue = checked
    } else {
      let processedValue = value
      
      // Aplicar máscaras específicas
      if (name === 'cpf') {
        processedValue = applyCPFMask(value)
      } else if (name === 'cep') {
        processedValue = applyCEPMask(value)
        
        // Buscar endereço automaticamente quando CEP estiver completo
        if (processedValue.length === 9) { // 00000-000
          handleCEPSearch(processedValue)
        }
      } else if (name === 'phone') {
        // Máscara para telefone (11) 99999-9999
        const numbers = value.replace(/\D/g, '')
        if (numbers.length <= 11) {
          if (numbers.length >= 11) {
            processedValue = numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
          } else if (numbers.length >= 7) {
            processedValue = numbers.replace(/(\d{2})(\d{4,5})(\d{0,4})/, '($1) $2-$3')
          } else if (numbers.length >= 3) {
            processedValue = numbers.replace(/(\d{2})(\d{0,5})/, '($1) $2')
          } else if (numbers.length >= 1) {
            processedValue = `(${numbers}`
          } else {
            processedValue = ''
          }
        }
      } else if (name === 'date_of_birth') {
        // Máscara para data DD/MM/AAAA
        const numbers = value.replace(/\D/g, '')
        if (numbers.length <= 8) {
          processedValue = numbers.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3')
            .replace(/(\d{2})(\d{2})(\d{0,4})/, '$1/$2/$3')
            .replace(/(\d{2})(\d{0,2})/, '$1/$2')
        }
      }
      
      formattedValue = processedValue
    }

    setFormData(prev => ({ ...prev, [name]: formattedValue }))
    
    // Remove erro do campo quando usuário começa a digitar
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  /**
   * Manipula submissão do formulário
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)

    try {
      const registerData = {
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirm_password,
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
        cpf: formData.cpf,
        date_of_birth: formData.date_of_birth,
        gender: formData.gender,
        cep: formData.cep,
        address_street: formData.address_street,
        address_number: formData.address_number,
        address_complement: formData.address_complement,
        address_neighborhood: formData.address_neighborhood,
        address_city: formData.address_city,
        address_state: formData.address_state,
        accept_terms: formData.accept_terms,
        accept_privacy: formData.accept_privacy,
      }

      await register(registerData)
      router.push('/dashboard')
    } catch (error: any) {
      // Erros são tratados pelo toast no apiClient
      if (error.errors) {
        setErrors(error.errors)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  /**
   * Renderiza indicador de força da senha
   */
  const renderPasswordStrength = () => {
    if (!passwordStrength) return null

    const { strength, requirements } = passwordStrength
    const colors: Record<PasswordValidation['strength'], string> = {
      weak: 'bg-red-500',
      medium: 'bg-yellow-500',
      strong: 'bg-green-500',
    }

    return (
      <div className="mt-2">
        <div className="flex space-x-1 mb-2">
          {[1, 2, 3].map((level) => (
            <div
              key={level}
              className={`h-1 flex-1 rounded ${
                level <= (strength === 'weak' ? 1 : strength === 'medium' ? 2 : 3)
                  ? colors[strength]
                  : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
        <div className="text-xs text-gray-600">
          <p className={`font-medium ${
            strength === 'weak' ? 'text-red-600' : 
            strength === 'medium' ? 'text-yellow-600' : 'text-green-600'
          }`}>
            Força: {strength === 'weak' ? 'Fraca' : strength === 'medium' ? 'Média' : 'Forte'}
          </p>
          <ul className="mt-1 space-y-1">
            <li className={requirements.minLength ? 'text-green-600' : 'text-red-600'}>
              ✓ Pelo menos 8 caracteres
            </li>
            <li className={requirements.hasUppercase ? 'text-green-600' : 'text-red-600'}>
              ✓ Letra maiúscula
            </li>
            <li className={requirements.hasLowercase ? 'text-green-600' : 'text-red-600'}>
              ✓ Letra minúscula
            </li>
            <li className={requirements.hasNumber ? 'text-green-600' : 'text-red-600'}>
              ✓ Número
            </li>
            <li className={requirements.hasSpecialChar ? 'text-green-600' : 'text-red-600'}>
              ✓ Caractere especial
            </li>
          </ul>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  if (user) {
    return null // Redirecionando...
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center">
            <Shield className="h-12 w-12 text-primary-600" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Crie sua conta
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Ou{' '}
            <Link
              href="/auth/login"
              className="font-medium text-primary-600 hover:text-primary-500"
            >
              faça login na sua conta existente
            </Link>
          </p>
        </div>

        {/* Formulário */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Primeiro nome */}
            <div>
              <label htmlFor="first_name" className="form-label">
                Primeiro nome
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  autoComplete="given-name"
                  required
                  className={`form-input pl-10 ${errors.first_name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="Seu primeiro nome"
                  value={formData.first_name}
                  onChange={handleChange}
                />
              </div>
              {errors.first_name && (
                <p className="form-error">{errors.first_name}</p>
              )}
            </div>

            {/* Sobrenome */}
            <div>
              <label htmlFor="last_name" className="form-label">
                Sobrenome
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  autoComplete="family-name"
                  required
                  className={`form-input pl-10 ${errors.last_name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="Seu sobrenome"
                  value={formData.last_name}
                  onChange={handleChange}
                />
              </div>
              {errors.last_name && (
                <p className="form-error">{errors.last_name}</p>
              )}
            </div>

            {/* Telefone */}
            <div>
              <label htmlFor="phone" className="form-label">
                Telefone (opcional)
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Phone className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  autoComplete="tel"
                  className={`form-input pl-10 ${errors.phone ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="(11) 99999-9999"
                  value={formData.phone}
                  onChange={handleChange}
                />
              </div>
              {errors.phone && (
                <p className="form-error">{errors.phone}</p>
              )}
            </div>

            {/* CPF */}
            <div>
              <label htmlFor="cpf" className="form-label">
                CPF
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="cpf"
                  name="cpf"
                  type="text"
                  autoComplete="off"
                  required
                  maxLength={14}
                  className={`form-input pl-10 ${errors.cpf ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="000.000.000-00"
                  value={formData.cpf}
                  onChange={handleChange}
                />
              </div>
              {errors.cpf && (
                <p className="form-error">{errors.cpf}</p>
              )}
            </div>

            {/* Data de Nascimento */}
            <div>
              <label htmlFor="date_of_birth" className="form-label">
                Data de Nascimento
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="date_of_birth"
                  name="date_of_birth"
                  type="text"
                  autoComplete="bday"
                  required
                  maxLength={10}
                  className={`form-input pl-10 ${errors.date_of_birth ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="DD/MM/AAAA"
                  value={formData.date_of_birth}
                  onChange={handleChange}
                />
              </div>
              {errors.date_of_birth && (
                <p className="form-error">{errors.date_of_birth}</p>
              )}
              {formData.date_of_birth && (
                <p className="text-xs text-gray-500 mt-1">
                  Idade: {calculateAge(formData.date_of_birth)} anos
                </p>
              )}
            </div>

            {/* Gênero */}
            <div>
              <label htmlFor="gender" className="form-label">
                Gênero
              </label>
              <select
                id="gender"
                name="gender"
                required
                className={`form-input ${errors.gender ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                value={formData.gender}
                onChange={handleChange}
              >
                <option value="M">Masculino</option>
                <option value="F">Feminino</option>
                <option value="O">Outro</option>
              </select>
              {errors.gender && (
                <p className="form-error">{errors.gender}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="form-label">
                Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className={`form-input pl-10 ${errors.email ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="seu@email.com"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
              {errors.email && (
                <p className="form-error">{errors.email}</p>
              )}
            </div>

            {/* Seção de Endereço */}
            <div className="border-t pt-6 mt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Endereço</h3>
              
              {/* CEP */}
              <div className="mb-4">
                <label htmlFor="cep" className="form-label">
                  CEP
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="cep"
                    name="cep"
                    type="text"
                    autoComplete="postal-code"
                    required
                    maxLength={9}
                    className={`form-input pl-10 ${errors.cep ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="00000-000"
                    value={formData.cep}
                    onChange={handleChange}
                  />
                  {isLoadingCEP && (
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                    </div>
                  )}
                </div>
                {errors.cep && (
                  <p className="form-error">{errors.cep}</p>
                )}
                {addressData && (
                  <p className="text-xs text-green-600 mt-1">
                    ✓ Endereço encontrado e preenchido automaticamente
                  </p>
                )}
              </div>

              {/* Logradouro e Número */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="md:col-span-2">
                  <label htmlFor="address_street" className="form-label">
                    Logradouro
                  </label>
                  <input
                    id="address_street"
                    name="address_street"
                    type="text"
                    autoComplete="street-address"
                    required
                    className={`form-input ${errors.address_street ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="Rua, Avenida, etc."
                    value={formData.address_street}
                    onChange={handleChange}
                  />
                  {errors.address_street && (
                    <p className="form-error">{errors.address_street}</p>
                  )}
                </div>
                <div>
                  <label htmlFor="address_number" className="form-label">
                    Número
                  </label>
                  <input
                    id="address_number"
                    name="address_number"
                    type="text"
                    autoComplete="off"
                    required
                    className={`form-input ${errors.address_number ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="123"
                    value={formData.address_number}
                    onChange={handleChange}
                  />
                  {errors.address_number && (
                    <p className="form-error">{errors.address_number}</p>
                  )}
                </div>
              </div>

              {/* Complemento */}
              <div className="mb-4">
                <label htmlFor="address_complement" className="form-label">
                  Complemento (opcional)
                </label>
                <input
                  id="address_complement"
                  name="address_complement"
                  type="text"
                  autoComplete="off"
                  className="form-input"
                  placeholder="Apartamento, bloco, etc."
                  value={formData.address_complement}
                  onChange={handleChange}
                />
              </div>

              {/* Bairro */}
              <div className="mb-4">
                <label htmlFor="address_neighborhood" className="form-label">
                  Bairro
                </label>
                <input
                  id="address_neighborhood"
                  name="address_neighborhood"
                  type="text"
                  autoComplete="off"
                  required
                  className={`form-input ${errors.address_neighborhood ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="Nome do bairro"
                  value={formData.address_neighborhood}
                  onChange={handleChange}
                />
                {errors.address_neighborhood && (
                  <p className="form-error">{errors.address_neighborhood}</p>
                )}
              </div>

              {/* Cidade e Estado */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label htmlFor="address_city" className="form-label">
                    Cidade
                  </label>
                  <input
                    id="address_city"
                    name="address_city"
                    type="text"
                    autoComplete="address-level2"
                    required
                    className={`form-input ${errors.address_city ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="Nome da cidade"
                    value={formData.address_city}
                    onChange={handleChange}
                  />
                  {errors.address_city && (
                    <p className="form-error">{errors.address_city}</p>
                  )}
                </div>
                <div>
                  <label htmlFor="address_state" className="form-label">
                    Estado
                  </label>
                  <select
                    id="address_state"
                    name="address_state"
                    autoComplete="address-level1"
                    required
                    className={`form-input ${errors.address_state ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                    value={formData.address_state}
                    onChange={handleChange}
                  >
                    <option value="">Selecione o estado</option>
                    <option value="AC">Acre</option>
                    <option value="AL">Alagoas</option>
                    <option value="AP">Amapá</option>
                    <option value="AM">Amazonas</option>
                    <option value="BA">Bahia</option>
                    <option value="CE">Ceará</option>
                    <option value="DF">Distrito Federal</option>
                    <option value="ES">Espírito Santo</option>
                    <option value="GO">Goiás</option>
                    <option value="MA">Maranhão</option>
                    <option value="MT">Mato Grosso</option>
                    <option value="MS">Mato Grosso do Sul</option>
                    <option value="MG">Minas Gerais</option>
                    <option value="PA">Pará</option>
                    <option value="PB">Paraíba</option>
                    <option value="PR">Paraná</option>
                    <option value="PE">Pernambuco</option>
                    <option value="PI">Piauí</option>
                    <option value="RJ">Rio de Janeiro</option>
                    <option value="RN">Rio Grande do Norte</option>
                    <option value="RS">Rio Grande do Sul</option>
                    <option value="RO">Rondônia</option>
                    <option value="RR">Roraima</option>
                    <option value="SC">Santa Catarina</option>
                    <option value="SP">São Paulo</option>
                    <option value="SE">Sergipe</option>
                    <option value="TO">Tocantins</option>
                  </select>
                  {errors.address_state && (
                    <p className="form-error">{errors.address_state}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Seção de Segurança */}
            <div className="border-t pt-6 mt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Segurança</h3>
              
              {/* Senha */}
              <div className="mb-4">
              <label htmlFor="password" className="form-label">
                Senha
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  className={`form-input pl-10 pr-10 ${errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="Sua senha"
                  value={formData.password}
                  onChange={handleChange}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
              {renderPasswordStrength()}
              {errors.password && (
                <p className="form-error">{errors.password}</p>
              )}
            </div>

              {/* Confirmação de senha */}
              <div>
                <label htmlFor="confirm_password" className="form-label">
                  Confirmar senha
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="confirm_password"
                    name="confirm_password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    className={`form-input pl-10 pr-10 ${errors.confirm_password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="Confirme sua senha"
                    value={formData.confirm_password}
                    onChange={handleChange}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    ) : (
                      <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>
                </div>
                {errors.confirm_password && (
                  <p className="form-error">{errors.confirm_password}</p>
                )}
              </div>
            </div>
          </div>

          {/* Aceite dos termos */}
          <div className="space-y-3">
            <div className="flex items-start">
              <input
                id="accept_terms"
                name="accept_terms"
                type="checkbox"
                checked={formData.accept_terms}
                onChange={handleChange}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="accept_terms" className="ml-2 block text-sm text-gray-900">
                Eu concordo com os{' '}
                <Link href="/terms" className="text-primary-600 hover:text-primary-500">
                  Termos de Uso
                </Link>
              </label>
            </div>
            {errors.accept_terms && (
              <p className="form-error">{errors.accept_terms}</p>
            )}

            <div className="flex items-start">
              <input
                id="accept_privacy"
                name="accept_privacy"
                type="checkbox"
                checked={formData.accept_privacy}
                onChange={handleChange}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="accept_privacy" className="ml-2 block text-sm text-gray-900">
                Eu concordo com a{' '}
                <Link href="/privacy" className="text-primary-600 hover:text-primary-500">
                  Política de Privacidade
                </Link>
              </label>
            </div>
            {errors.accept_privacy && (
              <p className="form-error">{errors.accept_privacy}</p>
            )}
          </div>

          {/* Botão de submit */}
          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <div className="loading-spinner"></div>
              ) : (
                'Criar conta'
              )}
            </button>
          </div>
        </form>

        {/* Links adicionais */}
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Já tem uma conta?{' '}
            <Link
              href="/auth/login"
              className="font-medium text-primary-600 hover:text-primary-500"
            >
              Faça login
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}