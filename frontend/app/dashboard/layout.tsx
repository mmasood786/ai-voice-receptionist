import Sidebar from "@/components/dashboard/Sidebar";
import Header from "@/components/dashboard/Header";
import AuthGuard from "@/components/auth/AuthGuard";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50">
        <Sidebar />

        <div className="ml-64">
          <Header />

          <main className="p-6">
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}