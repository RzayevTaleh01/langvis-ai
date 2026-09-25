import * as React from "react"
import { cn } from "cn"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "h-9 w-full min-w-0 rounded-md px-3 py-1 font-[inherit] border border-[var(--border-strong)] bg-[var(--panel)] text-[var(--ink-strong)] text-sm transition-colors outline-none placeholder:text-[var(--ink-dim)] focus-visible:border-primary focus-visible:ring-[3px] focus-visible:ring-[var(--pri-ghost)] disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive",
        className
      )}
      {...props}
    />
  )
}

export { Input }
