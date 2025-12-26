# Project Knowledge Base

## Overview

This file contains accumulated knowledge about the SQLAlchemy-serializer project, including key concepts, edge cases, common patterns, and troubleshooting information.

## Key Concepts

### Serialization Modes

The library operates in two distinct modes:

**1. Greedy Mode (Default)**
- Includes all SQLAlchemy fields by default
- Excludes fields only if explicitly marked with negative rules (`-field`)
- Activated when `serialize_only` is empty/not set
- Use `serialize_rules` to add/remove fields

**2. Strict Mode**
- Includes only fields explicitly specified
- Activated when `serialize_only` is provided
- More secure (prevents accidental field exposure)
- Use `serialize_only` to define exact field list

**Switching modes**:
```python
# Greedy mode (default)
model.to_dict()  # All fields

# Strict mode
model.to_dict(only=('id', 'name'))  # Only id and name
```

### Rule System

Rules control which fields are included/excluded in serialization.

**Rule Types**:
- **Positive rules**: Include field (`'field'`, `'relation.field'`)
- **Negative rules**: Exclude field (`'-field'`, `'-relation.field'`)

**Rule Syntax**:
- Dot notation for nested fields: `'relation.field.nested'`
- Negative prefix: `-` at the start
- Multiple rules: Pass as tuple `('field1', '-field2', 'relation.field3')`

**Rule Priority**:
- `serialize_only` (strict mode) has highest priority
- `serialize_rules` (greedy mode) extends default schema
- Negative rules in `serialize_only` require parent to be included first

### Forking Mechanism

When serializing nested structures (dicts, lists, models), the serializer creates a **fork** - a new Serializer instance with its own schema context.

**Why forking?**
- Isolation: Nested rules don't affect parent context
- Depth tracking: Prevents infinite recursion
- Schema inheritance: Nested rules work independently

**Forking occurs for**:
- Dictionary values
- Iterable items
- Related model instances

**Example**:
```python
# Parent serializer has rules: ('-id',)
# When serializing nested model, fork gets its own schema
# Nested model's serialize_only/rules are applied in fork context
```

### Type Serialization Chain

Types are checked in a specific order (first match wins):

1. Custom types (from `serialize_types`)
2. Atomic types (int, str, float, bool, None) - pass through
3. bytes → Base64 encoding
4. uuid.UUID → String representation
5. time → Formatted string (checked before datetime)
6. datetime → Formatted string with timezone support
7. date → Formatted string
8. Decimal → Formatted string (Python format syntax)
9. dict → Recursive serialization (checked before Iterable)
10. Iterable → List serialization
11. Enum → `.value` attribute
12. SerializerMixin → Model serialization

**Important**: Order matters! `time` must be checked before `datetime` because `datetime` is also an instance of `time`.

### Field Discovery

The library discovers serializable fields through:

1. **Explicit list**: `serializable_keys` attribute (highest priority)
2. **SQLAlchemy introspection**: Uses `sqlalchemy.inspect()` to get mapper attributes
3. **Property detection**: If `auto_serialize_properties=True`, includes `@property` fields

**Caching**: `get_serializable_keys()` uses `@functools.lru_cache` for performance.

## Serialization Rules

### Basic Rules

**Include field**:
```python
model.to_dict(rules=('field',))
```

**Exclude field**:
```python
model.to_dict(rules=('-field',))
```

**Nested field**:
```python
model.to_dict(rules=('relation.field',))
```

**Exclude nested field**:
```python
model.to_dict(rules=('-relation.field',))
```

### Strict Mode Rules

**Only specific fields**:
```python
model.to_dict(only=('id', 'name', 'relation.id'))
```

**Negative rules in strict mode**:
```python
# Include relation but exclude relation.id
model.to_dict(only=('relation', '-relation.id'))
```

**Important**: `only=('-field',)` returns nothing! Must include parent first.

### Model-Level Rules

Define rules on the model class:

```python
class MyModel(Base, SerializerMixin):
    serialize_only = ('id', 'name')  # Strict mode
    serialize_rules = ('-password',)  # Greedy mode, exclude password
```

**Priority**:
1. `to_dict(only=...)` argument (highest)
2. `to_dict(rules=...)` argument
3. Model's `serialize_only` attribute
4. Model's `serialize_rules` attribute
5. Default (greedy, all fields)

### Controversial Rules

When conflicting rules exist, behavior depends on mode:

**Greedy mode**:
```python
serialize_rules = ('-prop', 'prop.id')
# Result: prop is included (positive rule wins)
```

**Strict mode**:
```python
serialize_only = ('prop', '-prop.id')
# Result: prop included, prop.id excluded
```

**Rule**: Positive rules generally override negative rules when both apply to the same field.

### Recursive Models

For self-referential models, prevent infinite recursion:

```python
class User(Base, SerializerMixin):
    serialize_rules = ('-related_models.user',)  # Break cycle
    related_models = relationship("RelatedModel", backref='user')
```

**Common patterns**:
- Exclude backref: `'-relation.backref'`
- Limit depth: `'-children.children'` (only first level)
- Break specific cycle: `'-relation.relation'`

## Common Use Cases

### Basic Serialization

```python
# Simple model
class Product(Base, SerializerMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Numeric)

product = Product.query.first()
result = product.to_dict()
# {'id': 1, 'name': 'Widget', 'price': Decimal('19.99')}
```

### Excluding Sensitive Fields

```python
class User(Base, SerializerMixin):
    serialize_rules = ('-password', '-api_key')  # Always exclude
    
    id = Column(Integer, primary_key=True)
    email = Column(String)
    password = Column(String)  # Never serialized
    api_key = Column(String)   # Never serialized
```

### Including Computed Properties

```python
class Order(Base, SerializerMixin):
    auto_serialize_properties = True  # Include @property fields
    
    @property
    def total(self):
        return sum(item.price for item in self.items)
    
    items = relationship("OrderItem")

order.to_dict()  # Includes 'total' property
```

### Nested Relationships

```python
# Include only specific nested fields
order.to_dict(only=('id', 'customer.name', 'items.id', 'items.quantity'))

# Exclude nested fields
order.to_dict(rules=('-customer.email', '-items.price'))
```

### Custom Formats

```python
class Event(Base, SerializerMixin):
    date_format = '%s'  # Unix timestamp
    datetime_format = '%Y-%m-%dT%H:%M:%S'
    
    date = Column(Date)
    datetime = Column(DateTime)

event.to_dict()  # Uses custom formats
```

### Timezone Conversion

```python
# Per-call
event.to_dict(tzinfo=pytz.timezone('America/New_York'))

# Per-model
class Event(Base, SerializerMixin):
    def get_tzinfo(self):
        return pytz.timezone(get_current_user().timezone)
```

### Serializing Collections

```python
from sqlalchemy_serializer import serialize_collection

products = Product.query.all()
result = serialize_collection(products, only=('id', 'name'))
# [{'id': 1, 'name': 'Widget'}, {'id': 2, 'name': 'Gadget'}]
```

### Custom Type Serialization

```python
class GeoModel(Base, SerializerMixin):
    serialize_types = (
        (WKBElement, lambda x: to_shape(x).to_wkt()),
    )
    
    position = Column(Geometry('POINT'))
```

## Performance Considerations

### Field Introspection Caching

The library caches field names using `@functools.lru_cache`:
- Cache key: model instance
- Benefit: SQLAlchemy inspection is relatively expensive
- Trade-off: Field names must not change at runtime

**Impact**: Significant performance improvement for repeated serialization of same model type.

### Type Checking

**Current implementation**: `isinstance(value, types)` with tuple of types.

**Efficiency**: Already optimized - Python's `isinstance()` with tuple is efficient for multiple inheritance.

### Database Queries

**N+1 Problem**: Serializing relationships can trigger multiple queries.

**Mitigation**:
- Use SQLAlchemy eager loading: `query.options(joinedload(Model.relation))`
- Consider serialization depth limits
- Use `serialize_only` to limit nested serialization

### Large Collections

**Iterable serialization**: Each item is serialized individually.

**Considerations**:
- Large lists may be slow
- Consider pagination or limiting results
- Use `serialize_only` to reduce per-item processing

## Integration Patterns

### Flask/SQLAlchemy

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin

app = Flask(__name__)
db = SQLAlchemy(app)

class User(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

@app.route('/users')
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])
```

### FastAPI

```python
from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy_serializer import SerializerMixin, serialize_collection

app = FastAPI()

class Product(Base, SerializerMixin):
    # ... model definition

@app.get("/products")
def get_products(db: Session):
    products = db.query(Product).all()
    return serialize_collection(products, only=('id', 'name', 'price'))
```

### Custom Base Class

```python
from sqlalchemy_serializer import SerializerMixin

class BaseSerializerMixin(SerializerMixin):
    # Shared configuration
    date_format = '%Y-%m-%d'
    datetime_format = '%Y-%m-%d %H:%M:%S'
    auto_serialize_properties = True
    
    def get_tzinfo(self):
        # Shared timezone logic
        return pytz.UTC

class MyModel(Base, BaseSerializerMixin):
    # Inherits serialization configuration
    pass
```

### API Response Wrapper

```python
def api_response(data, status_code=200):
    """Wrap serialized data in standard API response"""
    if isinstance(data, list):
        serialized = serialize_collection(data)
    elif hasattr(data, 'to_dict'):
        serialized = data.to_dict()
    else:
        serialized = data
    
    return {
        'status': 'success',
        'data': serialized
    }, status_code
```

## Troubleshooting Guide

### Maximum Recursion Depth Exceeded

**Symptom**: `RecursionError: maximum recursion depth exceeded`

**Cause**: Circular relationship (often with backrefs)

**Solution**:
```python
class User(Base, SerializerMixin):
    serialize_rules = ('-related_models.user',)  # Break cycle
    related_models = relationship("RelatedModel", backref='user')
```

**Prevention**: Always exclude backrefs in recursive models.

### Field Not Appearing in Output

**Possible causes**:
1. Field excluded by negative rule
2. Strict mode (`serialize_only`) doesn't include field
3. Field not a SQLAlchemy attribute or property
4. Field name typo

**Debugging**:
```python
import logging
logging.getLogger("serializer").setLevel(logging.DEBUG)

# Check field discovery
from sqlalchemy_serializer.lib.fields import get_serializable_keys
print(get_serializable_keys(model))  # See discovered fields

# Check schema
serializer = Serializer()
serializer.schema.update(only=..., extend=...)
print(serializer.schema.is_included('field_name'))
```

### Type Not Serializable

**Symptom**: `IsNotSerializable: Unserializable type:...`

**Cause**: Type not in serialization chain

**Solution**:
```python
class MyModel(Base, SerializerMixin):
    serialize_types = (
        (CustomType, lambda x: str(x)),
    )
```

### Negative Rule in `serialize_only` Returns Nothing

**Symptom**: `serialize_only = ('-field',)` returns empty dict

**Cause**: Strict mode requires parent to be included first

**Solution**:
```python
# Wrong
serialize_only = ('-model.id',)  # Returns nothing

# Correct
serialize_only = ('model', '-model.id')  # Includes model without id
```

### One-Element Tuple Syntax Error

**Symptom**: Rules not working as expected

**Cause**: Missing comma in one-element tuple

**Solution**:
```python
# Wrong
serialize_only = ('field')  # Not a tuple!

# Correct
serialize_only = ('field',)  # Tuple with one element
```

### Controversial Rules Behavior

**Symptom**: Field included despite negative rule

**Cause**: Conflicting positive and negative rules

**Behavior**:
- Greedy mode: Positive rule wins (`'-field', 'field'` → field included)
- Strict mode: Both rules apply (`'field', '-field.id'` → field included, id excluded)

**Solution**: Remove conflicting rules or use strict mode for explicit control.

### Custom Serializer Can't Access Formats

**Symptom**: Custom serializer needs format/tzinfo but can't access it

**Cause**: By design - custom serializers are isolated

**Workaround**: Pass format as closure:
```python
def make_serializer(format_str):
    return lambda x: format_str.format(x)

class MyModel(Base, SerializerMixin):
    serialize_types = (
        (CustomType, make_serializer(self.custom_format)),
    )
```

**Note**: This is a documented limitation. May be implemented in future.

## API Decisions

### Why Mixin Instead of Base Class?

**Decision**: Use mixin pattern for `SerializerMixin`

**Rationale**:
- Models may already inherit from custom base classes
- Mixin allows composition without inheritance conflicts
- Easy to add/remove serialization capability
- Follows SQLAlchemy's own patterns

### Why Callback Chain Instead of Registry?

**Decision**: Ordered tuple of (Type, callable) pairs

**Rationale**:
- Simple, explicit ordering
- Easy to override (prepend custom types)
- Supports multiple inheritance (tuple of types)
- No global state or registration step

### Why Fork Instead of Shared Context?

**Decision**: Create new Serializer instances for nested structures

**Rationale**:
- Isolation: Nested rules don't pollute parent
- Depth tracking: Prevents infinite recursion
- Schema inheritance: Nested rules work correctly
- Clear separation of concerns

### Why Tree-Based Schema?

**Decision**: Recursive defaultdict structure for rules

**Rationale**:
- Efficient nested rule matching
- Supports dot-notation paths naturally
- Greedy/strict mode propagation
- Easy to merge rules from multiple sources

### Why Greedy by Default?

**Decision**: Default to including all fields

**Rationale**:
- Convenient: Works out of the box
- Minimal configuration for common cases
- Easy to exclude sensitive fields with negative rules
- Can switch to strict mode when needed

### Why LRU Cache for Field Introspection?

**Decision**: Cache `get_serializable_keys()` results

**Rationale**:
- SQLAlchemy inspection is relatively expensive
- Field names don't change at runtime
- Significant performance improvement
- Minimal memory overhead

### Why Options Pattern (namedtuple)?

**Decision**: Use `namedtuple` for serialization options

**Rationale**:
- Immutable configuration
- Easy to pass between Serializer instances
- Clear, explicit parameter list
- Lightweight (no class overhead)

### Why No Access to Formats in Custom Serializers?

**Decision**: Custom serializers cannot access format/tzinfo options

**Rationale**:
- Simplicity: Serializers are just callables
- Isolation: No coupling to Serializer internals
- Flexibility: Can pass format via closure if needed

**Trade-off**: Less convenient for some use cases (documented limitation)
