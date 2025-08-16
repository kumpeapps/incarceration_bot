## URGENT: MariaDB Binlog Optimization Required

### Problem
- **20GB+ MariaDB binlog growth in a few hours**
- Caused by excessive `last_seen` timestamp updates on every scrape
- Every existing inmate record updated unnecessarily 

### Root Cause
`backend/helpers/insert_ignore.py` line 51:
```sql
ON DUPLICATE KEY UPDATE
    last_seen = VALUES(last_seen),  -- ALWAYS updates timestamp
```

### Immediate Fix Applied
**File: `backend/helpers/insert_ignore.py`**

✅ **OPTIMIZED**: Only update `last_seen` if more than 1 hour old:
```sql
ON DUPLICATE KEY UPDATE
    last_seen = CASE 
        WHEN last_seen IS NULL OR last_seen < DATE_SUB(NOW(), INTERVAL 1 HOUR)
        THEN VALUES(last_seen)
        ELSE last_seen  -- Skip update if recent
    END,
```

### Deploy Fix
1. **Rebuild container** with `--no-cache`:
   ```bash
   docker-compose build --no-cache backend_api
   docker-compose restart backend_api
   ```

2. **Monitor results**:
   ```bash
   # Check binlog size before/after
   docker-compose exec backend_api mysql -e "SHOW BINARY LOGS;"
   ```

### Expected Results
- **90%+ reduction** in binlog growth
- Same functionality, dramatically fewer database writes
- Only updates timestamps when significantly different (>1 hour)

### Verification
After next scrape run, binlog growth should be **dramatically reduced** from 20GB/few hours to normal levels.

---

**Additional optimizations available in `BINLOG_OPTIMIZATION.md` for further improvements.**
