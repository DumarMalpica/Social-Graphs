# Rupestre SPA (Pictograma)

This is a Vite + React + TypeScript SPA for the Pictograma dashboard.

Quick start:

```bash
cd dashboard/spa
npm install
npm run dev
```

To build for production:

```bash
npm run build
# Copy contents of dist to the server static folder or configure server to serve build output
```

The SPA connects to the backend WebSocket at `ws://localhost:3000` by default.
