# GraphSQL Admin Dashboard

TypeScript/Fresh web application for managing GraphSQL databases.

## Features

- 🔐 **JWT Authentication** - Secure login with token-based auth
- 📊 **Dashboard** - Real-time stats, health monitoring, table overview
- 🗂️ **Table Browser** - Browse and search tables with pagination
- 📝 **Record Editor** - Create, read, update, delete records
- 🔍 **GraphQL Playground** - Interactive GraphQL IDE
- 🔄 **Live Updates** - WebSocket-based real-time data sync
- ⚡ **WebSocket Support** - Real-time events and notifications
- 🎨 **Tailwind + daisyUI** - Modern, responsive UI

## Tech Stack

- **Framework:** [Fresh](https://fresh.deno.dev/) - Full-stack web framework
- **Runtime:** [Deno](https://deno.land/) - Modern JavaScript/TypeScript runtime
- **UI Components:** [Preact](https://preactjs.com/) - Lightweight React alternative
- **Styling:** [Tailwind CSS](https://tailwindcss.com/) + [daisyUI](https://daisyui.com/)
- **API Communication:** Fetch API + WebSockets

## Project Structure

```
admin/
├── routes/              # Fresh routes (file-based routing)
│   ├── index.tsx       # Dashboard home
│   ├── login.tsx       # Login page
│   ├── logout.ts       # Logout handler
│   ├── settings/       # Settings pages
│   ├── monitoring/     # Monitoring dashboards
│   ├── tables/         # Table browsing
│   └── api/            # API routes
├── islands/            # Interactive components
│   ├── QueryBuilder.tsx
│   ├── GraphQLPlayground.tsx
│   ├── TableBrowser.tsx
│   └── LiveFeed.tsx
├── components/         # Shared components
│   ├── Layout.tsx
│   ├── Navbar.tsx
│   ├── Sidebar.tsx
│   └── ...
├── lib/                # Utility functions
│   ├── auth.ts         # Authentication helpers
│   ├── api.ts          # API client
│   ├── types.ts        # TypeScript types
│   └── ...
├── static/             # Static assets
├── deno.json           # Deno configuration
└── deno.lock           # Dependency lock file
```

## Getting Started

### Prerequisites

- [Deno](https://deno.land/) 2.0+
- Running GraphSQL backend server

### Installation

```bash
# Install dependencies (handled by Deno)
deno cache

# Set environment variables
cp .env.example .env
# Edit .env with your GraphSQL backend URL and JWT secret
```

### Development

```bash
# Run development server (hot reload)
deno task dev

# Or using make
make dev
```

The admin will be available at `http://localhost:8000`

### Building

```bash
# Create production build
deno task build

# Start production server
deno task start
```

## Environment Variables

Required environment variables in `.env`:

```env
GRAPHSQL_URL=http://localhost:8001        # GraphSQL backend URL
JWT_SECRET=your-secret-key                # Secret for JWT verification
JWT_ALGORITHM=HS256                       # JWT algorithm (default: HS256)
JWT_EXPIRATION=3600                       # Token expiration in seconds
```

## Scripts

```bash
# Run tasks
deno task dev              # Development server
deno task build           # Production build
deno task start           # Start production server

# Code quality
deno lint admin           # Lint TypeScript
deno fmt admin            # Format code
deno check admin          # Type checking

# Or using make from root directory
make deno-lint            # Lint admin code
make deno-fmt             # Format admin code
make quality              # Run all quality checks
```

## Routing

Fresh uses file-based routing:

- `/admin/routes/index.tsx` → `/`
- `/admin/routes/login.tsx` → `/login`
- `/admin/routes/tables/index.tsx` → `/tables`
- `/admin/routes/tables/[table].tsx` → `/tables/:table`
- `/admin/routes/api/auth.ts` → `/api/auth`

## Authentication

Authentication flow:

1. User enters credentials on `/login`
2. Backend validates and returns JWT token
3. Token stored in `HttpOnly` cookie
4. All API requests include token in `Authorization` header
5. Middleware (`requireAuth`) validates token on protected routes

## Type Safety

All files use TypeScript with strict type checking:

```bash
deno check admin    # Type check all files
```

### Type Conventions

- Route components: `PageProps<Data>`
- Island components: `ComponentChildren` from Preact
- API responses: Typed interfaces (e.g., `TableInfo`, `Record<string, unknown>`)
- No `any` types - use `Record<string, unknown>` for dynamic objects

## Code Quality

All code is linted and formatted:

```bash
# Check for issues
deno lint admin

# Format code
deno fmt admin

# Full quality check
make quality
```

### Linting Rules

- No unused variables
- No explicit `any` types
- No deprecated APIs
- Proper error handling
- Type safety enforcement

## WebSocket Events

Real-time updates via WebSocket:

```typescript
// Events from backend
- table:created
- table:updated
- table:deleted
- query:executed
- schema:changed
```

## API Integration

### Authentication API

```typescript
POST /api/auth/login
{
  username: string,
  password: string
}

Response:
{
  access_token: string,
  token_type: "bearer",
  expires_in: number
}
```

### GraphQL API

```typescript
POST /graphql
{
  query: string,
  variables?: Record<string, unknown>
}
```

### REST API

```typescript
GET /api/tables                    # List all tables
GET /api/tables/:table             # Get table schema
GET /api/tables/:table/records     # Get table records
POST /api/tables/:table/records    # Create record
PUT /api/tables/:table/records/:id # Update record
DELETE /api/tables/:table/records/:id # Delete record
```

## Performance

- **Code Splitting:** Routes automatically code-split
- **Lazy Loading:** Islands loaded only when needed
- **Caching:** Browser caching for static assets
- **Compression:** Gzip compression enabled by default
- **Streaming:** Server-side rendering with streaming

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

## Troubleshooting

### Port Already in Use
```bash
# Change port in deno.json or use environment variable
PORT=3001 deno task dev
```

### CORS Issues
Ensure backend has proper CORS headers configured.

### WebSocket Connection Failed
Check that backend WebSocket endpoint is properly configured and accessible.

### JWT Token Expired
Tokens expire based on `JWT_EXPIRATION` setting. User will be redirected to login.

## Contributing

1. Create a feature branch
2. Make changes and test locally
3. Run quality checks: `make quality`
4. Submit pull request

## License

See [LICENSE](../LICENSE) in root directory.

## Related

- [GraphSQL Backend](../README.md) - Main backend API
- [REST API Documentation](../docs/api.rst)
- [GraphQL Schema](../src/graphsql/graphql_schema.py)
