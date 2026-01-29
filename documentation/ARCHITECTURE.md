# Architecture & Code Organization

This document describes the improved codebase structure and architecture decisions.

## Overview

The codebase has been reorganized to:
- Eliminate code duplication
- Improve maintainability
- Enable type safety
- Support evaluation and agentic workflows

## Directory Structure

```
├── src/                    # Core shared modules
│   ├── config.py          # Constants, county mappings, settings
│   └── utils.py           # Shared utilities (CSV writer, etc.)
├── schemas/                # Pydantic schemas for type safety
├── agents/                 # Agentic system components
├── eval/                   # Evaluation framework
├── data/                   # Pipeline outputs
└── [scripts]               # Entry point scripts
```

## Key Improvements

### 1. Centralized Configuration (`src/config.py`)

**Before**: Constants duplicated across multiple files
- `CALIFORNIA_COUNTIES` in both `scraper.py` and `scraper_discovery.py`
- `STATE_NAME` scattered
- Settings duplicated

**After**: Single source of truth
- All constants in `src/config.py`
- Imported by all scripts
- Easy to update

### 2. Shared Utilities (`src/utils.py`)

**Before**: `save_to_csv()` only in `scraper.py`, imported by others

**After**: 
- Utilities in `src/utils.py`
- Reusable across all scripts
- Clear separation of concerns

### 3. Type Safety (`schemas/`)

**Before**: Dict-based data structures, no validation

**After**:
- Pydantic schemas for all phases
- Runtime validation
- IDE autocomplete
- Catch errors early

### 4. Evaluation Framework (`eval/`)

**Before**: No metrics tracking

**After**:
- Gold dataset support
- Comprehensive metrics (Recall@K, precision/recall, schema validity)
- Regression testing capability
- Run versioning

### 5. Agentic System (`agents/`)

**Before**: Heuristic-based discovery

**After**:
- Tools-based agentic discovery
- State management
- Failure handling
- Confidence tracking

## Module Dependencies

```
scripts (entry points)
    ↓
src/ (core modules)
    ├── config.py (constants)
    └── utils.py (utilities)
    ↓
schemas/ (type safety)
    ↓
agents/ (agentic workflows)
    ↓
eval/ (evaluation)
```

## Import Patterns

### Scripts Import from Core
```python
from src.config import STATE_NAME, CALIFORNIA_COUNTIES
from src.utils import save_to_csv
```

### Schemas Used for Validation
```python
from schemas.discovery import DiscoveryResult
from schemas.structured import StructuredCounty
```

### Agents Use Schemas
```python
from schemas.discovery import ProgramLink
```

## Benefits

1. **Maintainability**: Single source of truth for constants
2. **Type Safety**: Pydantic validation catches errors early
3. **Testability**: Clear module boundaries enable unit testing
4. **Extensibility**: Easy to add new features (agents, eval)
5. **Documentation**: Clear structure self-documents the codebase

## Migration Notes

- Scripts remain at root level for easy execution
- All scripts now import from `src/` for shared code
- Legacy `scraper.py` still works but uses new structure
- No breaking changes to existing workflows

## Future Improvements

- [ ] Add unit tests for `src/` modules
- [ ] Add integration tests for pipeline
- [ ] Add CI/CD with evaluation regression tests
- [ ] Add more agentic tools (search, verification)
- [ ] Expand gold dataset coverage

