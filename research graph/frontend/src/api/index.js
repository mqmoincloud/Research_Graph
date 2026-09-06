// Backend se ek hi call hoti hai:
//
//   POST /api/run   ->  form-data "file"  ->  poora graph result
//
//   result = { role_summary, requirements, selected_lanes, evidence,
//              missing_by_lane, round, exhausted, prep_document, ... }
//
// Call 1-3 minute le sakti hai - graph poora chal ke hi jawab deta hai.

import api from './client'

export async function runJd(file, onProgress) {
  const form = new FormData()
  form.append('file', file)

  const res = await api.post('/api/run', form, {
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })

  return res.data
}
