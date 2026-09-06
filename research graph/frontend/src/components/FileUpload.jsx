import { useRef, useState } from 'react'

// Sirf file chunne ka box. Upload yahan nahi hota - file parent ko
// onPicked(file) se chali jaati hai, aur asli call "Start research"
// dabane par hoti hai.
//
// props: label, hint, disabled, onPicked(file), onCleared()

export default function FileUpload({
  label,
  hint,
  disabled = false,
  onPicked,
  onCleared,
}) {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)

  function handleFile(picked) {
    if (!picked) return

    const name = picked.name.toLowerCase()
    if (!name.endsWith('.pdf') && !name.endsWith('.txt')) {
      setError('PDF ya .txt file chalegi.')
      return
    }
    if (picked.size > 20 * 1024 * 1024) {
      setError('File 20 MB se badi hai.')
      return
    }

    setError('')
    setFile(picked)
    onPicked?.(picked)
  }

  function clear() {
    setFile(null)
    setError('')
    if (inputRef.current) inputRef.current.value = ''
    onCleared?.()
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    if (!disabled) handleFile(e.dataTransfer.files?.[0])
  }

  return (
    <div className="card">
      <div className="card-head">
        <h3>{label}</h3>
        {file && !disabled && (
          <button className="link" onClick={clear}>
            remove
          </button>
        )}
      </div>

      {!file && (
        <div
          className={`drop ${dragging ? 'drop-active' : ''} ${disabled ? 'drop-off' : ''}`}
          onClick={() => !disabled && inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <div className="drop-icon">PDF</div>
          <p className="drop-title">Click karo ya file yahan drag karo</p>
          <p className="drop-hint">{hint}</p>
        </div>
      )}

      {file && (
        <div className="file-row">
          <div className="file-info">
            <span className="file-name">{file.name}</span>
            <span className="file-meta">{(file.size / 1024).toFixed(0)} KB</span>
          </div>
          <span className="status status-ok">ready</span>
        </div>
      )}

      {error && <p className="error-text">{error}</p>}

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt"
        hidden
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
    </div>
  )
}
