/**
 * Tipos TypeScript para a aplicação VidConv User Portal
 */

// Tipos de usuário
export interface User {
  id: string
  email: string
  username: string
  full_name: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  last_login?: string
  profile_picture?: string
  phone?: string
  date_of_birth?: string
  bio?: string
}

// Tipos de autenticação
export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  confirm_password: string
  first_name: string
  last_name: string
  accept_terms: boolean
  accept_privacy: boolean
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AuthResponse {
  user: User
  tokens: AuthTokens
}

// Tipos que correspondem à estrutura real da API do backend
export interface LoginResponseSchema {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
  session_id: string
  requires_2fa: boolean
}

export interface UserResponseSchema {
  id: string
  email: string
  username: string
  full_name: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  last_login?: string
  profile_picture?: string
  phone?: string
  date_of_birth?: string
  bio?: string
}

export interface SessionSchema {
  session_id: string
  device_id?: string
  device_name?: string
  device_type?: string
  ip_address?: string
  location?: string
  is_current: boolean
  created_at: string
  last_activity: string
  expires_at: string
}

export interface ActiveSessionsResponseSchema {
  sessions: SessionSchema[]
  total: number
}

// Tipos de sessão
export interface UserSession {
  id: string
  user_id: string
  device_info: string
  ip_address: string
  user_agent: string
  created_at: string
  last_activity: string
  is_current: boolean
  location?: string
  browser?: string
  os?: string
}

// Tipos de API
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  errors?: Record<string, string[]>
}

export interface ApiError {
  message: string
  status: number
  errors?: Record<string, string[]>
}

// Tipos de formulário
export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'password' | 'tel' | 'date' | 'textarea'
  placeholder?: string
  required?: boolean
  validation?: {
    minLength?: number
    maxLength?: number
    pattern?: RegExp
    custom?: (value: string) => string | null
  }
}

export interface FormErrors {
  [key: string]: string
}

// Tipos de contexto de autenticação
export interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  updateUser: (data: Partial<User>) => Promise<void>
  refreshToken: () => Promise<void>
}

// Tipos de configuração
export interface AppConfig {
  apiUrl: string
  appName: string
  version: string
  features: {
    registration: boolean
    emailVerification: boolean
    twoFactorAuth: boolean
    socialLogin: boolean
  }
}

// Tipos de notificação
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  read: boolean
}

// Tipos de dashboard
export interface DashboardStats {
  totalUsers: number
  activeUsers: number
  newUsersToday: number
  totalSessions: number
}

// Tipos de perfil
export interface ProfileUpdateData {
  full_name?: string
  username?: string
  phone?: string
  bio?: string
  date_of_birth?: string
}

export interface PasswordChangeData {
  current_password: string
  new_password: string
  confirm_password: string
}

// Tipos para validação de senha
export interface PasswordValidation {
  strength: 'weak' | 'medium' | 'strong'
  score: number
  requirements: {
    minLength: boolean
    hasUppercase: boolean
    hasLowercase: boolean
    hasNumber: boolean
    hasSpecialChar: boolean
  }
  isValid: boolean
}

// Tipos de componentes
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  children: React.ReactNode
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
  className?: string
}

export interface InputProps {
  label?: string
  error?: string
  required?: boolean
  className?: string
  [key: string]: any
}

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
  showCloseButton?: boolean
  closeOnOverlayClick?: boolean
  className?: string
}

// Tipos de rota
export interface ProtectedRouteProps {
  children: React.ReactNode
  requireAuth?: boolean
  redirectTo?: string
  requireVerification?: boolean
}

// Tipos de middleware
export interface MiddlewareConfig {
  matcher: string[]
  publicRoutes: string[]
  authRoutes: string[]
}