# Development Guide

## Setup

### Prerequisites

- **Python**: 3.10+ (specified in `pyproject.toml`)
- **Docker & Docker Compose**: Required for running tests with PostgreSQL
- **uv**: Dependency management (installed via Docker or locally)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SQLAlchemy-serializer
   ```

2. **Install dependencies with uv**
   ```bash
   uv pip install -e ".[dev]"
   ```

3. **Activate virtual environment** (if using uv's venv)
   ```bash
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

### Docker-based Development

The project uses Docker Compose for consistent test environments:

1. **Build and run tests**
   ```bash
   make test
   ```

2. **Run specific test file**
   ```bash
   make test file=tests/test_flat_model.py
   ```

3. **Run specific test function**
   ```bash
   make test file=tests/test_flat_model.py::test_function_name
   ```

The Docker setup includes:
- Python 3.10.14 Alpine base image
- PostgreSQL database for integration tests
- All development dependencies pre-installed

## Workflow

### Development Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Follow PEP 8 strictly
   - Add type hints to all functions
   - Keep functions small (< 20 lines when feasible)
   - Write tests before or immediately after implementation

3. **Run tests locally**
   ```bash
   make test
   ```

4. **Format and lint code**
   ```bash
   make format  # Runs ruff format and ruff check --fix
   ```

5. **Check linting only (no auto-fix)**
   ```bash
   uv run ruff check .
   ```

6. **Commit changes**
   - Atomic commits with clear messages
   - Keep working directory clean

7. **Push and create PR**
   - Document rationale in PR description
   - Ensure all tests pass
   - Maintain 80%+ code coverage

### Code Review Checklist

- [ ] All tests pass
- [ ] Code coverage maintained (80%+)
- [ ] Type hints added
- [ ] PEP 8 compliance
- [ ] No bare `except:` clauses
- [ ] Logging at appropriate levels
- [ ] Documentation updated if needed
- [ ] No debugging code or temporary variables

## Code Organization

### Project Structure

```
sqlalchemy_serializer/
├── __init__.py              # Public API exports
├── serializer.py            # SerializerMixin, Serializer classes
└── lib/
    ├── __init__.py
    ├── schema.py            # Schema, Tree, Rule classes
    ├── fields.py            # Field extraction utilities
    └── serializable/        # Type-specific serializers
        ├── __init__.py
        ├── base.py          # Base class for serializers
        ├── bytes.py
        ├── date.py
        ├── datetime.py
        ├── decimal.py
        ├── enum.py
        ├── time.py
        └── uuid.py

tests/
├── __init__.py
├── conftest.py             # Pytest fixtures (session, get_instance, get_serializer)
├── models.py              # Test models (FlatModel, NestedModel, RecursiveModel, etc.)
└── test_*.py              # Test files mirroring source structure
```

### Module Responsibilities

**Core Module (`serializer.py`)**
- `SerializerMixin`: User-facing mixin, configuration
- `Serializer`: Serialization engine, type routing
- `serialize_collection`: Helper function for collections

**Schema Module (`lib/schema.py`)**
- `Schema`: Public API for rule management
- `Tree`: Recursive rule storage structure
- `Rule`: Rule parsing and representation

**Fields Module (`lib/fields.py`)**
- Field introspection utilities
- SQLAlchemy mapper attribute discovery
- Property detection

**Serializable Module (`lib/serializable/`)**
- Type-specific serialization logic
- Format handling (datetime, date, time, decimal)
- Base class pattern for extensibility

### Naming Conventions

- **Classes**: PascalCase (`SerializerMixin`, `Schema`)
- **Functions**: snake_case (`get_serializable_keys`, `serialize_collection`)
- **Constants**: UPPER_SNAKE_CASE (`atomic_types`)
- **Private methods**: Leading underscore (not used in this codebase)
- **Test files**: `test_<module_name>.py` or `test_<function_name>_function.py`

### Import Organization

1. Standard library imports
2. Third-party imports (SQLAlchemy, pytz, etc.)
3. Local imports (`sqlalchemy_serializer.*`)

Example:
```python
import logging
from collections import namedtuple
from typing import Optional

from sqlalchemy import inspect

from sqlalchemy_serializer.lib.fields import get_serializable_keys
```

## Testing Strategy

### Test Structure

Tests mirror the source structure:
- `test_serializer.py` → `serializer.py`
- `test_schema.py` → `lib/schema.py`
- `test_fields.py` → `lib/fields.py`
- `test_serializer_serialize_model__function.py` → specific function tests

### Test Configuration

**pytest.ini_options** (in `pyproject.toml`):
- `addopts`: `-xvrs --color=yes` (verbose, extra verbose, print stdout/stderr, color)
- `log_cli`: `true` (show logging output)

**Coverage Configuration**:
- Target: 80% minimum
- Command: `--cov=sqlalchemy_serializer --cov-report term-missing`
- Run via: `make test` (docker-compose)

### Test Fixtures

**Session-scoped fixtures** (`conftest.py`):
- `session`: PostgreSQL database session (created once per test run)
- `get_instance(model, **kwargs)`: Factory for creating test model instances
- `get_serializer(**kwargs)`: Factory for creating Serializer instances

**Usage**:
```python
def test_example(get_instance, get_serializer):
    model = get_instance(FlatModel, string="test")
    serializer = get_serializer()
    result = serializer.serialize_model(model)
    assert result['string'] == "test"
```

### Test Models

Defined in `tests/models.py`:
- **FlatModel**: Simple model with all basic types
- **NestedModel**: Model with relationship to FlatModel
- **RecursiveModel**: Self-referential model for recursion testing
- **CustomSerializerModel**: Model with custom mixin for format testing

### Test Patterns

**Parametrized Tests**:
```python
@pytest.mark.parametrize("input, expected", [
    (("field",), {"field": "value"}),
    (("-field",), {}),
])
def test_serialization(input, expected):
    # Test logic
```

**Integration Tests**:
- Use PostgreSQL via docker-compose
- Test real SQLAlchemy relationships
- Verify database round-trips

**Unit Tests**:
- Test individual functions in isolation
- Mock external dependencies
- Test edge cases and error conditions

### Running Tests

**All tests**:
```bash
make test
```

**Specific test file**:
```bash
make test file=tests/test_flat_model.py
```

**Specific test function**:
```bash
make test file=tests/test_flat_model.py::test_function_name
```

**With coverage**:
```bash
# Coverage is included in make test via docker-compose
docker-compose run tests pytest --cov=sqlalchemy_serializer --cov-report term-missing
```

## Debugging Tips

### Enable Debug Logging

The serializer uses Python's `logging` module. To enable debug output:

```python
import logging

logger = logging.getLogger("serializer")
logger.setLevel(logging.DEBUG)
```

Debug logs show:
- Serialization flow: `"Call serializer for type:..."`
- Field processing: `"Serialize key:... type:... of model:..."`
- Rule processing: `"Checking rule:..."`
- Schema updates: `"Updating tree with rules:..."`
- Skipped fields: `"Skip key:... of model:..."`

### Common Debugging Scenarios

**1. Field not appearing in output**
- Check if field is in `serialize_only` (strict mode)
- Check if field has negative rule (`-field`)
- Verify field exists on model (SQLAlchemy attribute or property)
- Enable debug logging to see field processing

**2. Recursion errors**
- Check for circular relationships (backrefs)
- Add exclusion rules: `serialize_rules = ('-relation.backref',)`
- Verify recursion depth limits

**3. Type serialization issues**
- Check if type is in `serialize_types` chain
- Verify custom serializer signature: `callable(value) -> serialized`
- Check for `IsNotSerializable` exceptions in logs

**4. Schema rule not working**
- Verify rule syntax (dot notation, negative prefix)
- Check greedy vs strict mode (`serialize_only` vs `serialize_rules`)
- Use debug logging to see rule application

**5. Performance issues**
- Check if `get_serializable_keys` cache is working
- Profile with `cProfile` to find bottlenecks
- Verify database queries (N+1 problems in relationships)

### Debugging Tools

**pdb (Python Debugger)**:
```python
import pdb; pdb.set_trace()  # Breakpoint
```

**ipdb** (if installed):
```python
import ipdb; ipdb.set_trace()  # Better REPL
```

**Print debugging**:
```python
logger.debug("Value: %s, Type: %s", value, type(value))
```

**Schema inspection**:
```python
serializer = Serializer()
serializer.schema.update(only=..., extend=...)
print(serializer.schema._tree)  # Inspect rule tree
```

## Common Tasks

### Adding a New Type Serializer

1. **Create serializer class** in `lib/serializable/`:
   ```python
   # lib/serializable/custom_type.py
   from .base import Base
   
   class CustomType(Base):
       def __call__(self, value):
           return str(value)  # Serialization logic
   ```

2. **Export in `__init__.py`**:
   ```python
   from .custom_type import CustomType
   __all__ = [..., "CustomType"]
   ```

3. **Add to `serialize_types` chain** in `Serializer.init_callbacks()`:
   ```python
   self.serialize_types = (
       ...,
       (CustomType, serializable.CustomType()),
   )
   ```

4. **Write tests** in `tests/test_custom_type.py`

5. **Update documentation** (README.md, ARCHITECTURE.md)

### Modifying Schema Rules

**Adding new rule syntax**:
1. Modify `Rule.__init__()` in `lib/schema.py`
2. Update `Schema.apply()` for rule processing
3. Add tests in `tests/test_schema.py`
4. Document in README.md

**Changing greedy/strict behavior**:
1. Modify `Tree.apply()` and `Tree.to_strict()`
2. Update `Schema.is_included()`
3. Add comprehensive tests

### Optimizing Performance

**Field introspection caching**:
- Already implemented with `@functools.lru_cache` on `get_serializable_keys()`
- Cache key is model instance (works because field names don't change)

**Schema optimization**:
- TODO: Skip `is_included()` checks when not greedy (see code comments)
- Consider caching schema lookups for repeated serialization

**Type checking optimization**:
- Current: `isinstance(value, types)` with tuple of types
- Already efficient for multiple inheritance cases

### Updating Dependencies

1. **Update version in `pyproject.toml`**
2. **Update dependencies**:
   ```bash
   uv pip install -e ".[dev]" --upgrade
   ```
3. **Test compatibility**:
   ```bash
   make test
   ```
4. **Check for breaking changes** in dependency changelogs

### Adding New Test Models

1. **Define model** in `tests/models.py`:
   ```python
   class NewTestModel(Base, SerializerMixin):
       __tablename__ = "new_test_model"
       id = sa.Column(sa.Integer, primary_key=True)
       # ... fields
   ```

2. **Use in tests**:
   ```python
   def test_new_model(get_instance):
       model = get_instance(NewTestModel, ...)
       result = model.to_dict()
       assert ...
   ```

## Release Process

### Version Bumping

Version is specified in `pyproject.toml`:
```toml
[project]
version = "1.4.22"
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Pre-Release Checklist

- [ ] All tests pass (`make test`)
- [ ] Code coverage ≥ 80%
- [ ] No linting errors (`uv run ruff check .`)
- [ ] Code formatted (`make format`)
- [ ] Documentation updated (README.md, ARCHITECTURE.md, DEVELOPMENT.md, KNOWLEDGE.md)
- [ ] CHANGELOG updated (if maintained)
- [ ] Version bumped in `pyproject.toml`
- [ ] Dependencies reviewed and updated if needed

### Release Steps

1. **Update version** in `pyproject.toml`

2. **Create release commit**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to X.Y.Z"
   git tag vX.Y.Z
   ```

3. **Build package**:
   ```bash
   uv build
   ```

4. **Publish to PyPI** (if maintainer):
   ```bash
   uv publish
   ```

5. **Push to repository**:
   ```bash
   git push origin master
   git push origin vX.Y.Z
   ```

6. **Create GitHub release** (if using GitHub):
   - Tag: `vX.Y.Z`
   - Title: `Version X.Y.Z`
   - Description: Changelog entries

### Post-Release

- [ ] Verify package installs: `pip install SQLAlchemy-serializer==X.Y.Z`
- [ ] Test in clean environment
- [ ] Monitor for issues/feedback
- [ ] Update documentation if needed
