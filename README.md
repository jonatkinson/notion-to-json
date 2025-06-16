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
# Export entire workspace (default)
export NOTION_API_KEY="your-integration-token"
notion-to-json

# Using command-line flag
notion-to-json --api-key "your-integration-token"

# Specify output directory
notion-to-json --output-dir ./my-exports

# Export creates:
# - exports/pages/       # Individual page JSON files
# - exports/databases/   # Individual database JSON files  
# - exports/manifest.json # Export summary and metadata

# Test API connection only
notion-to-json --test --api-key "your-integration-token"

# Search and list all pages and databases
notion-to-json --search --api-key "your-integration-token"

# List ALL pages (not just first 10) and databases
notion-to-json --list-all --api-key "your-integration-token"

# Save search results to a JSON file
notion-to-json --search --save-list "notion-content.json" --api-key "your-integration-token"

# Retrieve specific page content
notion-to-json --get-page "page-id-here" --api-key "your-integration-token"

# Save page content to file
notion-to-json --get-page "page-id-here" -o "page-content.json" --api-key "your-integration-token"

# Retrieve specific database content
notion-to-json --get-database "database-id-here" --api-key "your-integration-token"

# Save database content to file  
notion-to-json --get-database "database-id-here" -o "database-content.json" --api-key "your-integration-token"
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
- [x] Phase 2: Notion API client implementation
- [x] Phase 3: Content discovery (pages & databases)
- [x] Phase 4: Full content retrieval
- [x] Phase 5: JSON export functionality
- [ ] Phase 6: CLI enhancements and distribution

## License

MIT