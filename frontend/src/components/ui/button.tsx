import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"
import { Slot } from "radix-ui"

// shadcn Button in the LangVis colours: forest green, warm paper, 6px corners.
const buttonVariants = cva(
  "group/button inline-flex shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded-md border border-transparent font-[inherit] font-medium whitespace-nowrap no-underline! transition-colors outline-none select-none focus-visible:ring-[3px] focus-visible:ring-ring/30 disabled:pointer-events-none disabled:opacity-55 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-primary text-white! hover:bg-[#0e574a]",
        outline: "border-[var(--border-strong)] bg-[var(--panel)] text-[var(--ink-strong)]! hover:border-primary hover:text-primary!",
        secondary: "bg-[var(--pri-ghost)] text-primary! hover:bg-[#d3e7e2]",
        ghost: "bg-transparent text-[var(--ink-strong)]! hover:bg-[var(--panel-2)]",
        destructive: "bg-[var(--bad-ghost)] text-[var(--bad)]! hover:bg-[#f0d6d0]",
        link: "h-auto! bg-transparent px-0! text-primary! underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 text-sm",
        sm: "h-8 px-3 text-[13px]",
        lg: "h-11 px-6 text-[15px]",
        icon: "size-9",
        "icon-sm": "size-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
