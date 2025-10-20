import { useAuthContext } from '@/contexts/AuthContext'

/**
 * Hook personalizado para acessar o contexto de autenticação
 * Fornece uma interface simplificada para componentes
 * 
 * @returns Objeto com estado e métodos de autenticação
 */
export function useAuth() {
  return useAuthContext()
}