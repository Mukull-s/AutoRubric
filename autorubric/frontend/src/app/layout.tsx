import { MSWProvider } from "@/components/MSWProvider";
import { QueryProvider } from "@/components/QueryProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Navigation } from "@/components/Navigation";
import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen flex flex-col">
        <QueryProvider>
          <MSWProvider>
            <Navigation />
            <ProtectedRoute>
              <main className="flex-1 p-6">
                {children}
              </main>
            </ProtectedRoute>
          </MSWProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
