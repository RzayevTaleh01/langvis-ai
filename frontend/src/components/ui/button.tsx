import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"
import { Slot } from "radix-ui"

// The one button of LangVis. Every button of the app is this component: the
// variants only change the colours, the shape is always the same.
const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap no-underline transition-colors outline-none select-none cursor-pointer focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/40 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-[#0e5a4d] hover:text-primary-foreground",
        speak: "bg-[var(--speak)] text-white hover:bg-[#b04e24] hover:text-white",
        outline:
          "border-border bg-card text-foreground hover:border-primary hover:text-primary aria-expanded:border-primary aria-expanded:text-primary",
        secondary: "bg-accent text-accent-foreground hover:bg-[#d3e7e2] aria-expanded:bg-[#d3e7e2]",
        // No see-through buttons: "ghost" looks like "outline".
        ghost:
          "border-border bg-card text-[var(--ink-strong)] hover:border-primary hover:text-primary aria-expanded:border-primary aria-expanded:text-primary",
        soft: "bg-accent text-accent-foreground hover:bg-[#d3e7e2]",
        // A small icon inside a list or a menu row (edit, delete): no box, a
        // soft icon that comes up when its row is pointed at.
        quiet:
          "text-[var(--ink-dim)] opacity-70 group-hover/row:opacity-100 group-hover/row:text-[var(--ink-strong)] hover:bg-secondary hover:opacity-100 hover:text-[var(--ink-strong)] focus-visible:opacity-100",
        destructive:
          "bg-destructive/10 text-destructive hover:bg-destructive/20 focus-visible:border-destructive/40 focus-visible:ring-destructive/20",
        // A text link, for small actions inside a board or a list ("I didn't say that").
        link: "h-auto! p-0! text-primary underline-offset-4 hover:underline",
      },
      size: {
        // default and lg are one height: buttons side by side always line up.
        default: "h-10 px-4",
        xs: "h-7 gap-1 px-2.5 text-xs [&_svg:not([class*='size-'])]:size-3.5",
        sm: "h-8 gap-1.5 px-3 text-[13px] [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-10 px-5 text-[15px]",
        icon: "size-10",
        "icon-xs": "size-7 [&_svg:not([class*='size-'])]:size-3.5",
        "icon-sm": "size-8",
        "icon-lg": "size-11 [&_svg:not([class*='size-'])]:size-5",
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
      {...(asChild ? {} : { type: props.type ?? "button" })}
      {...props}
    />
  )
}

export { Button, buttonVariants }
