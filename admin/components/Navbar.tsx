import { Head } from "$fresh/runtime.ts";

interface NavbarProps {
  user: any;
}

export default function Navbar({ user }: NavbarProps) {
  return (
    <>
      <Head>
        <title>GraphSQL Admin</title>
        <link rel="stylesheet" href="/styles.css" />
      </Head>
      <div class="navbar bg-base-100 shadow-sm sticky top-0 z-20">
        <div class="flex-1">
          <a class="btn btn-ghost normal-case text-xl" href="/">
            GraphSQL Admin
          </a>
        </div>
        <div class="flex-none gap-2">
          {user && (
            <div class="dropdown dropdown-end">
              <label tabIndex={0} class="btn btn-ghost btn-circle avatar placeholder">
                <div class="bg-neutral-focus text-neutral-content rounded-full w-10">
                  <span>{user.username?.slice(0, 2)?.toUpperCase() ?? "U"}</span>
                </div>
              </label>
              <ul tabIndex={0} class="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52">
                <li><span class="font-semibold">{user.username ?? "User"}</span></li>
                <li><a href="/settings">Settings</a></li>
                <li><a href="/logout">Logout</a></li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
