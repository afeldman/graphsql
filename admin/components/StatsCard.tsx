interface StatsCardProps {
  title: string;
  value: number | string;
  icon?: string;
  color?: string;
}

export default function StatsCard({ title, value, icon, color = "bg-primary" }: StatsCardProps) {
  return (
    <div class={`card shadow-md text-white ${color}`}>
      <div class="card-body">
        <div class="flex justify-between items-center">
          <div>
            <p class="opacity-80 text-sm">{title}</p>
            <p class="text-3xl font-bold">{value}</p>
          </div>
          {icon && <span class="text-3xl">{icon}</span>}
        </div>
      </div>
    </div>
  );
}
