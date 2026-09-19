"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Textarea } from "@/components/ui/textarea"
import { Empty, ErrorNote } from "@/components/shared"
import { COMPARATOR_LABEL, api, type DocumentMeta, type StrategyStats } from "@/lib/api"

const SAMPLE = `THÔNG TIN CHUNG

Địa chỉ: Tầng 1,5, 6, 7 Nhà A8; Trường Đại học GTVT. Điện thoại: (024) 37669860.

CHỨC NĂNG NHIỆM VỤ

Trung tâm Thông tin - Thư viện có chức năng tham mưu cho Hiệu trưởng trong việc quản lý, tổng hợp, đề xuất ý kiến. Đối tượng bạn đọc: giảng viên, cán bộ nghiên cứu, nghiên cứu sinh, học viên cao học và sinh viên trong và ngoài Trường.`

export function ChunkingPanel({ documents }: { documents: DocumentMeta[] }) {
  const [text, setText] = React.useState(SAMPLE)
  const [size, setSize] = React.useState(200)
  const [stats, setStats] = React.useState<Record<string, StrategyStats> | null>(null)
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [open, setOpen] = React.useState<string | null>(null)

  async function run(docId?: string) {
    setBusy(true)
    setError(null)
    try {
      const response = await api.chunk(text, size, docId)
      setStats(response.strategies)
      if (docId) setText(response.text)
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
          <CardTitle>So sánh chiến lược chia nhỏ</CardTitle>
          <CardDescription>
            Cùng một văn bản qua cả bốn chiến lược. Ba chiến lược đầu là{" "}
            <code className="font-mono">ChunkingStrategyComparator</code> trong{" "}
            <code className="font-mono">src/chunking.py</code>; chiến lược theo tiêu đề là phần mở rộng
            cho Giai đoạn 2.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={8}
            className="font-mono text-xs"
            placeholder="Dán văn bản vào đây…"
          />

          <div className="flex flex-wrap items-end gap-4">
            <div className="min-w-56 flex-1 space-y-2">
              <Label className="text-muted-foreground text-xs font-normal">
                chunk_size: <span className="text-foreground font-mono tabular-nums">{size}</span> ký tự
              </Label>
              <Slider
                min={80}
                max={1200}
                step={20}
                value={[size]}
                onValueChange={(next) => setSize(Array.isArray(next) ? next[0] : next)}
              />
            </div>
            <Button onClick={() => run()} disabled={busy || !text.trim()}>
              {busy ? "Đang chạy…" : "So sánh"}
            </Button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <span className="text-muted-foreground self-center text-xs">Nạp tài liệu thật:</span>
            {documents.map((doc) => (
              <Button
                key={doc.doc_id}
                size="sm"
                variant="ghost"
                disabled={busy}
                className="h-7 font-mono text-[11px]"
                onClick={() => run(doc.doc_id)}
              >
                {doc.doc_id}
              </Button>
            ))}
          </div>

          <ErrorNote error={error} />
        </CardContent>
      </Card>

      {stats ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(stats).map(([name, stat]) => (
            <Card key={name} className="gap-3">
              <CardHeader className="pb-0">
                <CardTitle className="text-sm">{COMPARATOR_LABEL[name] ?? name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <dl className="space-y-1 font-mono text-xs">
                  <Row label="số chunk" value={stat.count} strong />
                  <Row label="trung bình" value={stat.avg_length} />
                  <Row label="ngắn nhất" value={stat.min_length} />
                  <Row label="dài nhất" value={stat.max_length} />
                </dl>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 w-full text-[11px]"
                  onClick={() => setOpen(open === name ? null : name)}
                >
                  {open === name ? "Ẩn chunk" : "Xem chunk"}
                </Button>
                {open === name && (
                  <div className="max-h-72 space-y-1.5 overflow-y-auto">
                    {stat.chunks.map((chunk, index) => (
                      <div key={index} className="bg-muted/50 rounded p-2">
                        <div className="text-muted-foreground mb-1 flex justify-between font-mono text-[10px]">
                          <span>#{index}</span>
                          <span>{chunk.length}</span>
                        </div>
                        <p className="text-[11px] leading-snug break-words whitespace-pre-wrap">{chunk}</p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Empty>Bấm “So sánh” để chạy cả bốn chiến lược trên văn bản ở trên.</Empty>
      )}
    </div>
  )
}

function Row({ label, value, strong }: { label: string; value: number; strong?: boolean }) {
  return (
    <div className="flex justify-between">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={strong ? "text-foreground font-semibold tabular-nums" : "tabular-nums"}>{value}</dd>
    </div>
  )
}
