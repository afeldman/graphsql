interface DataGridProps {
  rows: Record<string, unknown>[];
}

export default function DataGrid({ rows }: DataGridProps) {
  if (!rows.length) {
    return <div class="text-sm text-base-content/60">No data loaded.</div>;
  }

  const columns = Object.keys(rows[0]);

  return (
    <div class="overflow-x-auto">
      <table class="table table-compact w-full">
        <thead>
          <tr>
            {columns.map((col) => <th key={col}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td key={col} class="font-mono text-xs">{String(row[col] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
