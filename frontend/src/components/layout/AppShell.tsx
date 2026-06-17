import { Outlet } from "react-router-dom";
import { RitchieChatWidget } from "@/components/agent/RitchieChatWidget";
import { MobileNav, Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export function AppShell() {
  const { user, logout } = useAuth();
  return (
    <div className="flex min-h-screen w-full overflow-hidden bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-14 items-center justify-between gap-3 border-b px-4 py-3 md:px-6">
          <div className="min-w-0">
            <div className="truncate text-sm font-medium md:hidden">1829 Ventures</div>
            <div className="truncate text-xs text-muted-foreground md:text-sm">Internal CRM</div>
          </div>
          <div className="flex min-w-0 items-center gap-2 md:gap-3">
            <span className="hidden max-w-[14rem] truncate text-sm sm:block">
              {user?.full_name ?? user?.email}
            </span>
            <Button variant="outline" size="sm" onClick={() => logout()}>
              Sign out
            </Button>
          </div>
        </header>
        <MobileNav />
        <main className="min-w-0 flex-1 overflow-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
      <RitchieChatWidget />
    </div>
  );
}
