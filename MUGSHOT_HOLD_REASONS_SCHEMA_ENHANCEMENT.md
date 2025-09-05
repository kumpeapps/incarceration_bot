# Mugshot and Hold Reasons Schema Enhancement

## Changes Applied

### 1. Database Schema Updates (`create_clean_schema.py`)
**Mugshot Field**: `TEXT` → `MEDIUMTEXT`
- **Before**: `mugshot TEXT NULL` (max ~65KB)
- **After**: `mugshot MEDIUMTEXT NULL` (max ~16MB)
- **Impact**: 256x larger storage capacity for base64-encoded images

**Hold Reasons Field**: `VARCHAR(1000)` → `TEXT`
- **Before**: `hold_reasons VARCHAR(1000) NOT NULL DEFAULT ''` (max 1KB)
- **After**: `hold_reasons TEXT NOT NULL DEFAULT ''` (max ~65KB)
- **Impact**: 65x larger storage capacity for detailed hold information

### 2. SQLAlchemy Model Updates (`models/Inmate.py`)
**Import Added**:
```python
from sqlalchemy.dialects.mysql import MEDIUMTEXT
```

**Field Definitions Updated**:
```python
# Before
mugshot = Column(Text(65535), nullable=True)
hold_reasons = Column(String(1000), nullable=False, default="")

# After  
mugshot = Column(MEDIUMTEXT, nullable=True)
hold_reasons = Column(Text, nullable=False, default="")
```

### 3. All Schema Variants Updated
- ✅ **Partitioned inmates table**: `inmates_partitioned_sql`
- ✅ **MySQL schema**: Standard inmates table definition
- ✅ **Non-MySQL schema**: Standard inmates table definition

## Storage Capacity Improvements

### Mugshot Field (BASE64 Images)
| Type | Max Size | Typical Image Support |
|------|----------|----------------------|
| **Before**: TEXT | ~65KB | Small thumbnails only |
| **After**: MEDIUMTEXT | ~16MB | High-resolution mugshots |

### Hold Reasons Field (Text Data)
| Type | Max Size | Typical Use Case |
|------|----------|-----------------|
| **Before**: VARCHAR(1000) | 1KB | Brief hold reasons |
| **After**: TEXT | ~65KB | Detailed court orders, multiple charges |

## Benefits

### 1. Enhanced Mugshot Storage
- **High-resolution images**: Support for detailed booking photos
- **Multiple formats**: JPEG, PNG base64 encoding up to 16MB
- **No truncation**: Eliminates image data loss from size limits

### 2. Comprehensive Hold Information
- **Detailed charges**: Full charge descriptions and legal text
- **Court orders**: Complete warrant and hold order information  
- **Multiple agencies**: Space for complex multi-jurisdictional holds

### 3. Database Compatibility
- **MySQL/MariaDB**: Uses native MEDIUMTEXT type for optimal performance
- **Other databases**: Falls back to TEXT type with sufficient capacity
- **Partitioning preserved**: Changes maintain existing performance optimizations

## Migration Impact

### Automatic Schema Updates
- ✅ **New installations**: Use enhanced schema automatically
- ✅ **Existing databases**: Automatic column expansion via `init_db.py`
- ✅ **Data preservation**: Existing data retained during schema updates

### Performance Considerations
- **Storage overhead**: Minimal impact - only uses space when data is stored
- **Query performance**: No impact on SELECT operations
- **Index efficiency**: Maintained with existing optimized indexes

## Deployment Verification

After container restart, verify the changes:

```sql
-- Check column types
DESCRIBE inmates;

-- Verify mugshot capacity (should show MEDIUMTEXT)
SHOW COLUMNS FROM inmates LIKE 'mugshot';

-- Verify hold_reasons capacity (should show TEXT)  
SHOW COLUMNS FROM inmates LIKE 'hold_reasons';
```

Expected results:
- `mugshot`: **mediumtext** | YES | NULL |
- `hold_reasons`: **text** | NO | |

This enhancement significantly improves the system's ability to store comprehensive inmate data while maintaining all existing performance optimizations.
