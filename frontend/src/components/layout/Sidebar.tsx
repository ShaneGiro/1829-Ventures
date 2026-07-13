import { NavLink } from "react-router-dom";
import {
  Building2,
  LayoutDashboard,
  Users,
  Briefcase,
  Upload,
  Bot,
  CheckSquare,
  PieChart,
  Send,
  ListChecks,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/companies", label: "Companies", icon: Building2 },
  { to: "/people", label: "People", icon: Users },
  { to: "/deals", label: "Pipeline", icon: Briefcase },
  { to: "/tasks", label: "Tasks", icon: CheckSquare },
  { to: "/outreach", label: "Outreach", icon: Send },
  { to: "/outreach-candidates", label: "Candidates", icon: ListChecks },
  { to: "/portfolio", label: "Portfolio", icon: PieChart },
  { to: "/imports", label: "Imports", icon: Upload },
  { to: "/ritchie", label: "Ritchie", icon: Bot },
];

export function Sidebar() {
  return (
    <aside className="hidden w-56 shrink-0 flex-col border-r bg-muted/30 p-3 md:flex">
      <div className="px-2 py-3 text-lg font-semibold">1829 Ventures</div>
      <nav className="flex flex-col gap-1">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="truncate">{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export function MobileNav() {
  return (
    <nav className="flex gap-1 overflow-x-auto border-b bg-background px-3 py-2 md:hidden">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "inline-flex min-w-fit items-center gap-2 rounded-md px-3 py-2 text-xs font-medium",
              isActive
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )
          }
        >
          <Icon className="h-4 w-4 shrink-0" />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
