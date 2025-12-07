/** SchemaExplorer component */

import { useState } from 'react';
import { Search, Database, Table2, ChevronRight } from 'lucide-react';
import { Card, LoadingSpinner } from '../common';
import { TableDetails } from './TableDetails';
import type { TableInfo } from '../../types';

interface SchemaExplorerProps {
    tables: TableInfo[];
    selectedTable: TableInfo | null;
    loading: boolean;
    onSearch: (query: string) => void;
    onSelectTable: (tableName: string) => void;
}

export function SchemaExplorer({
    tables,
    selectedTable,
    loading,
    onSearch,
    onSelectTable,
}: SchemaExplorerProps) {
    const [searchQuery, setSearchQuery] = useState('');

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(searchQuery);
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            {/* Tables list */}
            <div className="lg:col-span-1 space-y-4">
                <Card padding="sm">
                    <form onSubmit={handleSearch} className="flex gap-2">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-500" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search tables..."
                                className="w-full pl-10 pr-4 py-2 bg-surface-800/50 rounded-lg border border-surface-600 text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-smooth"
                            />
                        </div>
                    </form>
                </Card>

                <Card className="overflow-hidden" padding="none">
                    <div className="px-4 py-3 border-b border-surface-700 flex items-center gap-2">
                        <Database className="h-4 w-4 text-primary-400" />
                        <span className="font-medium text-surface-200">Tables</span>
                        <span className="ml-auto text-xs text-surface-500">{tables.length}</span>
                    </div>

                    <div className="max-h-[calc(100vh-300px)] overflow-y-auto">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <LoadingSpinner size="sm" />
                            </div>
                        ) : tables.length === 0 ? (
                            <div className="px-4 py-8 text-center text-surface-500">
                                No tables found
                            </div>
                        ) : (
                            <div className="divide-y divide-surface-700/50">
                                {tables.map((table) => (
                                    <button
                                        key={table.full_name}
                                        onClick={() => onSelectTable(table.name)}
                                        className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-smooth ${selectedTable?.name === table.name
                                                ? 'bg-primary-500/20 text-primary-300'
                                                : 'text-surface-300 hover:bg-surface-700/50 hover:text-surface-100'
                                            }`}
                                    >
                                        <Table2 className="h-4 w-4 text-surface-500" />
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium truncate">{table.name}</p>
                                            <p className="text-xs text-surface-500 truncate">{table.database}</p>
                                        </div>
                                        <ChevronRight className="h-4 w-4 text-surface-500" />
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </Card>
            </div>

            {/* Table details */}
            <div className="lg:col-span-2">
                {selectedTable ? (
                    <TableDetails table={selectedTable} />
                ) : (
                    <Card className="h-full flex items-center justify-center">
                        <div className="text-center">
                            <Database className="h-12 w-12 text-surface-600 mx-auto mb-3" />
                            <p className="text-surface-400">Select a table to view details</p>
                        </div>
                    </Card>
                )}
            </div>
        </div>
    );
}

export default SchemaExplorer;
