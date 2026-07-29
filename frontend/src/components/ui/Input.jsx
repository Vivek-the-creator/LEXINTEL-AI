import { forwardRef } from "react";
import { cn } from "../../utils/helpers";

const Input = forwardRef(function Input(
  { label, error, hint, className, leftIcon: LeftIcon, rightElement, ...props },
  ref
) {
  return (
    <div className="w-full">
      {label && <label className="label">{label}</label>}
      <div className="relative">
        {LeftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <LeftIcon className="w-4 h-4 text-surface-400" />
          </div>
        )}
        <input
          ref={ref}
          className={cn(
            "input",
            LeftIcon && "pl-10",
            rightElement && "pr-10",
            error && "border-red-500 focus:ring-red-500",
            className
          )}
          {...props}
        />
        {rightElement && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            {rightElement}
          </div>
        )}
      </div>
      {error && <p className="mt-1.5 text-xs text-red-500">{error}</p>}
      {hint && !error && <p className="mt-1.5 text-xs text-surface-400">{hint}</p>}
    </div>
  );
});

export default Input;
