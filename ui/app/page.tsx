"use client"

import * as React from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BenchmarkPanel } from "@/components/benchmark-panel"
import { ChunkingPanel } from "@/components/chunking-panel"
import { CorpusPanel } from "@/components/corpus-panel"
import { RetrievalPanel } from "@/components/retrieval-panel"
import { SimilarityPanel } from "@/components/similarity-panel"
import { ErrorNote } from "@/components/shared"
import { api, type Meta } from "@/lib/api"

export default function Page() {
  const [meta, setMeta] = React.useState<Meta | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    api
      .meta()
      .then(setMeta)
      .catch((caught) =>
        setError(
          caught instanceof Error
            ? `${caught.message} — API chưa chạy? Mở terminal thứ hai và chạy: python ui/api_server.py`
            : String(caught)
        )
      )
  }, [])

  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
      <header className="mb-6">
        <div className="mb-1.5 flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="font-mono text-[11px]">
            K4-L3A · Day 07
          </Badge>
          <Badge variant="outline" className="font-mono text-[11px]">
            Nhóm Logitech
          </Badge>
          {meta && (
            <Badge
              variant="outline"
              className={
                meta.embedder_is_mock
                  ? "border-amber-500/50 font-mono text-[11px] text-amber-600 dark:text-amber-400"
                  : "border-emerald-500/40 font-mono text-[11px] text-emerald-600 dark:text-emerald-400"
              }
            >
              embedder: {meta.embedder}
            </Badge>
          )}
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">Embedding &amp; Vector Store</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Giao diện chạy trực tiếp trên <code className="font-mono">src/</code> — chunking, cosine
          similarity, vector store và tác tử RAG. Không có logic nào được viết lại ở đây; sai ở{" "}
          <code className="font-mono">src/</code> thì sai ở màn hình này.
        </p>
      </header>

      <ErrorNote error={error} />

      {meta?.embedder_is_mock && (
        <Alert className="mb-6 border-amber-500/40">
          <AlertTitle>Đang chạy MockEmbedder — điểm số là nhiễu</AlertTitle>
          <AlertDescription>
            <code className="font-mono">MockEmbedder</code> băm MD5, không mang thông tin ngữ nghĩa:{" "}
            <code className="font-mono">&quot;cat&quot;</code> gần{" "}
            <code className="font-mono">&quot;dog&quot;</code> (+0.1607) hơn cả{" "}
            <code className="font-mono">&quot;cats&quot;</code> (−0.0638). Bộ 42 test vẫn xanh vì chúng chỉ
            kiểm tra hợp đồng của hàm. Muốn thứ hạng có nghĩa, đặt{" "}
            <code className="font-mono">EMBEDDING_PROVIDER=local</code> trong{" "}
            <code className="font-mono">.env</code> rồi khởi động lại API.
          </AlertDescription>
        </Alert>
      )}

      {meta ? (
        <Tabs defaultValue="retrieval">
          <TabsList className="mb-4 flex h-auto w-full flex-wrap justify-start">
            <TabsTrigger value="retrieval">Tìm kiếm</TabsTrigger>
            <TabsTrigger value="benchmark">Benchmark</TabsTrigger>
            <TabsTrigger value="chunking">Chia nhỏ</TabsTrigger>
            <TabsTrigger value="similarity">Độ tương tự</TabsTrigger>
            <TabsTrigger value="corpus">Tài liệu</TabsTrigger>
          </TabsList>

          <TabsContent value="retrieval">
            <RetrievalPanel strategies={meta.strategies} queries={meta.queries} />
          </TabsContent>
          <TabsContent value="benchmark">
            <BenchmarkPanel strategies={meta.strategies} />
          </TabsContent>
          <TabsContent value="chunking">
            <ChunkingPanel documents={meta.documents} />
          </TabsContent>
          <TabsContent value="similarity">
            <SimilarityPanel />
          </TabsContent>
          <TabsContent value="corpus">
            <CorpusPanel documents={meta.documents} />
          </TabsContent>
        </Tabs>
      ) : (
        !error && (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full max-w-md" />
            <Skeleton className="h-64 w-full" />
          </div>
        )
      )}
    </main>
  )
}
