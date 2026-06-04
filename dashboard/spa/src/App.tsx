import React, { useEffect } from 'react'
import { ReactFlowProvider } from 'react-flow-renderer'
import ImageUpload from './components/ImageUpload'
import AportesTable from './components/AportesTable'
import GraphView from './components/GraphView'
import useStore from './store/useStore'

export default function App() {
  const connect = useStore((s) => s.connect)

  useEffect(() => {
    connect()
  }, [connect])

  return (
    <ReactFlowProvider>
    <div className="h-screen bg-gray-50 text-gray-800">
      <header className="h-14 bg-white shadow-sm flex items-center px-4">
        <button className="p-2 rounded-md mr-3 hover:bg-gray-100">☰</button>
        <h1 className="text-lg font-semibold">Pictograma</h1>
        <div className="ml-auto flex items-center gap-3">
          <button className="p-2 rounded-md hover:bg-gray-100">⚙️</button>
          <div className="w-8 h-8 rounded-full bg-gray-200" />
        </div>
      </header>

      <main className="p-4 h-[calc(100vh-56px)] grid grid-cols-12 gap-4">
        <aside className="col-span-4 bg-white p-4 rounded-lg shadow-sm flex flex-col gap-4">
          <ImageUpload />
          <div className="flex-1 overflow-auto">
            <AportesTable />
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-2 px-3 bg-white rounded-md shadow hover:shadow-md">⬆️ Subir imagen</button>
            <button className="flex-1 py-2 px-3 bg-white rounded-md shadow hover:shadow-md">💾 Guardar aportes</button>
          </div>
        </aside>

        <section className="col-span-8 bg-white p-4 rounded-lg shadow-sm flex flex-col">
          <GraphView />
        </section>
      </main>
    </div>
    </ReactFlowProvider>
  )
}
