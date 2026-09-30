'use client'

import { useEffect, useState } from 'react'

export function MSWProvider({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const [mockingEnabled, setMockingEnabled] = useState(false)

  useEffect(() => {
    async function enableMocking() {
      if (
        typeof window !== 'undefined' &&
        process.env.NEXT_PUBLIC_USE_MOCKS === 'true'
      ) {
        const { worker } = await import('../mocks/browser')
        await worker.start()
      }
      setMockingEnabled(true)
    }

    enableMocking()
  }, [])

  if (!mockingEnabled) {
    return null
  }

  return <>{children}</>
}
