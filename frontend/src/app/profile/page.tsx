'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { apiClient } from '@/lib/api'
import { isValidEmail, validatePassword } from '@/lib/utils'
import {
  User,
  Mail,
  Phone,
  Lock,
  Save,
  ArrowLeft,
  Eye,
  EyeOff,
  Shield,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react'
import type { ProfileUpdateData, PasswordChangeData } from '@/types'

/**
 * Página de perfil do usuário
 * Permite editar informações pessoais e alterar senha
 */
export default function ProfilePage() {
  const { user, updateUser, isLoading } = useAuth()
  const router = useRouter()
  
  // Estados do formulário de perfil
  const [profileData, setProfileData] = useState<ProfileUpdateData>({
    full_name: '',
    username: '',
    phone: '',
  })
  const [profileErrors, setProfileErrors] = useState<Partial<ProfileUpdateData>>({})
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false)

  // Estados do formulário de senha
  const [passwordData, setPasswordData] = useState<PasswordChangeData>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [passwordErrors, setPasswordErrors] = useState<Partial<PasswordChangeData>>({})
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  })

  // Estados de sucesso
  const [profileSuccess, setProfileSuccess] = useState(false)
  const [passwordSuccess, setPasswordSuccess] = useState(false)

  // Redireciona se não estiver logado
  useEffect(() => {
    if (!user && !isLoading) {
      router.push('/auth/login')
    }
  }, [user, isLoading, router])

  // Preenche dados do perfil quando o usuário carrega
  useEffect(() => {
    if (user) {
      setProfileData({
        full_name: user.full_name || '',
        username: user.username || '',
        phone: user.phone || '',
      })
    }
  }, [user])

  /**
   * Valida dados do perfil
   */
  const validateProfileData = (): boolean => {
    const errors: Partial<ProfileUpdateData> = {}

    if (!profileData.full_name?.trim()) {
      errors.full_name = 'Nome completo é obrigatório'
    }

    if (!profileData.username?.trim()) {
      errors.username = 'Nome de usuário é obrigatório'
    } else if (profileData.username.length < 3) {
      errors.username = 'Nome de usuário deve ter pelo menos 3 caracteres'
    }

    setProfileErrors(errors)
    return Object.keys(errors).length === 0
  }

  /**
   * Valida dados da senha
   */
  const validatePasswordData = (): boolean => {
    const errors: Partial<PasswordChangeData> = {}

    if (!passwordData.current_password) {
      errors.current_password = 'Senha atual é obrigatória'
    }

    if (!passwordData.new_password) {
      errors.new_password = 'Nova senha é obrigatória'
    } else {
      const passwordValidation = validatePassword(passwordData.new_password)
      if (!passwordValidation.isValid) {
        errors.new_password = 'A senha deve atender aos requisitos mínimos de segurança'
      }
    }

    if (!passwordData.confirm_password) {
      errors.confirm_password = 'Confirmação de senha é obrigatória'
    } else if (passwordData.new_password !== passwordData.confirm_password) {
      errors.confirm_password = 'Senhas não coincidem'
    }

    setPasswordErrors(errors)
    return Object.keys(errors).length === 0
  }

  /**
   * Atualiza perfil do usuário
   */
  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setProfileSuccess(false)

    if (!validateProfileData()) return

    setIsUpdatingProfile(true)
    try {
      const updatedUser = await apiClient.updateProfile(profileData)
      updateUser(updatedUser)
      setProfileSuccess(true)
      setTimeout(() => setProfileSuccess(false), 3000)
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setProfileErrors({ username: error.response.data.detail })
      }
    } finally {
      setIsUpdatingProfile(false)
    }
  }

  /**
   * Altera senha do usuário
   */
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordSuccess(false)

    if (!validatePasswordData()) return

    setIsChangingPassword(true)
    try {
      await apiClient.changePassword(passwordData)
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      })
      setPasswordSuccess(true)
      setTimeout(() => setPasswordSuccess(false), 3000)
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setPasswordErrors({ current_password: error.response.data.detail })
      }
    } finally {
      setIsChangingPassword(false)
    }
  }

  /**
   * Alterna visibilidade da senha
   */
  const togglePasswordVisibility = (field: keyof typeof showPasswords) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }))
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  if (!user) {
    return null // Redirecionando...
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-6">
            <button
              onClick={() => router.push('/dashboard')}
              className="mr-4 p-2 text-gray-500 hover:text-gray-700 rounded-md"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                Perfil do Usuário
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Formulário de Perfil */}
          <div className="card">
            <div className="flex items-center mb-6">
              <User className="h-6 w-6 text-primary-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">
                Informações Pessoais
              </h2>
            </div>

            {profileSuccess && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-center">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                <span className="text-sm text-green-800">
                  Perfil atualizado com sucesso!
                </span>
              </div>
            )}

            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome completo
                </label>
                <input
                  type="text"
                  value={profileData.full_name || ''}
                  onChange={(e) => setProfileData(prev => ({ ...prev, full_name: e.target.value }))}
                  className={`input ${profileErrors.full_name ? 'border-red-300' : ''}`}
                  placeholder="Seu nome completo"
                />
                {profileErrors.full_name && (
                  <p className="mt-1 text-sm text-red-600">{profileErrors.full_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome de usuário
                </label>
                <input
                  type="text"
                  value={profileData.username || ''}
                  onChange={(e) => setProfileData(prev => ({ ...prev, username: e.target.value }))}
                  className={`input ${profileErrors.username ? 'border-red-300' : ''}`}
                  placeholder="Seu nome de usuário"
                />
                {profileErrors.username && (
                  <p className="mt-1 text-sm text-red-600">{profileErrors.username}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={user.email}
                  disabled
                  className="input bg-gray-50 text-gray-500 cursor-not-allowed"
                />
                <p className="mt-1 text-xs text-gray-500">
                  O email não pode ser alterado
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone (opcional)
                </label>
                <input
                  type="tel"
                  value={profileData.phone || ''}
                  onChange={(e) => setProfileData(prev => ({ ...prev, phone: e.target.value }))}
                  className="input"
                  placeholder="(11) 99999-9999"
                />
              </div>

              <button
                type="submit"
                disabled={isUpdatingProfile}
                className="btn-primary w-full"
              >
                {isUpdatingProfile ? (
                  <div className="loading-spinner h-4 w-4 mr-2"></div>
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Salvar alterações
              </button>
            </form>
          </div>

          {/* Formulário de Senha */}
          <div className="card">
            <div className="flex items-center mb-6">
              <Lock className="h-6 w-6 text-primary-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">
                Alterar Senha
              </h2>
            </div>

            {passwordSuccess && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-center">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                <span className="text-sm text-green-800">
                  Senha alterada com sucesso!
                </span>
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Senha atual
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.current ? 'text' : 'password'}
                    value={passwordData.current_password || ''}
                    onChange={(e) => setPasswordData(prev => ({ ...prev, current_password: e.target.value }))}
                    className={`input pr-10 ${passwordErrors.current_password ? 'border-red-300' : ''}`}
                    placeholder="Sua senha atual"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('current')}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.current ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                {passwordErrors.current_password && (
                  <p className="mt-1 text-sm text-red-600">{passwordErrors.current_password}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nova senha
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.new ? 'text' : 'password'}
                    value={passwordData.new_password || ''}
                    onChange={(e) => setPasswordData(prev => ({ ...prev, new_password: e.target.value }))}
                    className={`input pr-10 ${passwordErrors.new_password ? 'border-red-300' : ''}`}
                    placeholder="Sua nova senha"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('new')}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.new ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                {passwordErrors.new_password && (
                  <p className="mt-1 text-sm text-red-600">{passwordErrors.new_password}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirmar nova senha
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.confirm ? 'text' : 'password'}
                    value={passwordData.confirm_password || ''}
                    onChange={(e) => setPasswordData(prev => ({ ...prev, confirm_password: e.target.value }))}
                    className={`input pr-10 ${passwordErrors.confirm_password ? 'border-red-300' : ''}`}
                    placeholder="Confirme sua nova senha"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('confirm')}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.confirm ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                {passwordErrors.confirm_password && (
                  <p className="mt-1 text-sm text-red-600">{passwordErrors.confirm_password}</p>
                )}
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <div className="flex">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2 flex-shrink-0" />
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium mb-1">Requisitos da senha:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Pelo menos 8 caracteres</li>
                      <li>Pelo menos uma letra maiúscula</li>
                      <li>Pelo menos uma letra minúscula</li>
                      <li>Pelo menos um número</li>
                      <li>Pelo menos um caractere especial</li>
                    </ul>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isChangingPassword}
                className="btn-primary w-full"
              >
                {isChangingPassword ? (
                  <div className="loading-spinner h-4 w-4 mr-2"></div>
                ) : (
                  <Lock className="h-4 w-4 mr-2" />
                )}
                Alterar senha
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  )
}