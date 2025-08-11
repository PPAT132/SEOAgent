# Lighthouse Service

A Node.js microservice that provides SEO analysis using Google Lighthouse for both live websites and raw HTML content.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start the Service

```bash
node server.js
```

The service will start on port 3001.

## 📡 API Endpoints

### POST `/audit`

Analyze a live website URL for SEO.

**Request:**

```json
{
  "url": "https://example.com"
}
```

**Response:**

```json
{
  "seoScore": 92.34,
  "audits": { ... }
}
```

### POST `/audit-html`

Analyze raw HTML content for SEO.

**Request:**

```json
{
  "html": "<!DOCTYPE html><html>...</html>"
}
```

**Response:**

```json
{
  "seoScore": 85.67,
  "audits": { ... },
  "categories": { ... },
  "fullReport": { ... },
  "source": "html_content",
  "tempUrl": "http://localhost:3002/temp-page"
}
```

## 🧪 Testing

### Quick Test

```bash
npm install axios
node quick-test.js
```

### Manual Testing

```bash
# Test URL audit
curl -X POST http://localhost:3001/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Test HTML audit
curl -X POST http://localhost:3001/audit-html \
  -H "Content-Type: application/json" \
  -d '{"html": "<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"}'
```

## 📚 Documentation

See [TESTING.md](./TESTING.md) for comprehensive testing instructions and examples.

## 🔧 Configuration

- **Port**: Set via `PORT` environment variable (default: 3001)
- **Chrome Flags**: Modify in `server.js` for different Chrome behavior
- **Lighthouse Options**: Customize analysis categories and output format

## 🐛 Troubleshooting

- **Port in use**: Kill existing process or change port
- **Chrome launch failed**: Ensure Chrome is installed
- **Analysis timeout**: Increase timeout in client requests

## 📦 Dependencies

- `express`: Web framework
- `lighthouse`: SEO analysis engine
- `chrome-launcher`: Headless Chrome management
