/// <reference no-default-lib="true" />
/// <reference lib="deno.ns" />
/// <reference lib="dom" />
/// <reference lib="dom.iterable" />

import { start } from "$fresh/server.ts";
import manifest from "./fresh.gen.ts";

await start(manifest);
