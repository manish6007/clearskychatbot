/** Schema-related TypeScript types */

export interface ColumnInfo {
    name: string;
    data_type: string;
    description?: string;
    is_nullable?: boolean;
    is_partition_key?: boolean;
    sample_values?: string[];
}

export interface TableInfo {
    catalog: string;
    database: string;
    name: string;
    full_name: string;
    description?: string;
    columns: ColumnInfo[];
    row_count?: number;
    size_bytes?: number;
    partition_keys?: string[];
    location?: string;
}

export interface SchemaInfo {
    catalog: string;
    name: string;
    description?: string;
    tables: TableInfo[];
}
