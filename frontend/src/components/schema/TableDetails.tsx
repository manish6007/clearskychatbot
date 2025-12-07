/** TableDetails component */

import { Table2, Key, Hash, Calendar, Type } from 'lucide-react';
import { Card } from '../common';
import type { TableInfo } from '../../types';

interface TableDetailsProps {
    table: TableInfo;
}

const typeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    string: Type,
    varchar: Type,
    int: Hash,
    integer: Hash,
    bigint: Hash,
    double: Hash,
    float: Hash,
    decimal: Hash,
    date: Calendar,
    timestamp: Calendar,
    datetime: Calendar,
};

export function TableDetails({ table }: TableDetailsProps) {
    return (
        <Card className="h-full overflow-hidden" padding="none">
            {/* Header */}
            <div className="px-6 py-4 border-b border-surface-700 bg-gradient-to-r from-primary-500/10 to-transparent">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
                        <Table2 className="h-5 w-5 text-primary-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-surface-100">{table.name}</h2>
                        <p className="text-sm text-surface-400">
                            {table.catalog}.{table.database}
                        </p>
                    </div>
                </div>
                {table.description && (
                    <p className="mt-3 text-surface-300">{table.description}</p>
                )}
            </div>

            {/* Stats */}
            <div className="px-6 py-3 border-b border-surface-700 flex gap-6 text-sm">
                <div>
                    <span className="text-surface-500">Columns:</span>{' '}
                    <span className="text-surface-200">{table.columns.length}</span>
                </div>
                {table.row_count !== undefined && (
                    <div>
                        <span className="text-surface-500">Rows:</span>{' '}
                        <span className="text-surface-200">{table.row_count.toLocaleString()}</span>
                    </div>
                )}
                {table.partition_keys && table.partition_keys.length > 0 && (
                    <div>
                        <span className="text-surface-500">Partitions:</span>{' '}
                        <span className="text-surface-200">{table.partition_keys.join(', ')}</span>
                    </div>
                )}
            </div>

            {/* Columns */}
            <div className="max-h-[calc(100vh-350px)] overflow-y-auto">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Column</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table.columns.length > 0 ? (
                            table.columns.map((col) => {
                                const TypeIcon = typeIcons[col.data_type.toLowerCase()] || Type;
                                return (
                                    <tr key={col.name}>
                                        <td>
                                            <div className="flex items-center gap-2">
                                                {col.is_partition_key && (
                                                    <Key className="h-4 w-4 text-yellow-400" title="Partition Key" />
                                                )}
                                                <code className="text-primary-300">{col.name}</code>
                                            </div>
                                        </td>
                                        <td>
                                            <div className="flex items-center gap-2">
                                                <TypeIcon className="h-4 w-4 text-surface-500" />
                                                <span className="text-surface-400">{col.data_type}</span>
                                                {col.is_nullable === false && (
                                                    <span className="text-xs text-red-400">NOT NULL</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="text-surface-400">
                                            {col.description || '—'}
                                        </td>
                                    </tr>
                                );
                            })
                        ) : (
                            <tr>
                                <td colSpan={3} className="text-center text-surface-500 py-8">
                                    No column information available
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </Card>
    );
}

export default TableDetails;
