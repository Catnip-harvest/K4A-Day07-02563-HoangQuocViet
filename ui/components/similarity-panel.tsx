"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { ErrorNote, Score } from "@/components/shared"
import { api } from "@/lib/api"

interface Pair {
  a: string
  b: string
  guess: "cao" | "thấp" | null
  score: number | null
}

/** Bài tập 3.3 starts from the corpus, so the defaults do too. */
const DEFAULTS: [string, string][] = [
  ["Sinh viên đăng ký học phần", "Thời gian đăng ký môn học"],
  ["Ký túc xá có bao nhiêu phòng", "Thư viện mở cửa đến mấy giờ"],
  ["Phòng Đào tạo đại học", "Phòng Đào tạo đại học"],
  ["chăm sóc sức khỏe sinh viên", "khám sức khỏe định kỳ cho sinh viên"],
  ["học phí và các khoản thu", "an ninh trật tự trong trường"],
]

export function SimilarityPanel() {
  const [pairs, setPairs] = React.useState<Pair[]>(
    DEFAULTS.map(([a, b]) => ({ a, b, guess: null, score: null }))
  )
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [revealed, setRevealed] = React.useState(false)

  const allGuessed = pairs.every((pair) => pair.guess !== null)

  function update(index: number, patch: Partial<Pair>) {
    setPairs((current) => current.map((pair, i) => (i === index ? { ...pair, ...patch } : pair)))
    if (patch.a !== undefined || patch.b !== undefined) setRevealed(false)
  }

  async function reveal() {
    setBusy(true)
    setError(null)
    try {
      const response = await api.similarity(pairs.map((pair) => [pair.a, pair.b]))
      setPairs((current) => current.map((pair, i) => ({ ...pair, score: response.pairs[i].score })))
      setRevealed(true)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught))
    } finally {
      setBusy(false)
    }
  }

  // A guess of "cao" is counted right when the score clears 0.5 - the point is
  // the direction of the intuition, not a threshold anyone agreed on.
  const correct = pairs.filter(
    (pair) => pair.score !== null && (pair.score > 0.5 ? "cao" : "thấp") === pair.guess
  ).length

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Dự đoán độ tương tự</CardTitle>
          <CardDescription>
            Bài tập 3.3 yêu cầu <strong>dự đoán trước khi chạy</strong>. Nút hiện kết quả chỉ bật khi cả
            năm cặp đã có dự đoán, nên không thể xem trộm rồi mới điền.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {pairs.map((pair, index) => (
            <div key={index} className="border-border grid gap-2 rounded-lg border p-3 sm:grid-cols-[1fr_1fr_auto_auto]">
              <Input
                value={pair.a}
                onChange={(event) => update(index, { a: event.target.value })}
                placeholder="Câu A"
                className="text-xs"
              />
              <Input
                value={pair.b}
                onChange={(event) => update(index, { b: event.target.value })}
                placeholder="Câu B"
                className="text-xs"
              />
              <div className="flex gap-1.5">
                {(["cao", "thấp"] as const).map((option) => (
                  <Button
                    key={option}
                    size="sm"
                    variant={pair.guess === option ? "default" : "outline"}
                    className="h-9 px-3 text-xs"
                    onClick={() => update(index, { guess: option })}
                  >
                    {option}
                  </Button>
                ))}
              </div>
              <div className="flex min-w-24 items-center justify-end">
                {revealed && pair.score !== null ? (
                  <span
                    className={
                      (pair.score > 0.5 ? "cao" : "thấp") === pair.guess
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-destructive"
                    }
                  >
                    <Score value={pair.score} />
                  </span>
                ) : (
                  <span className="text-muted-foreground font-mono text-xs">—</span>
                )}
              </div>
            </div>
          ))}

          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={reveal} disabled={busy || !allGuessed}>
              {busy ? "Đang tính…" : "Hiện điểm thực tế"}
            </Button>
            {!allGuessed && (
              <span className="text-muted-foreground text-xs">Điền dự đoán cho cả 5 cặp trước.</span>
            )}
            {revealed && (
              <span className="text-sm">
                Đúng <strong>{correct}/5</strong> dự đoán
              </span>
            )}
          </div>

          <ErrorNote error={error} />
        </CardContent>
      </Card>

      {revealed && (
        <Alert>
          <AlertTitle>Đọc kết quả thế nào</AlertTitle>
          <AlertDescription>
            Nếu đang chạy <code className="font-mono">MockEmbedder</code>, mọi điểm số ở đây đều là nhiễu:
            nó băm MD5 chứ không hiểu ngữ nghĩa, nên chỉ hai chuỗi trùng khớp tuyệt đối mới cho{" "}
            <code className="font-mono">+1.0000</code>. Cặp số 3 cố tình để hai câu giống hệt nhau làm mốc
            kiểm chứng. Muốn điểm có ý nghĩa thì đặt{" "}
            <code className="font-mono">EMBEDDING_PROVIDER=local</code> trong <code className="font-mono">.env</code>.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
