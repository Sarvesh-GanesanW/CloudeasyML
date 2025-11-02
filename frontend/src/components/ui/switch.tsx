'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface SwitchProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onChange'> {
  checked: boolean
  onCheckedChange?: (checked: boolean) => void
}

export const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ className, checked, onCheckedChange, disabled, ...props }, ref) => {
    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      props.onClick?.(event)
      if (disabled) return
      onCheckedChange?.(!checked)
    }

    return (
      <button
        ref={ref}
        role="switch"
        aria-checked={checked}
        data-state={checked ? 'on' : 'off'}
        disabled={disabled}
        onClick={handleClick}
        className={cn(
          'relative inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-full border border-[rgba(214,186,150,0.7)] bg-[#FFF4E5] p-1 transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F7C873] focus-visible:ring-offset-2 focus-visible:ring-offset-background aria-[checked=true]:bg-[#F7B56F] aria-[checked=true]:border-[#E89A3F] disabled:cursor-not-allowed disabled:opacity-60',
          className
        )}
        {...props}
      >
        <span
          className={cn(
            'inline-block h-5 w-5 transform rounded-full bg-white shadow-[0_10px_25px_-18px_rgba(176,119,66,0.75)] transition-transform duration-300',
            checked ? 'translate-x-5' : 'translate-x-0'
          )}
        />
      </button>
    )
  }
)

Switch.displayName = 'Switch'
