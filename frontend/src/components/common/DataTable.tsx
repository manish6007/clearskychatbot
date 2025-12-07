/** DataTable component */

import { useMemo } from 'react';
import clsx from 'clsx';

interface DataTableProps {
    columns: string[];
    rows: unknown[][];
    maxRows?: number;
    className?: string;
}

export function DataTable({ columns, rows, maxRows = 100, className }: DataTableProps) {
    const displayRows = useMemo(() => {
        return rows.slice(0, maxRows);
    }, [rows, maxRows]);

    const formatCell = (value: unknown): string => {
        if (value === null || value === undefined) return '—';
        if (typeof value === 'number') return value.toLocaleString();
        return String(value);
    };

    return (
        <div className={clsx('overflow-auto rounded-lg border border-surface-700', className)}>
            <table className="data-table min-w-full">
                <thead>
                    <tr>
                        {columns.map((col, i) => (
                            <th key={i} className="whitespace-nowrap">
                                {col}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {displayRows.map((row, rowIdx) => (
                        <tr key={rowIdx}>
                            {row.map((cell, cellIdx) => (
                                <td key={cellIdx} className="whitespace-nowrap">
                                    {formatCell(cell)}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
            {rows.length > maxRows && (
                <div className="px-4 py-2 text-sm text-surface-400 bg-surface-800/50 border-t border-surface-700">
                    Showing {maxRows} of {rows.length} rows
                </div>
            )}
        </div>
    );
}

export default DataTable;
