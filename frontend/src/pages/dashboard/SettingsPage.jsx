import { Sun, Moon, Bell, Shield, Globe } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";
import { cn } from "../../utils/helpers";

function SettingRow({ icon: Icon, title, description, children }) {
  return (
    <div className="flex items-center justify-between py-5 border-b border-surface-100 dark:border-surface-800 last:border-0">
      <div className="flex items-start gap-4">
        <div className="w-9 h-9 rounded-lg bg-surface-100 dark:bg-surface-800 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Icon className="w-4 h-4 text-surface-500 dark:text-surface-400" />
        </div>
        <div>
          <p className="text-sm font-medium text-surface-900 dark:text-surface-100">{title}</p>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">{description}</p>
        </div>
      </div>
      <div className="ml-4 flex-shrink-0">{children}</div>
    </div>
  );
}

function Toggle({ enabled, onChange }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={cn(
        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200",
        enabled ? "bg-primary-600" : "bg-surface-300 dark:bg-surface-600"
      )}
    >
      <span
        className={cn(
          "inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200",
          enabled ? "translate-x-6" : "translate-x-1"
        )}
      />
    </button>
  );
}

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">Settings</h1>
        <p className="text-surface-500 dark:text-surface-400 mt-1">Manage your application preferences.</p>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-surface-900 dark:text-surface-100 mb-2">Appearance</h2>
        <SettingRow
          icon={theme === "dark" ? Moon : Sun}
          title="Dark Mode"
          description="Switch between light and dark interface themes"
        >
          <Toggle enabled={theme === "dark"} onChange={toggleTheme} />
        </SettingRow>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-surface-900 dark:text-surface-100 mb-2">Notifications</h2>
        <SettingRow icon={Bell} title="Email Notifications" description="Receive updates about your cases via email">
          <Toggle enabled={true} onChange={() => {}} />
        </SettingRow>
        <SettingRow icon={Bell} title="Push Notifications" description="Browser push notifications for real-time updates">
          <Toggle enabled={false} onChange={() => {}} />
        </SettingRow>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-surface-900 dark:text-surface-100 mb-2">Privacy & Security</h2>
        <SettingRow icon={Shield} title="Two-Factor Authentication" description="Add an extra layer of security to your account">
          <span className="text-xs text-surface-400 bg-surface-100 dark:bg-surface-800 px-2 py-1 rounded">Coming soon</span>
        </SettingRow>
        <SettingRow icon={Globe} title="Session Management" description="View and manage active sessions">
          <span className="text-xs text-surface-400 bg-surface-100 dark:bg-surface-800 px-2 py-1 rounded">Coming soon</span>
        </SettingRow>
      </div>
    </div>
  );
}
