# Notion to JSON Exporter

Export your entire Notion workspace to JSON format with a simple command-line tool.

## Features

- Export all pages and databases from your Notion workspace
- Systematic traversal of nested content
- Progress tracking with rich terminal UI
- JSON format preserving Notion structure
- Secure API key handling via CLI or environment variables
- Rate-limited API calls to respect Notion's limits

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/notion-to-json.git
cd notion-to-json

# Install dependencies
uv sync
```

### Using uvx (direct execution)

```bash
uvx notion-to-json --api-key YOUR_API_KEY
```

## Usage

### Basic usage

```bash
# Using environment variable
export NOTION_API_KEY="your-integration-token"
notion-to-json

# Using command-line flag
notion-to-json --api-key "your-integration-token"

# Specify output directory
notion-to-json --output-dir ./my-exports
```

### Getting a Notion API Key

1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the "Internal Integration Token"
4. Share your Notion pages/databases with the integration

## Development

### Setup

```bash
# Install development dependencies
make install

# Run linting
make lint

# Format code
make format

# Run tests
make test

# Run all checks
make dev
```

### Project Structure

```
notion-to-json/
├── src/
│   └── notion_to_json/
│       ├── cli.py          # CLI interface
│       ├── client.py       # Notion API client
│       ├── models.py       # Data models
│       └── exporter.py     # JSON export logic
└── tests/                  # Test suite
```

## Roadmap

- [x] Phase 1: Project setup and structure
- [ ] Phase 2: Notion API client implementation
- [ ] Phase 3: Content discovery (pages & databases)
- [ ] Phase 4: Full content retrieval
- [ ] Phase 5: JSON export functionality
- [ ] Phase 6: CLI enhancements and distribution

## License

MIT