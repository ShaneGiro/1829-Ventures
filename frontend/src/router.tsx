import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/PlaceholderPage";
import { CompanyList } from "@/pages/CompanyList";
import { CompanyDetail } from "@/pages/CompanyDetail";
import { PeopleList } from "@/pages/PeopleList";
import { ContactDetail } from "@/pages/ContactDetail";
import { PipelineBoard } from "@/pages/PipelineBoard";
import { TaskList } from "@/pages/TaskList";
import { ImportManager } from "@/pages/ImportManager";
import { RitchiePage } from "@/pages/RitchiePage";
import { PortfolioDashboard } from "@/pages/PortfolioDashboard";
import { OutreachPage } from "@/pages/OutreachPage";
import { OutreachCandidatesPage } from "@/pages/OutreachCandidatesPage";

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
      { path: "companies", element: <CompanyList /> },
      { path: "companies/:companyId", element: <CompanyDetail /> },
      { path: "people", element: <PeopleList /> },
      { path: "people/:personId", element: <ContactDetail /> },
      { path: "deals", element: <PipelineBoard /> },
      { path: "tasks", element: <TaskList /> },
      { path: "outreach", element: <OutreachPage /> },
      { path: "outreach-candidates", element: <OutreachCandidatesPage /> },
      { path: "imports", element: <ImportManager /> },
      { path: "portfolio", element: <PortfolioDashboard /> },
      { path: "ritchie", element: <RitchiePage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
