import { useEffect, useRef, useState } from 'react'
import FileUpload from './components/FileUpload'
import Loader from './components/Loader'
import ResultPanel from './components/ResultPanel'
import { runJd } from './api'

// Full flow:
//   1. Pick the JD file
//   2. "Start research" -> POST /api/run
//   3. the backend runs the whole graph (1-3 min) and returns the result

export default function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [error, setError] = useState('')

  const timerRef = useRef(null)

  // We only count elapsed time - the backend sends nothing in between.
  useEffect(() => {
    if (!running) return

    setSeconds(0)
    timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000)

    return () => clearInterval(timerRef.current)
  }, [running])

  async function handleStart() {
    setError('')
    setRunning(true)
    try {
      setResult(await runJd(file))
    } catch (err) {
      setError(err.message)
    } finally {
      setRunning(false)
    }
  }

  function handleReset() {
    setResult(null)
    setError('')
  }

  const isDone = Boolean(result)

  return (
    <div className="page">
      <header className="header">
        <h1>Prep Graph</h1>
        <p>Drop in a job description, get a full interview prep plan back.</p>
      </header>

      <main className="main">
        <FileUpload
          label="Job description"
          hint="PDF or .txt of the JD — this is the research input"
          disabled={running || isDone}
          onPicked={setFile}
          onCleared={() => setFile(null)}
        />

        {error && <div className="error-box">{error}</div>}

        {!isDone && (
          <div className="run-bar">
            {running ? (
              <Loader seconds={seconds} />
            ) : (
              <>
                <button
                  className="primary"
                  disabled={!file}
                  onClick={handleStart}
                >
                  Start research
                </button>
                <span className="run-hint">
                  {file
                    ? 'Ready — press the button and the graph starts.'
                    : 'Pick the JD file first.'}
                </span>
              </>
            )}
          </div>
        )}

        {isDone && <ResultPanel run={result} onReset={handleReset} />}
      </main>
    </div>
  )
}
