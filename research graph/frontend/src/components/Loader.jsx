// Run chalne ke dauraan dikhne wala block.
//
// Backend ek hi call mein poora graph chalata hai, isliye beech ka
// live status nahi milta - sirf spinner aur bita hua time.
//
// props: seconds

export default function Loader({ seconds }) {
  return (
    <div className="loader">
      <div className="spinner" />
      <div className="loader-text">
        <strong>Research chal raha hai…</strong>
        <span>graph poora chal ke hi jawab deta hai</span>
      </div>
      <div className="loader-stats">
        <span>{seconds}s</span>
        <span>1-3 minute lag sakte hain</span>
      </div>
    </div>
  )
}
