# ClearSky Text-to-SQL Frontend

React-based frontend for the ClearSky Text-to-SQL application.

## Features

- **Natural Language Chat Interface** - Ask questions in plain English
- **Query Result Visualization** - View results as tables and charts
- **Quick Chart Recommendations** - AI-powered chart suggestions
- **Multiple Chart Types** - Bar, line, pie, scatter, bubble, heatmap, 3D
- **Schema Explorer** - Browse tables and columns
- **Chat History** - View and continue previous sessions

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Plotly.js** - Charting
- **React Router** - Routing
- **Lucide React** - Icons

## Prerequisites

- Node.js 18+
- npm or yarn

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
# Create .env file
echo "VITE_API_BASE_URL=/api" > .env
```

For production, set `VITE_API_BASE_URL` to your backend URL.

3. Start development server:
```bash
npm run dev
```

App will be available at `http://localhost:5173`

## Build

```bash
npm run build
```

Output will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   │   ├── client.ts
│   │   ├── chatApi.ts
│   │   ├── schemaApi.ts
│   │   └── configApi.ts
│   ├── components/       # React components
│   │   ├── common/       # Reusable UI components
│   │   ├── layout/       # Layout components
│   │   ├── chat/         # Chat interface
│   │   ├── charts/       # Plotly visualizations
│   │   ├── schema/       # Schema explorer
│   │   └── history/      # Chat history
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Page components
│   ├── types/            # TypeScript types
│   ├── App.tsx           # Main app with routing
│   ├── main.tsx          # React entry point
│   └── index.css         # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.cjs
└── tsconfig.json
```

## Configuration

The frontend loads feature flags from the backend `/api/config` endpoint at runtime. This includes:

- `enable_advanced_charts` - Enable 3D and advanced chart types
- `enable_streaming` - Enable streaming responses
- `default_max_rows` - Default result limit
- `enable_sql_explanation` - Show SQL explanations

No restart required when backend config changes.

## Development

### Proxy

Vite is configured to proxy `/api` requests to `http://localhost:8000` for local development. Ensure the backend is running.

### Component Development

Components follow a modular structure:
- Each component folder has an `index.ts` barrel export
- Common components are reusable across the app
- Feature components are domain-specific

### Adding New Chart Types

1. Add the type to `types/visualization.ts`
2. Update `ChartRenderer.tsx` with new chart logic
3. Add icon to `ChartSelector.tsx`

## Deployment

### Static Hosting

Build and deploy the `dist` folder to any static hosting (S3, CloudFront, Vercel, Netlify).

### Docker

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Config

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
    }
}
```

## License

MIT License
