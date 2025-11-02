'use client'

import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cn } from '@/lib/utils'

type ButtonVariant = 'default' | 'secondary' | 'ghost' | 'outline'
type ButtonSize = 'default' | 'sm' | 'lg' | 'icon'

const variantClasses: Record<ButtonVariant, string> = {
  default:
    'bg-[#2F6BFF] text-white shadow-[0_22px_55px_-28px_rgba(41,93,255,0.65)] hover:bg-[#2457d6] focus-visible:ring-[#2F6BFF]',
  secondary:
    'bg-[#FFE7C8] text-[#7A4117] border border-[#F5C16B] shadow-[0_10px_35px_-28px rgba(210,140,65,0.55)] hover:bg-[#FFDBAC] focus-visible:ring-[#F5C16B]',
  ghost:
    'bg-transparent text-[#7A4117] hover:bg-[#FFF3E0] hover:text-[#C45D10] focus-visible:ring-[#F7C873]',
  outline:
    'border border-[#D8C6AE] bg-transparent text-[#5B3713] hover:bg-white focus-visible:ring-[#2F6BFF]',
}

const sizeClasses: Record<ButtonSize, string> = {
  default: 'h-11 px-5',
  sm: 'h-9 px-4 text-sm',
  lg: 'h-12 px-6 text-lg',
  icon: 'h-10 w-10',
}

type ButtonElement = React.ElementRef<'button'>
type ButtonBaseProps = React.ComponentPropsWithoutRef<'button'>

export interface ButtonProps extends ButtonBaseProps {
  variant?: ButtonVariant
  size?: ButtonSize
  asChild?: boolean
}

export const Button = React.forwardRef<ButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-2xl font-semibold tracking-tight transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background active:translate-y-[1px]',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
