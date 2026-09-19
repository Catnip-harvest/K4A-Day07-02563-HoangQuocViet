"use client"

import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AudienceBadge, Empty, ErrorNote, Score, StrategyPicker } from "@/components/shared"
import { api, STRATEGY_LABEL, type BenchmarkRow } from "@/lib/api"

export function BenchmarkPanel({ strategies }: { strategies: string[] }) {
  const [strategy, setStrategy] = React.useState("recursive")
  const [rows, setRows] = React.useState<BenchmarkRow[] | null>(null)
  const [score, setScore] = React.useState<{ hits: number; total: number; chunks: number } | null>(null)
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  async function run() {
    setBusy(true)
    setError(null)
    try {
      const response = await api.benchmark(strategy)
      setRows(response.rows)
      setScore({ hits: response.hits, total: response.total, chunks: response.chunks_indexed })
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>5 câu hỏi đánh giá của nhóm</CardTitle>
          <CardDescription>
            Đúng bộ câu hỏi trong <code className="font-mono">benchmark/queries.json</code>, chấm hit@3 tự
            động theo <code className="font-mono">gold_doc_ids</code>. Cả nhóm chạy chung bộ này, chỉ đổi
            chiến lược — đó là biến duy nhất.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <StrategyPicker
              strategies={strategies}
              value={strategy}
              onChange={setStrategy}
              disabled={busy}
            />
            <Button onClick={run} disabled={busy}>
              {busy ? "Đang chạy…" : "Chạy benchmark"}
            </Button>
          </div>

          {score && (
            <div className="bg-muted/50 flex flex-wrap items-center gap-4 rounded-lg px-4 py-3">
              <span className="text-2xl font-semibold tabular-nums">
                {score.hits}
                <span className="text-muted-foreground text-base font-normal">/{score.total}</span>
              </span>
              <span className="text-muted-foreground text-xs">
                hit@3 · {STRATEGY_LABEL[strategy]} · {score.chunks} chunk
              </span>
            </div>
          )}

          <ErrorNote error={error} />
        </CardContent>
      </Card>

      {rows ? (
        rows.map((row) => (
          <Card key={row.id}>
            <CardHeader className="pb-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline" className="font-mono text-[11px]">
                  {row.id}
                </Badge>
                <Badge
                  variant="outline"
                  className={
                    row.hit
                      ? "border-emerald-500/40 text-[11px] text-emerald-600 dark:text-emerald-400"
                      : "border-destructive/50 text-destructive text-[11px]"
                  }
                >
                  {row.hit ? "hit@3" : "miss"}
                </Badge>
                {row.metadata_filter && (
                  <Badge variant="outline" className="font-mono text-[11px]">
                    filter: audience={row.metadata_filter.audience}
                  </Badge>
                )}
                {row.traps.length > 0 && (
                  <Badge variant="outline" className="border-amber-500/50 text-[11px] text-amber-600 dark:text-amber-400">
                    bẫy: {row.traps.join(", ")}
                  </Badge>
                )}
              </div>
              <CardTitle className="pt-1 text-sm leading-snug">{row.query}</CardTitle>
              <CardDescription className="text-xs">{row.tests}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="border-border rounded-lg border border-dashed p-3">
                <p className="text-muted-foreground mb-1 font-mono text-[11px]">
                  gold · {row.gold_doc_ids.join(", ")}
                </p>
                <p className="text-xs leading-relaxed">{row.gold_answer}</p>
              </div>

              <div className="space-y-1.5">
                {row.results.map((hit, index) => {
                  const isGold = row.gold_doc_ids.includes(hit.metadata.doc_id)
                  const isTrap = row.traps.includes(hit.metadata.doc_id)
                  return (
                    <div
                      key={hit.id}
                      className={
                        "rounded-md border p-2.5 " +
                        (isGold
                          ? "border-emerald-500/40 bg-emerald-500/5"
                          : isTrap
                            ? "border-amber-500/40 bg-amber-500/5"
                            : "border-border")
                      }
                    >
                      <div className="mb-1 flex flex-wrap items-center gap-2">
                        <span className="text-muted-foreground font-mono text-[11px]">#{index + 1}</span>
                        <Score value={hit.score} />
                        <span className="font-mono text-[11px]">{hit.metadata.doc_id}</span>
                        <AudienceBadge audience={hit.metadata.audience} />
                        {isGold && <span className="text-[11px] text-emerald-600 dark:text-emerald-400">đúng</span>}
                        {isTrap && <span className="text-[11px] text-amber-600 dark:text-amber-400">bẫy</span>}
                      </div>
                      <p className="text-foreground/75 line-clamp-2 text-[11px] leading-snug">{hit.content}</p>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        ))
      ) : (
        <Empty>Chọn một chiến lược rồi bấm “Chạy benchmark”.</Empty>
      )}
    </div>
  )
}
