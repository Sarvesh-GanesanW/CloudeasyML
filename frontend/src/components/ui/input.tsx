'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        'h-12 w-full rounded-2xl border border-[rgba(214,186,150,0.7)] bg-white/80 px-4 text-base shadow-[inset_0_10px_25px_-24px_rgba(163,109,58,0.45)] transition-all duration-300 placeholder:text-muted-foreground/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F7C873] focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Input.displayName = 'Input'
