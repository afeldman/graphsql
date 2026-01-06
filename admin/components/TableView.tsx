interface TableViewProps {
  table: string;
  rows: Record<string, unknown>[];
}

export default function TableView({ table, rows }: TableViewProps) {
  const columns = rows.length ? Object.keys(rows[0]) : [];

  return (
    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <h3 class="card-title mb-2">{table}</h3>
        {rows.length === 0
          ? <div class="text-sm text-base-content/60">No records</div>
          : (
            <div class="overflow-x-auto">
              <table class="table table-zebra">
                <thead>
                  <tr>
                    {columns.map((col) => <th key={col}>{col}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, idx) => (
                    <tr key={idx}>
                      {columns.map((col) => (
                        <td key={col} class="font-mono text-xs">
                          {String(row[col] ?? "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>
    </div>
  );
}
