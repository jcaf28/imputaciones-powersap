// PATH: frontend/src/services/uploadService.js

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export default async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData
  })
  if (!response.ok) {
    throw new Error('Error al procesar el archivo')
  }
  const blob = await response.blob()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.setAttribute('download', 'Activities_modificado.xlsx')
  document.body.appendChild(link)
  link.click()
  link.remove()
}