import * as React from "react"
import { cn } from "cn"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex field-sizing-content min-h-16 w-full rounded-md px-3 py-2 font-[inherit] leading-relaxed border border-[var(--border-strong)] bg-[var(--panel)] text-[var(--ink-strong)] text-sm transition-colors outline-none placeholder:text-[var(--ink-dim)] focus-visible:border-primary focus-visible:ring-[3px] focus-visible:ring-[var(--pri-ghost)] disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
