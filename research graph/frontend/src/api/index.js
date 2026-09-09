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

export async function listDemos() {
  const res = await api.get('/api/demo')
  return res.data
}

export async function loadDemo(name) {
  const res = await api.get(`/api/demo/${name}`)
  return res.data
}
