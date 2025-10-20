import React, { forwardRef } from 'react'
import { cn } from '@/lib/utils'
import type { InputProps } from '@/types'

/**
 * Componente Input reutilizável
 * Suporta diferentes tipos, estados de erro e ícones
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className, 
    type = 'text', 
    error, 
    label, 
    helperText, 
    leftIcon, 
    rightIcon,
    ...props 
  }, ref) => {
    const inputId = props.id || `input-${Math.random().toString(36).substr(2, 9)}`
    
    return (
      <div className="w-full">
        {label && (
          <label 
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <div className="h-5 w-5 text-gray-400">
                {leftIcon}
              </div>
            </div>
          )}
          
          <input
            id={inputId}
            type={type}
            ref={ref}
            className={cn(
              'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              error && 'border-red-300 focus:ring-red-500 focus:border-red-500',
              className
            )}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              <div className="h-5 w-5 text-gray-400">
                {rightIcon}
              </div>
            </div>
          )}
        </div>
        
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
        
        {helperText && !error && (
          <p className="mt-1 text-sm text-gray-500">{helperText}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'