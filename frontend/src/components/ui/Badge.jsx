import { cn } from "../../utils/helpers";

const variants = {
  default: "bg-surface-100 text-surface-700 dark:bg-surface-800 dark:text-surface-300",
  primary: "bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400",
  success: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  danger: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

export default function Badge({ children, variant = "default", className }) {
  return (
    <span className={cn("badge", variants[variant], className)}>
      {children}
    </span>
  );
}
