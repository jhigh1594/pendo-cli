# Pendo CLI

Full-featured CLI tool for Pendo's Engage API with complete CRUD capabilities for segments, guides, and analytics.

## Features

- **Segment Management**: Create, list, update, delete segments
- **Visitor Queries**: Query visitors with filters
- **Activity Analytics**: Run aggregation queries
- **Export**: Export data to JSON/CSV

## Quick Start

### Installation

```bash
# Install from source (development mode)
cd ~/jhigh/pendo-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your Pendo credentials:
```bash
PENDO_SUBSCRIPTION_ID=4598576627318784
PENDO_APP_ID=-323232

# For write operations (create/update/delete):
PENDO_API_KEY=your-integration-key-here
```

**Finding your credentials:**
- Subscription ID and App ID: Pendo → Settings → Subscription Settings
- Integration Key: Pendo → Settings → Integration Keys → Create New Key

## Usage

### Segment Management

```bash
# List all segments
python3 -m pendo_cli segment list

# Create a new segment
python3 -m pendo_cli segment create --name "Power Users" --description "High engagement users"

# Update a segment
python3 -m pendo_cli segment update SEGMENT_ID --name "Updated Name"

# Delete a segment
python3 -m pendo_cli segment delete SEGMENT_ID
```

### Query Commands

```bash
# Query visitors
python3 -m pendo_cli query visitors --last-days 30

# Query accounts
python3 -m pendo_cli query accounts --last-days 30

# Query activity
python3 -m pendo_cli query activity --entity visitor --group-by daysActive
```

### Export Commands

```bash
# Export segments to JSON
python3 -m pendo_cli export segments --format json --output segments.json

# Export visitors to CSV
python3 -m pendo_cli export visitors --format csv --output visitors.csv
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=pendo_cli --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run with verbose output
pytest -v tests/
```

### Code Quality

```bash
# Format code
black pendo_cli/

# Lint code
ruff check pendo_cli/

# Type check
mypy pendo_cli/
```

## Architecture

```
pendo_cli/
├── api/                 # Pendo API client
│   ├── client.py        # Async API client with graceful error handling
│   └── models.py        # TypedDict models and config
├── commands/            # CLI command implementations
│   ├── base.py          # BaseCommand abstract class
│   ├── segment.py       # Segment CRUD commands
│   └── query.py         # Query commands
├── collectors/          # Data collectors (future)
│   └── base_collector.py # BaseCollector abstract class
├── utils/               # Utility functions
├── cli.py               # CLI entry point
└── config.py            # Configuration management
```

## API Design

All API methods return a consistent structure:

```python
{
    "data": <response_data>,  # On success: the API response
    "errors": []              # On success: empty list
}

# On error:
{
    "data": None,
    "errors": ["error message"]  # List of error messages
}
```

This enables graceful error handling without exceptions.

## Troubleshooting

### "Authentication failed"
- Check your subscription ID and app ID in `.env`
- Verify your Pendo account has API access enabled

### "Segment not found"
- Verify the segment ID is correct
- Use `segment list` to see all available segments

### "Timeout"
- Network issues or slow API response
- The CLI uses a 30-second timeout by default

### "ModuleNotFoundError"
- Make sure you've installed the package: `pip install -e .`
- Or use: `python3 -m pendo_cli` instead of `pendo`

## Testing Strategy

This project follows **Test-Driven Development (TDD)** principles:

1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to pass the test
3. **REFACTOR**: Clean up the code while keeping tests green

### Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| API Client | 90%+ |
| Commands | 80%+ |
| Collectors | 85%+ |
| Overall | 80%+ |

## Contributing

1. Follow TDD: write tests first
2. Keep functions small and focused
3. Use type hints for all public APIs
4. Add docstrings to all classes and methods
5. Run tests before committing

## License

MIT License - see LICENSE file for details.

## Roadmap

- [ ] Full Pendo MCP integration (aggregation queries)
- [ ] Guide management commands
- [ ] Export command implementation
- [ ] Interactive mode with prompts
- [ ] Shell completion (bash/zsh)
- [ ] Configuration file support (YAML)
