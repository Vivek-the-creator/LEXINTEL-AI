import { NavLink, useLocation } from "react-router-dom";
import {
  Scale, LayoutDashboard, Brain, Upload, FileText,
  MessageSquare, Settings, ChevronLeft, ChevronRight, X, Briefcase
} from "lucide-react";
import { cn } from "../../utils/helpers";

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/dashboard/cases", icon: Brain, label: "AI Analysis" },
  { to: "/dashboard/my-cases", icon: Briefcase, label: "My Cases" },
  { to: "/dashboard/uploads", icon: Upload, label: "Uploads" },
  { to: "/dashboard/reports", icon: FileText, label: "Reports" },
  { to: "/dashboard/conversations", icon: MessageSquare, label: "Conversations" },
];

const bottomItems = [
  { to: "/dashboard/settings", icon: Settings, label: "Settings" },
];

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={cn(
          "fixed top-0 left-0 h-full bg-surface-900 dark:bg-surface-950 border-r border-surface-800 z-30 flex flex-col transition-all duration-300",
          collapsed ? "w-16" : "w-64",
          "lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className={cn(
          "flex items-center h-16 px-4 border-b border-surface-800",
          collapsed ? "justify-center" : "justify-between"
        )}>
          {!collapsed && (
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center flex-shrink-0">
                <Scale className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-white text-sm">LexIntel AI</span>
            </div>
          )}
          {collapsed && (
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <Scale className="w-4 h-4 text-white" />
            </div>
          )}
          <div className="flex items-center gap-1">
            <button
              onClick={onMobileClose}
              className="lg:hidden p-1.5 rounded-lg text-surface-400 hover:text-white hover:bg-surface-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
            <button
              onClick={onToggle}
              className="hidden lg:flex p-1.5 rounded-lg text-surface-400 hover:text-white hover:bg-surface-800 transition-colors"
            >
              {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/dashboard"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-primary-600 text-white shadow-sm"
                    : "text-surface-400 hover:text-white hover:bg-surface-800",
                  collapsed && "justify-center"
                )
              }
              title={collapsed ? label : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="py-4 px-2 border-t border-surface-800 space-y-1">
          {bottomItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-primary-600 text-white"
                    : "text-surface-400 hover:text-white hover:bg-surface-800",
                  collapsed && "justify-center"
                )
              }
              title={collapsed ? label : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </div>
      </aside>
    </>
  );
}
