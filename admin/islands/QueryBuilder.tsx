import { useState } from "preact/hooks";

export default function QueryBuilder() {
  const [table, setTable] = useState("");
  const [limit, setLimit] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const addFilter = () => {
    setFilters({ ...filters, [`col${Object.keys(filters).length + 1}`]: "" });
  };

  return (
    <div class="card bg-base-100 shadow">
      <div class="card-body space-y-4">
        <h2 class="card-title">Visual Query Builder</h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Table</label>
            <input
              class="input input-bordered w-full"
              placeholder="users"
              value={table}
              onInput={(e) => setTable((e.target as HTMLInputElement).value)}
            />
          </div>
          <div>
            <label class="label">Limit</label>
            <input
              class="input input-bordered w-full"
              type="number"
              min={1}
              value={limit}
              onInput={(e) => setLimit(Number((e.target as HTMLInputElement).value))}
            />
          </div>
        </div>
        <div>
          <div class="flex justify-between items-center mb-2">
            <span class="font-semibold">Filters</span>
            <button type="button" class="btn btn-xs" onClick={addFilter}>Add</button>
          </div>
          <div class="space-y-2">
            {Object.entries(filters).map(([key, value]) => (
              <input
                key={key}
                class="input input-bordered w-full"
                placeholder={`${key} = value`}
                value={value}
                onInput={(e) =>
                  setFilters({ ...filters, [key]: (e.target as HTMLInputElement).value })}
              />
            ))}
            {Object.keys(filters).length === 0 && (
              <p class="text-sm text-base-content/60">No filters yet.</p>
            )}
          </div>
        </div>
        <div class="alert alert-info text-sm">
          This is a visual stub. Hook into API client to execute constructed queries.
        </div>
      </div>
    </div>
  );
}
