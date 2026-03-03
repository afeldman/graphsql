export interface TableInfoColumn {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default?: string | null;
}

export interface TableInfo {
  name: string;
  columns: TableInfoColumn[];
  primary_keys: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}
