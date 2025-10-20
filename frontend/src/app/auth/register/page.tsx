'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { isValidEmail, validatePassword } from '@/lib/utils'
import { Eye, EyeOff, Mail, Lock, User, Shield, Phone } from 'lucide-react'
import type { PasswordValidation } from '@/types'

/**
 * Página de registro de novo usuário
 * Inclui validação completa de formulário e verificação de força da senha
 */
export default function RegisterPage() {
  const { register, user, isLoading } = useAuth()
  const router = useRouter()

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    phone: '',
    accept_terms: false,
    accept_privacy: false,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState<PasswordValidation | null>(null)

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
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Confirmação de senha é obrigatória'
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Senhas não coincidem'
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

  /**
   * Manipula mudanças nos campos do formulário
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target
    let formattedValue: string | boolean = value

    // Para checkboxes, usa o valor checked
    if (type === 'checkbox') {
      formattedValue = checked
    }
    // Formata telefone automaticamente
    else if (name === 'phone') {
      const cleaned = value.replace(/\D/g, '')
      if (cleaned.length <= 11) {
        if (cleaned.length <= 2) {
          formattedValue = cleaned
        } else if (cleaned.length <= 6) {
          formattedValue = `(${cleaned.slice(0, 2)}) ${cleaned.slice(2)}`
        } else if (cleaned.length <= 10) {
          formattedValue = `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 6)}-${cleaned.slice(6)}`
        } else {
          formattedValue = `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 7)}-${cleaned.slice(7, 11)}`
        }
      } else {
        return // Não permite mais de 11 dígitos
      }
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
        confirm_password: formData.confirmPassword,
        first_name: formData.first_name,
        last_name: formData.last_name,
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

            {/* Senha */}
            <div>
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
              <label htmlFor="confirmPassword" className="form-label">
                Confirmar senha
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  className={`form-input pl-10 pr-10 ${errors.confirmPassword ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="Confirme sua senha"
                  value={formData.confirmPassword}
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
              {errors.confirmPassword && (
                <p className="form-error">{errors.confirmPassword}</p>
              )}
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