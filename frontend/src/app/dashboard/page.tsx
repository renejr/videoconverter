'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { apiClient } from '@/lib/api'
import { formatDateTime, getRelativeTime, getInitials, stringToColor } from '@/lib/utils'
import {
  User,
  Settings,
  Shield,
  Monitor,
  LogOut,
  Mail,
  Phone,
  Calendar,
  MapPin,
  Globe,
  Smartphone,
  Trash2,
  AlertTriangle,
} from 'lucide-react'
import type { SessionSchema } from '@/types'

/**
 * Página do dashboard do usuário
 * Exibe informações do perfil, sessões ativas e estatísticas
 */
export default function DashboardPage() {
  const { user, logout, isLoading } = useAuth()
  const router = useRouter()
  const [sessions, setSessions] = useState<SessionSchema[]>([])
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [revokingSession, setRevokingSession] = useState<string | null>(null)

  // Redireciona se não estiver logado
  useEffect(() => {
    if (!user && !isLoading) {
      router.push('/auth/login')
    }
  }, [user, isLoading, router])

  // Carrega sessões do usuário
  useEffect(() => {
    if (user) {
      loadUserSessions()
    }
  }, [user])

  /**
   * Carrega sessões ativas do usuário
   */
  const loadUserSessions = async () => {
    try {
      const userSessions = await apiClient.getUserSessions()
      setSessions(userSessions)
    } catch (error) {
      console.error('Erro ao carregar sessões:', error)
    } finally {
      setLoadingSessions(false)
    }
  }

  /**
   * Revoga uma sessão específica
   */
  const handleRevokeSession = async (sessionId: string) => {
    setRevokingSession(sessionId)
    try {
      await apiClient.revokeSession(sessionId)
      setSessions(prev => prev.filter(session => session.session_id !== sessionId))
    } catch (error) {
      console.error('Erro ao revogar sessão:', error)
    } finally {
      setRevokingSession(null)
    }
  }

  /**
   * Revoga todas as sessões exceto a atual
   */
  const handleRevokeAllSessions = async () => {
    try {
      await apiClient.revokeAllSessions()
      setSessions(prev => prev.filter(session => session.is_current))
    } catch (error) {
      console.error('Erro ao revogar todas as sessões:', error)
    }
  }

  /**
   * Obtém ícone baseado no tipo de dispositivo
   */
  const getDeviceIcon = (deviceType?: string, deviceName?: string) => {
    // Verifica se é um dispositivo móvel baseado no tipo ou nome do dispositivo
    const isMobile = deviceType?.toLowerCase().includes('mobile') || 
                    deviceType?.toLowerCase().includes('phone') ||
                    deviceName?.toLowerCase().includes('mobile') ||
                    deviceName?.toLowerCase().includes('phone') ||
                    deviceName?.toLowerCase().includes('android') ||
                    deviceName?.toLowerCase().includes('iphone')
    
    if (isMobile) {
      return <Smartphone className="h-5 w-5" />
    }
    return <Monitor className="h-5 w-5" />
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
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                VidConv Portal
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div
                  className="h-8 w-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                  style={{ backgroundColor: stringToColor(user.full_name) }}
                >
                  {getInitials(user.full_name)}
                </div>
                <span className="text-sm font-medium text-gray-700">
                  {user.full_name}
                </span>
              </div>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-md"
                title="Sair"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">
            Bem-vindo de volta, {user.full_name}!
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Informações do Perfil */}
          <div className="lg:col-span-2">
            <div className="card">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">
                  Informações do Perfil
                </h2>
                <button
                  onClick={() => router.push('/profile')}
                  className="btn-secondary text-sm"
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Editar
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <User className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Nome completo</p>
                    <p className="text-sm text-gray-600">{user.full_name}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Mail className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Email</p>
                    <div className="flex items-center space-x-2">
                      <p className="text-sm text-gray-600">{user.email}</p>
                      {user.is_verified ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Verificado
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Não verificado
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <User className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Nome de usuário</p>
                    <p className="text-sm text-gray-600">@{user.username}</p>
                  </div>
                </div>

                {user.phone && (
                  <div className="flex items-center space-x-3">
                    <Phone className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">Telefone</p>
                      <p className="text-sm text-gray-600">{user.phone}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-center space-x-3">
                  <Calendar className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Membro desde</p>
                    <p className="text-sm text-gray-600">
                      {formatDateTime(user.created_at)}
                    </p>
                  </div>
                </div>

                {user.last_login && (
                  <div className="flex items-center space-x-3">
                    <Shield className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">Último login</p>
                      <p className="text-sm text-gray-600">
                        {getRelativeTime(user.last_login)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Estatísticas */}
          <div className="space-y-6">
            {/* Status da conta */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Status da Conta
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Conta ativa</span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    user.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {user.is_active ? 'Ativa' : 'Inativa'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Email verificado</span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    user.is_verified 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {user.is_verified ? 'Verificado' : 'Pendente'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Sessões ativas</span>
                  <span className="text-sm font-medium text-gray-900">
                    {sessions.length}
                  </span>
                </div>
              </div>
            </div>

            {/* Ações rápidas */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Ações Rápidas
              </h3>
              <div className="space-y-2">
                <button
                  onClick={() => router.push('/profile')}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md flex items-center"
                >
                  <Settings className="h-4 w-4 mr-3" />
                  Editar perfil
                </button>
                <button
                  onClick={() => router.push('/security')}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md flex items-center"
                >
                  <Shield className="h-4 w-4 mr-3" />
                  Configurações de segurança
                </button>
                {!user.is_verified && (
                  <button
                    onClick={() => apiClient.requestEmailVerification()}
                    className="w-full text-left px-3 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded-md flex items-center"
                  >
                    <Mail className="h-4 w-4 mr-3" />
                    Verificar email
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Sessões Ativas */}
        <div className="mt-8">
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">
                Sessões Ativas
              </h2>
              {sessions.length > 1 && (
                <button
                  onClick={handleRevokeAllSessions}
                  className="btn-danger text-sm"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Revogar todas
                </button>
              )}
            </div>

            {loadingSessions ? (
              <div className="flex justify-center py-8">
                <div className="loading-spinner"></div>
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8">
                <Monitor className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Nenhuma sessão ativa encontrada</p>
              </div>
            ) : (
              <div className="space-y-4">
                {sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`border rounded-lg p-4 ${
                      session.is_current 
                        ? 'border-primary-200 bg-primary-50' 
                        : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="text-gray-400">
                          {getDeviceIcon(session.device_type, session.device_name)}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <p className="text-sm font-medium text-gray-900">
                              {session.device_name || session.device_type || 'Dispositivo desconhecido'}
                            </p>
                            {session.is_current && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                                Sessão atual
                              </span>
                            )}
                          </div>
                          <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                            <span className="flex items-center">
                              <MapPin className="h-3 w-3 mr-1" />
                              {session.ip_address}
                            </span>
                            <span className="flex items-center">
                              <Calendar className="h-3 w-3 mr-1" />
                              {getRelativeTime(session.last_activity)}
                            </span>
                          </div>
                        </div>
                      </div>
                      {!session.is_current && (
                        <button
                          onClick={() => handleRevokeSession(session.session_id)}
                          disabled={revokingSession === session.session_id}
                          className="text-red-600 hover:text-red-800 p-2 rounded-md disabled:opacity-50"
                          title="Revogar sessão"
                        >
                          {revokingSession === session.session_id ? (
                            <div className="loading-spinner h-4 w-4"></div>
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}