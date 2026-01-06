export default function Sidebar() {
  const links = [
    { href: "/", label: "Dashboard", icon: "🏠" },
    { href: "/tables", label: "Tables", icon: "📊" },
    { href: "/monitoring", label: "Monitoring", icon: "📈" },
    { href: "/settings", label: "Settings", icon: "⚙️" },
  ];

  return (
    <aside class="w-64 bg-base-100 min-h-screen border-r border-base-200 hidden md:block">
      <nav class="p-4 space-y-2">
        {links.map((link) => (
          <a
            key={link.href}
            href={link.href}
            class="flex items-center gap-3 p-3 rounded-lg hover:bg-base-200 transition-colors"
          >
            <span class="text-lg">{link.icon}</span>
            <span class="font-medium">{link.label}</span>
          </a>
        ))}
      </nav>
    </aside>
  );
}
