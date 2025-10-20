'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import Cookies from 'js-cookie'
import { apiClient } from '@/lib/api'
import type { User, LoginCredentials, RegisterData, AuthContextType } from '@/types'

/**
 * Contexto de autenticação para gerenciar estado global do usuário
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

/**
 * Provider do contexto de autenticação
 * Gerencia estado do usuário, login, logout e refresh de tokens
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  /**
   * Verifica se usuário está autenticado
   */
  const isAuthenticated = !!user

  /**
   * Carrega dados do usuário atual
   */
  const loadUser = async () => {
    try {
      const token = Cookies.get('access_token')
      if (!token) {
        setIsLoading(false)
        return
      }

      const userData = await apiClient.getCurrentUser()
      setUser(userData)
    } catch (error) {
      // Token inválido ou expirado, remove cookies
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Realiza login do usuário
   */
  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true)
    try {
      const { user: userData } = await apiClient.login(credentials)
      setUser(userData)
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Registra novo usuário e faz login automático
   */
  const register = async (data: RegisterData) => {
    setIsLoading(true)
    try {
      const { user: userData } = await apiClient.register(data)
      setUser(userData)
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Realiza logout do usuário
   */
  const logout = async () => {
    setIsLoading(true)
    try {
      await apiClient.logout()
    } catch (error) {
      // Ignora erros de logout
    } finally {
      setUser(null)
      setIsLoading(false)
    }
  }

  /**
   * Atualiza dados do usuário
   */
  const updateUser = async (data: Partial<User>) => {
    if (!user) return

    try {
      const updatedUser = await apiClient.updateProfile(data)
      setUser(updatedUser)
    } catch (error) {
      throw error
    }
  }

  /**
   * Atualiza token de acesso
   */
  const refreshToken = async () => {
    try {
      await apiClient.refreshToken()
    } catch (error) {
      // Se refresh falhar, faz logout
      setUser(null)
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
      throw error
    }
  }

  /**
   * Configura refresh automático do token
   */
  useEffect(() => {
    let refreshInterval: NodeJS.Timeout

    if (isAuthenticated) {
      // Refresh token a cada 14 minutos (token expira em 15 minutos)
      refreshInterval = setInterval(async () => {
        try {
          await refreshToken()
        } catch (error) {
          console.error('Erro ao renovar token:', error)
        }
      }, 14 * 60 * 1000) // 14 minutos
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    }
  }, [isAuthenticated])

  /**
   * Carrega usuário na inicialização
   */
  useEffect(() => {
    loadUser()
  }, [])

  /**
   * Monitora mudanças nos cookies (para logout em outras abas)
   */
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'access_token' && !e.newValue && user) {
        // Token removido em outra aba, faz logout
        setUser(null)
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [user])

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateUser,
    refreshToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook para usar o contexto de autenticação
 * @returns Contexto de autenticação
 * @throws Erro se usado fora do AuthProvider
 */
export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext)
  
  if (context === undefined) {
    throw new Error('useAuthContext deve ser usado dentro de um AuthProvider')
  }
  
  return context
}