import React, { useCallback, useEffect, useMemo } from 'react'
import ReactFlow, { Background, Controls, MiniMap, addEdge, useReactFlow } from 'react-flow-renderer'
import useStore from '../store/useStore'

function dedupeEdges(edges) {
  const map = new Map()
  const result = []
  for (const e of edges) {
    const key = `${e.source}__${e.target}`
    const list = map.get(key) || []
    if (list.length < 2) {
      list.push(e)
      map.set(key, list)
      result.push(e)
    }
  }
  return result
}

export default function GraphView() {
  const nodes = useStore((s) => s.nodes)
  const edges = useStore((s) => s.edges)
  const setEdges = useStore((s) => s.setEdges)
  const rf = useReactFlow()

  useEffect(() => {
    // dedupe and limit edges
    const cleaned = dedupeEdges(edges)
    setEdges(cleaned)
  }, [edges, setEdges])

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges])

  return (
    <div className="flex-1" style={{ height: '100%' }}>
      <ReactFlow nodes={nodes} edges={edges} onConnect={onConnect} fitView>
        <Background />
        <MiniMap />
        <Controls />
      </ReactFlow>
    </div>
  )
}
