import { useState } from 'react'

// Final prep document. We show the markdown as-is, along with
// copy and download buttons.
//
// The same panel shows a saved sample run (GET /api/demo/:name returns the
// same shape POST /api/run does). The only difference is the badge - without
// it there would be no way to tell a saved document from one just produced.

export default function ResultPanel({ run, onReset }) {
  const [copied, setCopied] = useState(false)

  // saved_at only comes back on a demo. toLocaleDateString on a bad string
  // gives "Invalid Date", so we check before showing anything.
  const savedDate = run.saved_at ? new Date(run.saved_at) : null
  const savedOn =
    savedDate && !isNaN(savedDate) ? savedDate.toLocaleDateString() : ''

  async function copy() {
    await navigator.clipboard.writeText(run.prep_document || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  function download() {
    const blob = new Blob([run.prep_document || ''], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'prep-plan.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="card result">
      <div className="card-head">
        <h3>
          Prep plan
          {run.is_demo && (
            <span className="badge" title={`Saved run, not a live one${savedOn ? ` — from ${savedOn}` : ''}`}>
              sample run{savedOn ? ` · ${savedOn}` : ''}
            </span>
          )}
        </h3>
        <div className="actions">
          <button className="link" onClick={copy}>
            {copied ? 'copied' : 'copy'}
          </button>
          <button className="link" onClick={download}>
            download
          </button>
          <button className="link" onClick={onReset}>
            {run.is_demo ? 'close' : 'new run'}
          </button>
        </div>
      </div>

      {run.role_summary && <p className="summary">{run.role_summary}</p>}

      {/* Do not show an empty box for an empty document - otherwise there
          is no telling what happened. Normally this should not happen: llm.py
          raises an error on an empty answer. This is only a safety net. */}
      {run.prep_document ? (
        <pre className="doc">{run.prep_document}</pre>
      ) : (
        <p className="error-text">
          The run finished but the document came back empty. Check the backend
          terminal — a “[llm] answer received: N characters” line should be there.
        </p>
      )}
    </div>
  )
}
