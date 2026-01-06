# Production image for GraphSQL Admin (Fresh + Deno)

FROM denoland/deno:1.43.6 as base
WORKDIR /app

# Cache deps
COPY deno.json ./
RUN deno cache deno.json

# Copy source
COPY . .

# Build the Fresh app (produces .fresh/)
RUN deno task build

# --- Runtime ---
FROM denoland/deno:1.43.6
WORKDIR /app
ENV DENO_ENV=production \
    PORT=8001 \
    GRAPHSQL_URL=http://graphsql:8000

# Copy built artifacts only
COPY --from=base /app /app

# Expose admin port
EXPOSE 8001

# Run in production mode (no watch)
CMD ["deno", "run", "-A", "main.ts", "--port", "8001"]
