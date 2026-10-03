import { useMemo } from 'react'
import { tableFeatures, useTable } from '@tanstack/react-table'
import type { ColumnDef } from '@tanstack/react-table'
import type { Case, Code, MatrixCell } from './entities'

const features = tableFeatures({})
type MatrixRow = { codeId: number; codeName: string; counts: Record<string, number> }

export function useMatrix(codes: Code[], cases: Case[], cells: MatrixCell[], select: (code: number, case_: number) => void) {
  const rows = useMemo(() => codes.map(code => ({ codeId: code.id, codeName: code.name, counts: Object.fromEntries(cases.map(case_ => [String(case_.id), cells.find(cell => cell.code_id === code.id && cell.case_id === case_.id)?.count ?? 0])) })), [codes, cases, cells])
  const columns = useMemo<ColumnDef<typeof features, MatrixRow>[]>(() => [
    { id: 'code', accessorKey: 'codeName', header: 'Code' },
    ...cases.map(case_ => ({ id: String(case_.id), accessorFn: (row: MatrixRow) => row.counts[String(case_.id)], header: case_.name })),
  ], [cases])
  const table = useTable({ features, columns, data: rows })
  const maximum = Math.max(1, ...cells.map(cell => cell.count))
  return { table, rows: table.getRowModel().rows.map(row => ({ id: row.id, cells: row.getAllCells().map(cell => ({ id: cell.id, cell, label: `${row.original.codeName} · ${cell.column.columnDef.header} · ${cell.getValue()} segments`, isCode: cell.column.id === 'code', style: { '--heat': Number(cell.getValue()) / maximum * 0.6 }, select: () => select(row.original.codeId, Number(cell.column.id)) })) })) }
}
