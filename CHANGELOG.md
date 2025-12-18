# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.4] - 2025-12-17

### Added
- Custom serialization for specific columns via `serialize_columns` parameter
  - Supports per-call customization: `to_dict(serialize_columns={'field': lambda v: ...})`
  - Supports model-level defaults: `serialize_columns = {'field': lambda v: ...}` class attribute
  - Custom serializers receive the field value and return the serialized result

## [1.5.3] - 2025-12-16

### Added
- `max_serialization_depth` parameter to control relationship recursion depth
  - Per-call usage: `to_dict(max_serialization_depth=1)`
  - Model-level default: `max_serialization_depth = 1` class attribute
  - Defaults to unlimited (`math.inf`) for backward compatibility
  - Prevents infinite recursion in models with circular relationships

## [1.5.2] - 2025-12-13

### Added
- `exclude_values` parameter to filter out specific values from serialized output
  - Supports per-call usage: `to_dict(exclude_values=(None,))`
  - Supports model-level defaults: `exclude_values = (None,)` class attribute
  - Works with nested dictionaries and models
  - Only supports hashable values

## [1.5.0] - 2025-12-13

### Added
- Enhanced rules and documentation
- Additional test coverage
- UV package manager support
- GitHub Actions workflow improvements with coverage reporting
- PyPI readiness tests and make commands

### Changed
- Updated GitHub Actions workflow to use `uv` for dependency installation and linting
- Improved test infrastructure and fixtures

## [1.4.22] - 2024-07-03

### Fixed
- Various bug fixes and improvements from earlier versions

---

## Unreleased

### Added
- (Future features will be listed here)

### Changed
- (Future changes will be listed here)

### Fixed
- (Future fixes will be listed here)

### Removed
- (Future removals will be listed here)

