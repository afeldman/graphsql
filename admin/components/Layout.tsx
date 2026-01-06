import { ComponentChildren } from "preact";
import Navbar from "./Navbar.tsx";
import Sidebar from "./Sidebar.tsx";

interface LayoutProps {
  user: Record<string, unknown>;
  children: ComponentChildren;
}

export default function Layout({ user, children }: LayoutProps) {
  return (
    <div class="min-h-screen bg-base-200">
      <Navbar user={user} />
      <div class="flex">
        <Sidebar />
        <main class="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
