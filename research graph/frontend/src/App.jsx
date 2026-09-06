import { useEffect, useRef, useState } from 'react'
import FileUpload from './components/FileUpload'
import Loader from './components/Loader'
import ResultPanel from './components/ResultPanel'
import { runJd } from './api'

// Poora flow:
//   1. JD ki file chuno
//   2. "Start research" -> POST /api/run
//   3. backend graph poora chalata hai (1-3 min) aur result wapas deta hai

export default function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [error, setError] = useState('')

  const timerRef = useRef(null)

  // Sirf bita hua time ginte hain - backend beech mein kuch nahi bhejta.
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
        <p>Job description daalo, poora interview prep plan wapas lo.</p>
      </header>

      <main className="main">
        <FileUpload
          label="Job description"
          hint="JD ka PDF ya .txt — yahi research ka input hai"
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
                    ? 'Ready — button dabao aur graph chalu ho jayega.'
                    : 'Pehle JD ki file chuno.'}
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
