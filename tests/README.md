# Integration Tests

This directory contains integration tests for the iTREDS healthcare data scraper pipeline.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_phase1_discovery.py # Phase 1 (Discovery) tests
├── test_phase2_extraction.py # Phase 2 (Extraction) tests
├── test_phase3_structuring.py # Phase 3 (Structuring) tests
├── test_pipeline_integration.py # End-to-end pipeline tests
├── test_schemas.py          # Pydantic schema validation tests
└── README.md               # This file
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_phase1_discovery.py
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run Verbose
```bash
pytest tests/ -v
```

## Test Categories

### Phase 1 Tests (`test_phase1_discovery.py`)
- Discovery result schema validation
- Health department finding
- Maternal section finding
- Program link collection
- Full discovery workflow

### Phase 2 Tests (`test_phase2_extraction.py`)
- Raw page schema validation
- Contact extraction (phones, emails)
- PDF link extraction
- Program page processing
- Pattern matching for various formats

### Phase 3 Tests (`test_phase3_structuring.py`)
- Structured program schema validation
- Prompt building
- OpenAI extraction (mocked)
- Discovery loading
- Critical fields missing rate calculation

### Integration Tests (`test_pipeline_integration.py`)
- Full pipeline flow
- Phase 1 → Phase 2 → Phase 3 integration
- CSV output format validation
- End-to-end workflow

### Schema Tests (`test_schemas.py`)
- Pydantic schema validation
- Required fields
- Type checking
- Validation error handling

## Test Fixtures

Shared fixtures in `conftest.py`:
- `temp_data_dir` - Temporary directory for test data
- `sample_county_name` - Sample county name
- `sample_county_url` - Sample county URL
- `sample_discovery_result` - Sample Phase 1 output
- `sample_raw_page` - Sample Phase 2 output
- `sample_structured_program` - Sample Phase 3 output
- `mock_html_content` - Mock HTML for scraping tests
- `mock_openai_response` - Mock OpenAI API response

## Mocking Strategy

Tests use mocking to avoid:
- Actual web scraping (network calls)
- Real API calls (OpenAI/Anthropic)
- File system operations (use temp directories)

This makes tests:
- Fast (no network delays)
- Reliable (no external dependencies)
- Isolated (no side effects)

## Continuous Integration

These tests are designed to run in CI/CD:
- No external dependencies required
- All network calls mocked
- Deterministic results
- Fast execution

## Adding New Tests

When adding new functionality:
1. Add unit tests for individual functions
2. Add integration tests for phase workflows
3. Update fixtures if new test data needed
4. Ensure all tests pass before committing

## Test Coverage Goals

- **Phase 1**: 80%+ coverage
- **Phase 2**: 80%+ coverage
- **Phase 3**: 70%+ coverage (LLM calls mocked)
- **Schemas**: 100% coverage
- **Integration**: All major workflows covered
