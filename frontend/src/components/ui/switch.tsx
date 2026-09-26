"use client"

// shadcn Switch in the LangVis look: a warm track that turns forest green,
// with a white thumb.

import * as React from "react"
import { cn } from "cn"
import { Switch as SwitchPrimitive } from "radix-ui"

function Switch({
  className,
  size = "default",
  ...props
}: React.ComponentProps<typeof SwitchPrimitive.Root> & {
  size?: "sm" | "default"
}) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      data-size={size}
      className={cn(
        "peer group/switch relative inline-flex shrink-0 cursor-pointer items-center rounded-full border border-transparent p-0 outline-none transition-colors",
        "data-[size=default]:h-[22px] data-[size=default]:w-[40px] data-[size=sm]:h-[16px] data-[size=sm]:w-[28px]",
        "data-unchecked:bg-[var(--border-strong)] data-checked:bg-primary hover:data-unchecked:bg-[var(--ink-dim)]",
        "focus-visible:ring-[3px] focus-visible:ring-ring/30 data-disabled:cursor-not-allowed data-disabled:opacity-50",
        className
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className="pointer-events-none block rounded-full bg-white shadow-[0_1px_2px_rgba(35,32,26,.25)] transition-transform group-data-[size=default]/switch:size-[18px] group-data-[size=sm]/switch:size-3 data-unchecked:translate-x-[1px] group-data-[size=default]/switch:data-checked:translate-x-[19px] group-data-[size=sm]/switch:data-checked:translate-x-[13px]"
      />
    </SwitchPrimitive.Root>
  )
}

export { Switch }
