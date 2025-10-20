import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Middleware para proteção de rotas
 * Verifica se o usuário está autenticado antes de acessar rotas protegidas
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Obtém o token JWT dos cookies
  const token = request.cookies.get('access_token')?.value
  
  // Rotas que requerem autenticação
  const protectedRoutes = ['/dashboard', '/profile', '/security']
  
  // Rotas de autenticação (login, registro)
  const authRoutes = ['/auth/login', '/auth/register']
  
  // Verifica se a rota atual é protegida
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname.startsWith(route)
  )
  
  // Verifica se a rota atual é de autenticação
  const isAuthRoute = authRoutes.some(route => 
    pathname.startsWith(route)
  )
  
  // Se é uma rota protegida e não há token, redireciona para login
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }
  
  // Se é uma rota de autenticação e há token, redireciona para dashboard
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }
  
  // Permite o acesso à rota
  return NextResponse.next()
}

/**
 * Configuração do middleware
 * Define quais rotas devem ser processadas pelo middleware
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
}