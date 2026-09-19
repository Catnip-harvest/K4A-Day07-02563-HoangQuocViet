/** Typed view of ui/api_server.py. Every shape here is produced by src/. */

export interface DocumentMeta {
  doc_id: string
  title: string
  source_url: string
  retrieved_at: string
  document_version: string
  audience: string
  department: string
  category: string
  language: string
  chars: number
}

export interface GoldQuery {
  id: string
  query: string
  tests: string
  gold_answer: string
  gold_doc_ids: string[]
  metadata_filter: Record<string, string> | null
}

export interface Meta {
  embedder: string
  embedder_is_mock: boolean
  documents: DocumentMeta[]
  strategies: string[]
  queries: GoldQuery[]
}

export interface StrategyStats {
  count: number
  avg_length: number
  min_length: number
  max_length: number
  chunks: string[]
}

export interface Hit {
  id: string
  content: string
  score: number
  metadata: Record<string, string>
}

export interface BenchmarkRow {
  id: string
  query: string
  tests: string
  gold_answer: string
  gold_doc_ids: string[]
  metadata_filter: Record<string, string> | null
  results: Hit[]
  hit: boolean
  traps: string[]
}

/** Human labels for the four strategies, so the UI never shows a bare slug. */
export const STRATEGY_LABEL: Record<string, string> = {
  fixed: "Fixed size",
  sentence: "By sentence",
  recursive: "Recursive",
  heading: "By heading",
}

export const COMPARATOR_LABEL: Record<string, string> = {
  fixed_size: "Fixed size",
  by_sentences: "By sentence",
  recursive: "Recursive",
  heading: "By heading",
}

export const AUDIENCE_TONE: Record<string, string> = {
  student: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  all: "border-sky-500/40 text-sky-600 dark:text-sky-400",
  staff: "border-amber-500/40 text-amber-600 dark:text-amber-400",
}

async function call<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? undefined : { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const payload = await response.json().catch(() => ({ error: "the API returned something that is not JSON" }))
  if (!response.ok || payload.error) throw new Error(payload.error ?? `HTTP ${response.status}`)
  return payload as T
}

export const api = {
  meta: () => call<Meta>("/api/meta"),
  /** Pass `docId` to chunk a corpus document; the response echoes its text back. */
  chunk: (text: string, chunkSize: number, docId?: string) =>
    call<{ strategies: Record<string, StrategyStats>; text: string }>("/api/chunk", {
      text,
      chunk_size: chunkSize,
      doc_id: docId,
    }),
  similarity: (pairs: [string, string][]) =>
    call<{ pairs: { a: string; b: string; score: number }[] }>("/api/similarity", { pairs }),
  search: (query: string, strategy: string, topK: number, metadataFilter: Record<string, string> | null) =>
    call<{ results: Hit[]; chunks_indexed: number }>("/api/search", {
      query,
      strategy,
      top_k: topK,
      metadata_filter: metadataFilter,
    }),
  answer: (question: string, strategy: string, topK: number) =>
    call<{ reply: string; context: Hit[]; prompt: string }>("/api/answer", {
      question,
      strategy,
      top_k: topK,
    }),
  benchmark: (strategy: string) =>
    call<{ rows: BenchmarkRow[]; hits: number; total: number; chunks_indexed: number }>("/api/benchmark", {
      strategy,
    }),
}
