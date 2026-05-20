import create from 'zustand'

type Aporte = { id: string; municipio: string; tipo: string; fecha: string; confianza?: number }

const useStore = create((set, get) => ({
  aportes: [] as Aporte[],
  nodes: [],
  edges: [],
  ws: null as WebSocket | null,
  connect: () => {
    if (get().ws) return
    const ws = new WebSocket('ws://localhost:3000')
    ws.onopen = () => console.log('ws open')
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'init') {
          set({ aportes: msg.data.interacciones || [] })
          // build nodes/edges
          const municipios = Array.from(new Set((msg.data.interacciones || []).map((i) => i.municipio)))
          const nodes = municipios.map((m, idx) => ({ id: m, data: { label: m }, position: { x: 100 + idx * 120, y: 100 } }))
          const edges = (msg.data.interacciones || []).map((i, idx) => ({ id: `e${idx}`, source: i.municipio, target: msg.data.pictogramas?.[0]?.id || 'P0' }))
          set({ nodes, edges })
        }
        if (msg.type === 'new_interaccion') {
          set((s) => ({ aportes: [...s.aportes, msg.data] }))
          // add node/edge
          set((s) => {
            const nodeExists = s.nodes.find((n) => n.id === msg.data.municipio)
            const nodes = nodeExists ? s.nodes : [...s.nodes, { id: msg.data.municipio, data: { label: msg.data.municipio }, position: { x: Math.random() * 600, y: Math.random() * 400 } }]
            const edges = [...s.edges, { id: `edge_${Date.now()}`, source: msg.data.municipio, target: msg.data.pictograma || 'P0' }]
            return { nodes, edges }
          })
        }
      } catch (err) {
        console.error(err)
      }
    }
    ws.onclose = () => set({ ws: null })
    set({ ws })
  },
  setEdges: (edges) => set({ edges }),
  uploadImage: (dataUrl: string | null) => {
    console.log('Upload image (client-side):', dataUrl?.slice(0, 60))
    // send to backend later
  }
}))

export default useStore
