'use client'

import Link from 'next/link'
import { ArrowUpRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-[#E5D9C7] bg-[#FBF4EA]/95 backdrop-blur-md">
      <div className="bg-[#FFD400] text-xs font-semibold uppercase tracking-[0.3em] text-[#1E1E1E]">
        <div className="container mx-auto flex items-center justify-center px-4 py-2">
          Lies, Benchmarks & Breakthroughs — Livestreaming the latest HCPE drop ✦ Nov 12
        </div>
      </div>

      <div className="container mx-auto flex items-center justify-between px-4 py-5">
        <Link href="/" className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-[#E5D9C7] bg-white text-sm font-semibold text-[#2F6BFF] shadow-[0_10px_24px_-18px_rgba(47,107,255,0.55)]">
            HC
          </span>
          <div className="flex flex-col">
            <span className="text-lg font-semibold tracking-[0.08em] text-[#2D1D10]">HCPE Control Studio</span>
            <span className="text-xs uppercase tracking-[0.32em] text-[#8B6950]">
              Making Infrastructure Feel Small
            </span>
          </div>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-medium text-[#5B3713] md:flex">
          <Link href="#" className="transition hover:text-[#2F6BFF]">
            Product
          </Link>
          <Link href="#" className="transition hover:text-[#2F6BFF]">
            Pricing
          </Link>
          <Link href="#" className="transition hover:text-[#2F6BFF]">
            Docs
          </Link>
          <Link href="#" className="transition hover:text-[#2F6BFF]">
            Community
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" className="hidden text-[#5B3713] md:inline-flex">
            Log in
          </Button>
          <Button size="sm" className="inline-flex gap-2">
            Start free
            <ArrowUpRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
