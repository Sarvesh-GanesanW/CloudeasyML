import type { Metadata } from 'next'
import { Space_Grotesk, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { cn } from '@/lib/utils'

const bodyFont = Space_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body',
})

const headingFont = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-heading',
})

export const metadata: Metadata = {
  title: 'HCPE - Housing Crisis Prediction Ensemble',
  description: 'Deploy and manage ML infrastructure for housing crisis prediction with custom Jupyter notebooks',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className={cn(bodyFont.variable, headingFont.variable)}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
