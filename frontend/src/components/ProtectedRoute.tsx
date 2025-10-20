import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import type { ProtectedRouteProps } from '@/types'

/**
 * Componente para proteção de rotas
 * Redireciona usuários não autenticados para a página de login
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  redirectTo = '/auth/login',
  requireVerification = false,
}) => {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      // Se não há usuário, redireciona para login
      if (!user) {
        const currentPath = window.location.pathname
        const loginUrl = `${redirectTo}?redirect=${encodeURIComponent(currentPath)}`
        router.push(loginUrl)
        return
      }

      // Se requer verificação e usuário não está verificado
      if (requireVerification && !user.is_verified) {
        router.push('/auth/verify-email')
        return
      }

      // Se usuário não está ativo
      if (!user.is_active) {
        router.push('/auth/account-suspended')
        return
      }
    }
  }, [user, isLoading, router, redirectTo, requireVerification])

  // Mostra loading enquanto verifica autenticação
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="loading-spinner h-8 w-8 mx-auto mb-4"></div>
          <p className="text-gray-600">Verificando autenticação...</p>
        </div>
      </div>
    )
  }

  // Se não há usuário, não renderiza nada (redirecionando)
  if (!user) {
    return null
  }

  // Se requer verificação e usuário não está verificado
  if (requireVerification && !user.is_verified) {
    return null
  }

  // Se usuário não está ativo
  if (!user.is_active) {
    return null
  }

  // Renderiza o conteúdo protegido
  return <>{children}</>
}