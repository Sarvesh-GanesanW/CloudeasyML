'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'success' | 'destructive'
}

const variants: Record<Required<BadgeProps>['variant'], string> = {
  default: 'border border-[#3B7CFF] bg-[#E4ECFF] text-[#1E3A8A]',
  outline: 'border border-[#E5D9C7] text-[#5B3713]',
  success: 'border border-[#8BD991] bg-[#E6F9E7] text-[#27632A]',
  destructive: 'border border-[#F5A3A3] bg-[#FFE2E2] text-[#B54444]',
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium uppercase tracking-wide',
        variants[variant],
        className
      )}
      {...props}
    />
  )
)

Badge.displayName = 'Badge'
