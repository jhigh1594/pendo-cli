# Pendo CLI

Full-featured CLI tool for Pendo's Engage API with complete CRUD capabilities for segments, guides, and analytics.

## Features

- **Segment Management**: Create, list, update, delete segments
- **Usage Analytics**: DAU/WAU/MAU, feature usage, page usage (for product analytics)
- **Cohort Exports**: Export visitors and accounts with metadata for AI/BI analysis
- **Track Event Counts**: Query custom events (e.g. cards created) with date ranges
- **Multiple Subscriptions**: default (AgilePlace), roadmaps, portfolios, viz

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
PENDO_API_KEY=your-integration-key-here

# Optional: Multi-subscription (roadmaps, portfolios, viz)
# See .env.example for PENDO_ROADMAPS_*, PENDO_PORTFOLIOS_*, PENDO_VIZ_*
```

Use `--subscription roadmaps` (or `portfolios`, `viz`) on query commands to target a different app.

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

#### Usage Analytics (for Sr PMs)

```bash
# Active users: WAU (default), DAU, MAU, or custom window
python3 -m pendo_cli query usage --mode wau
python3 -m pendo_cli query usage --mode mau --format json
python3 -m pendo_cli query usage --mode custom --last-days 14 --group-by account

# Feature usage: top features by events and time
python3 -m pendo_cli query features --top 10 --format csv
python3 -m pendo_cli query features --feature-id FEATURE_ID --format json

# Page usage: top pages by events
python3 -m pendo_cli query pages --top 20 --last-days 30
```

#### Cohort and Segment Exports

```bash
# Export visitors with metadata (for AI assistants or BI)
python3 -m pendo_cli query visitors --format csv
python3 -m pendo_cli query visitors --new-last-days 7 --format json   # New signups last 7 days
python3 -m pendo_cli query visitors --inactive-days 14 --format csv  # No activity in 14 days

# Export accounts with ARR, plan, CSM
python3 -m pendo_cli query accounts --format csv
python3 -m pendo_cli query accounts --new-last-days 30 --format json
```

#### Track Events and WAU

```bash
# WAU (or N-day active users)
python3 -m pendo_cli query wau --last-days 7
python3 -m pendo_cli query wau --from-date 2025-01-01 --to-date 2025-01-31 --subscription default

# Custom track event counts
python3 -m pendo_cli query events --event-name "core-card-service POST /io/card" --from-date 2025-01-01 --to-date 2025-12-31
```

#### Output Formats

All query commands support `--format table|json|csv`:
- `table` (default): Human-readable aligned columns
- `json`: Machine-friendly for pipelines or AI tools
- `csv`: For spreadsheets or data analysis

#### Using with AI Assistants

Pipe JSON output for analysis:
```bash
python3 -m pendo_cli query visitors --format json | head -c 50000  # First 50KB for context
python3 -m pendo_cli query usage --mode mau --format json
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

- [x] Aggregation queries (usage, features, pages, visitors, accounts)
- [ ] Guide management commands
- [ ] Export command implementation
- [ ] Interactive mode with prompts
- [ ] Shell completion (bash/zsh)
- [ ] Configuration file support (YAML)
