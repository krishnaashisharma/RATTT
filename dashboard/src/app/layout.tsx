import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Remote Device Management',
  description: 'Secure cross-platform remote device management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
