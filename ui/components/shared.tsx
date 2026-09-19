"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { AUDIENCE_TONE, STRATEGY_LABEL } from "@/lib/api"
import { cn } from "@/lib/utils"

/** A button group rather than a dropdown: four options, all worth seeing at once. */
export function StrategyPicker({
  strategies,
  value,
  onChange,
  disabled,
}: {
  strategies: string[]
  value: string
  onChange: (next: string) => void
  disabled?: boolean
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-muted-foreground text-xs font-normal">Chiến lược chia nhỏ</Label>
      <div className="flex flex-wrap gap-1.5">
        {strategies.map((strategy) => (
          <Button
            key={strategy}
            size="sm"
            variant={strategy === value ? "default" : "outline"}
            disabled={disabled}
            onClick={() => onChange(strategy)}
          >
            {STRATEGY_LABEL[strategy] ?? strategy}
          </Button>
        ))}
      </div>
    </div>
  )
}

export function AudienceBadge({ audience }: { audience: string }) {
  return (
    <Badge variant="outline" className={cn("font-mono text-[11px]", AUDIENCE_TONE[audience])}>
      {audience}
    </Badge>
  )
}

/** Scores are the whole point of the exercise, so they are always monospaced and signed. */
export function Score({ value }: { value: number }) {
  return (
    <span className="font-mono text-xs tabular-nums">
      {value >= 0 ? "+" : ""}
      {value.toFixed(4)}
    </span>
  )
}

export function ErrorNote({ error }: { error: string | null }) {
  if (!error) return null
  return (
    <p className="border-destructive/40 bg-destructive/5 text-destructive rounded-md border px-3 py-2 text-xs">
      {error}
    </p>
  )
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-muted-foreground py-8 text-center text-sm">{children}</p>
}
