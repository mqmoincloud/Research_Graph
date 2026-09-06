import { useState } from 'react'

// Final prep document. Markdown ko as-is dikhate hain, saath mein
// copy aur download ke buttons.

export default function ResultPanel({ run, onReset }) {
  const [copied, setCopied] = useState(false)

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
        <h3>Prep plan</h3>
        <div className="actions">
          <button className="link" onClick={copy}>
            {copied ? 'copied' : 'copy'}
          </button>
          <button className="link" onClick={download}>
            download
          </button>
          <button className="link" onClick={onReset}>
            new run
          </button>
        </div>
      </div>

      {run.role_summary && <p className="summary">{run.role_summary}</p>}

      {/* Khaali document par khaali box mat dikhao - warna samajh hi nahi
          aata ki kya hua. Normally aisa hona nahi chahiye: llm.py khaali
          jawab par error uthata hai. Ye sirf ek safety net hai. */}
      {run.prep_document ? (
        <pre className="doc">{run.prep_document}</pre>
      ) : (
        <p className="error-text">
          Run poora ho gaya lekin document khaali aaya. Backend terminal
          dekho — wahan “[llm] jawab mila: N characters” line aani chahiye.
        </p>
      )}
    </div>
  )
}
