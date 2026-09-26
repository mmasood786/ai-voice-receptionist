"use client";

import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("auth_user");

    router.replace("/login");
  }

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div>
        <h2 className="text-lg font-semibold">Dashboard</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-900 text-sm font-medium text-white">
            A
          </div>

          <div className="hidden sm:block">
            <p className="text-sm font-medium">Admin</p>
            <p className="text-xs text-gray-500">Business Owner</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg border px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-100"
        >
          Logout
        </button>
      </div>
    </header>
  );
}