import React, { useCallback, useRef } from 'react'
import ReactFlow, { Background, Controls, MiniMap, addEdge } from 'react-flow-renderer'
import useStore from '../store/useStore'

export default function GraphView() {
  const nodes = useStore((s) => s.nodes)
  const edges = useStore((s) => s.edges)
  const setEdges = useStore((s) => s.setEdges)

  const onConnect = useCallback(
    (params) => setEdges((eds) => {
      const key = `${params.source}__${params.target}`
      const exists = eds.some(e => `${e.source}__${e.target}` === key || `${e.target}__${e.source}` === key)
      return exists ? eds : addEdge(params, eds)
    }),
    [setEdges]
  )

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
