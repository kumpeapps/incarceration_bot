# Maintenance Commands for Incarceration Bot

The maintenance system is now packaged with the Docker image and provides easy-to-use commands for database operations.

## Available Commands

### 1. Status Check
Get an overview of the database status:
```bash
docker-compose exec incarceration_bot python maintenance.py status
```

### 2. Populate Missing last_seen Values
Fix records that have NULL last_seen dates:
```bash
docker-compose exec incarceration_bot python maintenance.py populate-last-seen
```

### 3. Clean Up Duplicates (Safe Mode)
Remove duplicate records with batch processing (keeps system online):
```bash
docker-compose exec incarceration_bot python maintenance.py cleanup-duplicates
```

### 4. Quick Duplicate Cleanup (Fast Mode)
Remove duplicates with table locking (fastest but blocks database access):
```bash
docker-compose exec incarceration_bot python maintenance.py quick-cleanup
```

## Full Maintenance Mode

For comprehensive maintenance that stops scraping, cleans database, and restarts:
```bash
./run_maintenance.sh
```

This script:
1. Stops scraping services
2. Runs database cleanup
3. Restarts services
4. Verifies everything is working

## Manual Operations

### Check Specific Issues
```bash
# Check for duplicates
docker-compose exec incarceration_bot python -c "
from database_connect import new_session
from sqlalchemy import text
session = new_session()
result = session.execute(text('SELECT COUNT(*) FROM (SELECT name, race, dob, sex, arrest_date, jail_id, COUNT(*) as count FROM inmates GROUP BY name, race, dob, sex, arrest_date, jail_id HAVING COUNT(*) > 1) as duplicates'))
print(f'Duplicate groups: {result.fetchone()[0]}')
session.close()
"

# Check last_seen status
docker-compose exec incarceration_bot python -c "
from database_connect import new_session
from sqlalchemy import text
session = new_session()
result = session.execute(text('SELECT COUNT(*) FROM inmates WHERE last_seen IS NULL'))
print(f'NULL last_seen records: {result.fetchone()[0]}')
session.close()
"
```

## Best Practices

1. **Regular Status Checks**: Run `maintenance.py status` weekly
2. **After Major Changes**: Always run status check after system updates
3. **Backup First**: Consider database backups before major cleanup operations
4. **Monitor Logs**: Check `maintenance_cleanup.log` for detailed operation logs

## Troubleshooting

If maintenance commands fail:
1. Check container logs: `docker-compose logs incarceration_bot`
2. Verify database connection: `docker-compose exec incarceration_bot python -c "from database_connect import new_session; session = new_session(); print('Connected'); session.close()"`
3. Check available space: `docker-compose exec incarceration_bot df -h`
