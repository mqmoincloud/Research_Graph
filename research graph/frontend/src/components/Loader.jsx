// The block shown while a run is going.
//
// The backend runs the whole graph in one call, so there is no live
// status in between - only a spinner and the elapsed time.
//
// props: seconds

export default function Loader({ seconds }) {
  return (
    <div className="loader">
      <div className="spinner" />
      <div className="loader-text">
        <strong>Research is running…</strong>
        <span>the graph answers only once it finishes</span>
      </div>
      <div className="loader-stats">
        <span>{seconds}s</span>
        <span>can take 1-3 minutes</span>
      </div>
    </div>
  )
}
