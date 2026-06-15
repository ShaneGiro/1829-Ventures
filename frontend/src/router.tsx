import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage, PlaceholderPage } from "@/pages/PlaceholderPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "companies", element: <PlaceholderPage title="Companies" /> },
      { path: "people", element: <PlaceholderPage title="People" /> },
      { path: "deals", element: <PlaceholderPage title="Pipeline" /> },
      { path: "imports", element: <PlaceholderPage title="Imports" /> },
      { path: "ritchie", element: <PlaceholderPage title="Ritchie" /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
