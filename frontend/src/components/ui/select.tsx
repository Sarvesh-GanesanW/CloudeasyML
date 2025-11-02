'use client'

import * as React from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({ className, children, ...props }, ref) => {
  return (
    <div className="relative">
      <select
        ref={ref}
        className={cn(
          'h-12 w-full appearance-none rounded-2xl border border-[rgba(214,186,150,0.7)] bg-white/80 px-4 pr-12 text-base shadow-[inset_0_12px_24px_-24px_rgba(163,109,58,0.4)] transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F7C873] focus-visible:ring-offset-2 focus-visible:ring-offset-background',
          className
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#C58940]" />
    </div>
  )
})

Select.displayName = 'Select'
