import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Sistema Experto de Algas',
  description: 'Identifica especies de macroalgas mediante diagnóstico interactivo',
  generator: 'v0.app',
  icons: {
    icon: [
      {
        url: '/algaico.png',
      },
      {
        url: '/algaico.png',
      },
      {
        url: '/algaico.png',
      },
    ],
    apple: '/algaico.png',
  },
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="es" className="bg-background" suppressHydrationWarning>
      <body className="antialiased bg-background text-foreground">
        <script
          dangerouslySetInnerHTML={{
            __html: "(function(){try{var t=localStorage.getItem('theme'); if(t==='dark'||t==='light'){document.documentElement.classList.add(t);} }catch(e){}})();",
          }}
        />
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
