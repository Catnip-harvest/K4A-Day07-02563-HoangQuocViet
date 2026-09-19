"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { AudienceBadge, Empty, ErrorNote, Score, StrategyPicker } from "@/components/shared"
import { api, type GoldQuery, type Hit } from "@/lib/api"

const AUDIENCES = ["student", "all", "staff"] as const

export function RetrievalPanel({
  strategies,
  queries,
}: {
  strategies: string[]
  queries: GoldQuery[]
}) {
  const [query, setQuery] = React.useState("Ai quản lý ký túc xá của trường?")
  const [strategy, setStrategy] = React.useState("recursive")
  const [audience, setAudience] = React.useState<string | null>(null)
  const [topK, setTopK] = React.useState(3)
  const [hits, setHits] = React.useState<Hit[] | null>(null)
  const [reply, setReply] = React.useState<string | null>(null)
  const [indexed, setIndexed] = React.useState<number | null>(null)
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  async function run() {
    setBusy(true)
    setError(null)
    try {
      const filter = audience ? { audience } : null
      const [search, answer] = await Promise.all([
        api.search(query, strategy, topK, filter),
        api.answer(query, strategy, topK),
      ])
      setHits(search.results)
      setIndexed(search.chunks_indexed)
      setReply(answer.reply)
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
          <CardTitle>Tìm kiếm &amp; trả lời</CardTitle>
          <CardDescription>
            <code className="font-mono">EmbeddingStore.search</code> /{" "}
            <code className="font-mono">search_with_filter</code> rồi đưa qua{" "}
            <code className="font-mono">KnowledgeBaseAgent.answer</code>. Đổi chiến lược là nạp lại kho
            với cách chia nhỏ khác — mọi thứ còn lại giữ nguyên.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && !busy && run()}
              placeholder="Nhập câu hỏi…"
            />
            <Button onClick={run} disabled={busy || !query.trim()}>
              {busy ? "…" : "Chạy"}
            </Button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <span className="text-muted-foreground self-center text-xs">Câu hỏi mẫu:</span>
            {queries.map((gold) => (
              <Button
                key={gold.id}
                size="sm"
                variant="ghost"
                className="h-7 text-[11px]"
                onClick={() => {
                  setQuery(gold.query)
                  setAudience(gold.metadata_filter?.audience ?? null)
                }}
              >
                {gold.id}
              </Button>
            ))}
          </div>

          <Separator />

          <div className="grid gap-4 sm:grid-cols-3">
            <StrategyPicker
              strategies={strategies}
              value={strategy}
              onChange={setStrategy}
              disabled={busy}
            />

            <div className="space-y-1.5">
              <Label className="text-muted-foreground text-xs font-normal">Lọc audience</Label>
              <div className="flex flex-wrap gap-1.5">
                <Button
                  size="sm"
                  variant={audience === null ? "default" : "outline"}
                  onClick={() => setAudience(null)}
                >
                  không lọc
                </Button>
                {AUDIENCES.map((value) => (
                  <Button
                    key={value}
                    size="sm"
                    variant={audience === value ? "default" : "outline"}
                    onClick={() => setAudience(value)}
                  >
                    {value}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-muted-foreground text-xs font-normal">top_k</Label>
              <div className="flex gap-1.5">
                {[1, 3, 5, 10].map((value) => (
                  <Button
                    key={value}
                    size="sm"
                    variant={topK === value ? "default" : "outline"}
                    className="w-11 font-mono"
                    onClick={() => setTopK(value)}
                  >
                    {value}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          <ErrorNote error={error} />
        </CardContent>
      </Card>

      {reply !== null && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Câu trả lời của agent</CardTitle>
            <CardDescription>
              Lab không cấu hình mô hình sinh, nên agent trả về nguyên văn đoạn đứng đầu — đúng cái mà
              prompt đã đưa cho mô hình. Không có chỗ cho nó bịa.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{reply}</p>
          </CardContent>
        </Card>
      )}

      {hits ? (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">
              Top {hits.length}
              {indexed !== null && (
                <span className="text-muted-foreground ml-2 font-mono text-xs font-normal">
                  trong {indexed} chunk
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {hits.length === 0 && <Empty>Bộ lọc không để lại chunk nào.</Empty>}
            {hits.map((hit, index) => (
              <div key={hit.id} className="border-border rounded-lg border p-3">
                <div className="mb-1.5 flex flex-wrap items-center gap-2">
                  <span className="text-muted-foreground font-mono text-xs">#{index + 1}</span>
                  <Score value={hit.score} />
                  <span className="font-mono text-xs">{hit.metadata.doc_id}</span>
                  <AudienceBadge audience={hit.metadata.audience} />
                  <span className="text-muted-foreground font-mono text-[11px]">
                    {hit.metadata.category}
                  </span>
                </div>
                <p className="text-foreground/80 line-clamp-4 text-xs leading-relaxed">{hit.content}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : (
        <Empty>Chạy một câu hỏi để xem kho trả về gì.</Empty>
      )}
    </div>
  )
}
