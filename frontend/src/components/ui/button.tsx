import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-xs font-semibold transition duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/30 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "border border-accent/45 bg-accent/90 px-4 py-2 text-white shadow-[0_0_20px_rgba(21,94,117,0.14)] hover:bg-accent hover:shadow-[0_0_24px_rgba(21,94,117,0.2)]",
        executive:
          "border border-white/10 bg-white/[0.055] px-4 py-2 text-white/82 hover:border-gold/35 hover:bg-white/[0.08] hover:text-white",
        ghost: "px-3 py-2 text-white/58 hover:bg-white/[0.055] hover:text-white",
        gold:
          "border border-gold/35 bg-gold/[0.09] px-4 py-2 text-gold hover:bg-gold/[0.13]",
      },
      size: {
        default: "h-9",
        sm: "h-8 px-3 text-xs",
        lg: "h-10 px-5 text-sm",
        icon: "h-9 w-9 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
