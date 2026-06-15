import { Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { startLogin, useAuth } from "@/hooks/useAuth";

export function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return null;
  if (isAuthenticated) return <Navigate to="/" replace />;

  return (
    <div className="flex h-screen flex-col items-center justify-center gap-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">1829 Ventures CRM</h1>
        <p className="mt-1 text-sm text-muted-foreground">Sign in with your RIT Google account.</p>
      </div>
      <Button size="lg" onClick={startLogin}>
        Continue with Google
      </Button>
    </div>
  );
}
