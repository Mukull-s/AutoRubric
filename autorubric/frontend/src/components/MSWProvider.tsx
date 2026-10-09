'use client'

import { useEffect, useState } from 'react'

export function MSWProvider({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const [mockingEnabled, setMockingEnabled] = useState(false)
  const mocksRequested = process.env.NEXT_PUBLIC_USE_MOCKS === 'true'

  useEffect(() => {
    async function enableMocking() {
      if (
        typeof window !== 'undefined' &&
        mocksRequested
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

  return (
    <>
      {mocksRequested && (
        <div className="sticky top-0 z-50 bg-red-700 px-4 py-2 text-center text-xs font-bold tracking-wide text-white">
          MOCK DATA: not connected to the backend
        </div>
      )}
      {children}
    </>
  )
}
