"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { AudienceBadge } from "@/components/shared"
import type { DocumentMeta } from "@/lib/api"

export function CorpusPanel({ documents }: { documents: DocumentMeta[] }) {
  const total = documents.reduce((sum, doc) => sum + doc.chars, 0)
  const byAudience = documents.reduce<Record<string, number>>((counts, doc) => {
    counts[doc.audience] = (counts[doc.audience] ?? 0) + 1
    return counts
  }, {})

  return (
    <Card>
      <CardHeader>
        <CardTitle>Bộ tài liệu</CardTitle>
        <CardDescription>
          {documents.length} tài liệu · {total.toLocaleString("vi-VN")} ký tự ·{" "}
          {Object.entries(byAudience)
            .map(([audience, count]) => `${audience} ${count}`)
            .join(" / ")}{" "}
          — ba giá trị <code className="font-mono">audience</code> nên bộ lọc metadata có việc thật để làm.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>doc_id</TableHead>
                <TableHead>audience</TableHead>
                <TableHead>category</TableHead>
                <TableHead className="text-right">ký tự</TableHead>
                <TableHead>nguồn</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.doc_id}>
                  <TableCell className="font-mono text-xs">{doc.doc_id}</TableCell>
                  <TableCell>
                    <AudienceBadge audience={doc.audience} />
                  </TableCell>
                  <TableCell className="text-muted-foreground font-mono text-xs">{doc.category}</TableCell>
                  <TableCell className="text-right font-mono text-xs tabular-nums">
                    {doc.chars.toLocaleString("vi-VN")}
                  </TableCell>
                  <TableCell>
                    <a
                      href={doc.source_url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="text-muted-foreground hover:text-foreground text-xs underline underline-offset-2"
                    >
                      utc.edu.vn
                    </a>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
