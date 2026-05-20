import React from 'react'
import useStore from '../store/useStore'

export default function AportesTable() {
  const aportes = useStore((s) => s.aportes)

  return (
    <div>
      <h3 className="text-sm font-medium mb-2">Aportes</h3>
      <div className="overflow-auto max-h-[40vh]">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500">
              <th>Municipio</th>
              <th>Tipo</th>
              <th>Fecha</th>
              <th>Confianza</th>
            </tr>
          </thead>
          <tbody>
            {aportes.map((a) => (
              <tr key={a.id} className="border-t">
                <td className="py-2">{a.municipio}</td>
                <td>{a.tipo}</td>
                <td>{a.fecha}</td>
                <td>{(a.confianza ?? 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
