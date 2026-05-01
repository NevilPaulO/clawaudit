import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold", {
  variants: {
    variant: {
      default: "border-cyan-400/30 bg-cyan-400/10 text-cyan-200",
      critical: "border-red-400/30 bg-red-500/10 text-red-200",
      high: "border-rose-400/30 bg-rose-500/10 text-rose-200",
      warn: "border-amber-300/30 bg-amber-400/10 text-amber-200",
      info: "border-sky-300/30 bg-sky-400/10 text-sky-200",
      muted: "border-white/10 bg-white/5 text-slate-300",
      success: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
    },
  },
  defaultVariants: { variant: "default" },
});

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
