import Link from "next/link";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen flex flex-col">
        <nav className="border-b p-4 flex gap-4 bg-slate-50 items-center">
          <Link href="/" className="font-bold">AutoRubric</Link>
          <Link href="/upload" className="text-sm hover:underline">Upload</Link>
          <div className="flex-1"></div>
          <Link href="/login" className="text-sm hover:underline">Login / Logout</Link>
        </nav>
        <main className="flex-1 p-6">
          {children}
        </main>
      </body>
    </html>
  );
}
