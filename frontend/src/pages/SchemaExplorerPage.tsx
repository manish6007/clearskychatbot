/** SchemaExplorerPage - Database schema exploration */

import { SchemaExplorer } from '../components/schema';
import { useSchema } from '../hooks';

export function SchemaExplorerPage() {
    const { tables, selectedTable, loading, searchTables, selectTable } = useSchema();

    return (
        <div className="h-full">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-surface-100">Schema Explorer</h1>
                <p className="text-surface-400 mt-1">
                    Browse and explore your data tables and columns.
                </p>
            </div>

            <SchemaExplorer
                tables={tables}
                selectedTable={selectedTable}
                loading={loading}
                onSearch={searchTables}
                onSelectTable={selectTable}
            />
        </div>
    );
}

export default SchemaExplorerPage;
