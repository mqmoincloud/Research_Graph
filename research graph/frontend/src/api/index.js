// There is only one call to the backend:
//
//   POST /api/run   ->  form-data "file"  ->  the whole graph result
//
//   result = { role_summary, requirements, selected_lanes, evidence,
//              missing_by_lane, round, exhausted, prep_document, ... }
//
// The call can take 1-3 minutes - the graph answers only once it finishes.

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
