import React, { useCallback, useState } from 'react'
import useStore from '../store/useStore'

export default function ImageUpload() {
  const [preview, setPreview] = useState<string | null>(null)
  const upload = useStore((s) => s.uploadImage)

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0]
    if (f && /image\/(png|jpeg|jpg)/.test(f.type)) {
      const reader = new FileReader()
      reader.onload = () => {
        setPreview(reader.result as string)
      }
      reader.readAsDataURL(f)
    }
  }, [])

  const onFile = (ev: React.ChangeEvent<HTMLInputElement>) => {
    const f = ev.target.files?.[0]
    if (f && /image\/(png|jpeg|jpg)/.test(f.type)) {
      const reader = new FileReader()
      reader.onload = () => setPreview(reader.result as string)
      reader.readAsDataURL(f)
    }
  }

  return (
    <div>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className="border-2 border-dashed border-gray-200 rounded-md p-4 flex flex-col items-center justify-center h-40"
      >
        {preview ? (
          <img src={preview} alt="preview" className="max-h-32" />
        ) : (
          <div className="text-gray-400">Arrastra una imagen PNG/JPG aquí</div>
        )}
      </div>
      <div className="mt-2 flex gap-2">
        <label className="py-2 px-3 bg-white rounded-md shadow cursor-pointer">
          Seleccionar
n          <input onChange={onFile} type="file" accept="image/png, image/jpeg" className="hidden" />
        </label>
        <button
          onClick={() => upload(preview)}
          className="py-2 px-3 bg-green-50 rounded-md shadow hover:bg-green-100"
        >
          Subir imagen
        </button>
      </div>
    </div>
  )
}
