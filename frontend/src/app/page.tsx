'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import Link from 'next/link'
import { Shield, Users, Lock, CheckCircle } from 'lucide-react'

/**
 * Página inicial da aplicação
 * Redireciona usuários autenticados para o dashboard
 * Exibe landing page para visitantes
 */
export default function HomePage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user && !isLoading) {
      router.push('/dashboard')
    }
  }, [user, isLoading, router])

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
    <div className="min-h-screen">
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
            <div className="flex space-x-4">
              <Link
                href="/auth/login"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Entrar
              </Link>
              <Link
                href="/auth/register"
                className="btn-primary text-sm"
              >
                Criar Conta
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-20 text-center">
          <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
            Sistema de Autenticação
            <span className="text-primary-600"> Seguro</span>
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Gerencie seus usuários com segurança. Autenticação JWT, verificação de email,
            2FA e muito mais.
          </p>
          <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
            <div className="rounded-md shadow">
              <Link
                href="/auth/register"
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 md:py-4 md:text-lg md:px-10"
              >
                Começar Agora
              </Link>
            </div>
            <div className="mt-3 rounded-md shadow sm:mt-0 sm:ml-3">
              <Link
                href="/auth/login"
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-primary-600 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10"
              >
                Fazer Login
              </Link>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="py-12">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
              Recursos Principais
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="flex justify-center">
                  <Lock className="h-12 w-12 text-primary-600" />
                </div>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  Autenticação JWT
                </h3>
                <p className="mt-2 text-gray-600">
                  Sistema seguro de autenticação com tokens JWT e refresh tokens
                </p>
              </div>
              <div className="text-center">
                <div className="flex justify-center">
                  <Users className="h-12 w-12 text-primary-600" />
                </div>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  Gerenciamento de Usuários
                </h3>
                <p className="mt-2 text-gray-600">
                  Perfis completos, sessões ativas e controle de acesso
                </p>
              </div>
              <div className="text-center">
                <div className="flex justify-center">
                  <CheckCircle className="h-12 w-12 text-primary-600" />
                </div>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  Verificação de Email
                </h3>
                <p className="mt-2 text-gray-600">
                  Verificação automática de email e recuperação de senha
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 mt-20">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex justify-center items-center mb-4">
              <Shield className="h-6 w-6 text-primary-400" />
              <span className="ml-2 text-lg font-bold text-white">
                VidConv Portal
              </span>
            </div>
            <p className="text-gray-400">
              © 2024 VidConv. Todos os direitos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}