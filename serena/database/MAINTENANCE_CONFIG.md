# Maintenance Configuration

This file explains the `maintenance_config.json` settings for Serena's automatic database maintenance.

## Configuration Sections

### Intervals
Controls how often maintenance operations run:
- `health_check`: Daily database health monitoring
- `checkpoint`: Weekly WAL checkpoint (recommended: 7d)  
- `vacuum`: Monthly database optimization (recommended: 30d)

**Format**: `"1d"` (days), `"24h"` (hours), `"60m"` (minutes), or `{"days": 7, "hours": 2}`

### Enabled
Toggle maintenance operations on/off:
- Set to `false` to disable specific operations
- Useful for debugging or custom maintenance schedules

### Thresholds
Database size and performance warnings:
- `large_db_size_mb`: When to consider database "large" (affects vacuum frequency)
- `large_entry_count`: Entry count threshold for optimization
- `warning_db_size_mb`: Size threshold for warnings
- `critical_db_size_mb`: Size threshold for critical alerts

### Notifications
Control maintenance logging and output:
- `enable_console_output`: Show maintenance messages in console
- `enable_file_logging`: Write maintenance logs to file
- `log_file`: Path to maintenance log file

### Performance
Maintenance operation limits:
- `max_checkpoint_duration_seconds`: Timeout for checkpoint operations
- `max_vacuum_duration_seconds`: Timeout for vacuum operations  
- `auto_optimize_intervals`: Automatically adjust intervals based on usage

### Backup
Database backup settings (optional):
- `enable_pre_vacuum_backup`: Create backup before vacuum operations
- `backup_directory`: Where to store backup files
- `max_backup_files`: Maximum number of backup files to keep

## Default Configuration

The default configuration is optimized for most development workflows:
- **Daily health checks** for early problem detection
- **Weekly checkpoints** for good performance without overhead
- **Monthly vacuum** for optimal space usage
- **Conservative thresholds** that work for teams of any size

## Customization Examples

### High-Volume Project
```json
{
  "intervals": {
    "health_check": "12h",
    "checkpoint": "3d",
    "vacuum": "14d"
  },
  "thresholds": {
    "large_db_size_mb": 2000,
    "large_entry_count": 500000
  }
}
```

### Development/Testing
```json
{
  "intervals": {
    "health_check": "1h",
    "checkpoint": "1d", 
    "vacuum": "7d"
  },
  "backup": {
    "enable_pre_vacuum_backup": true
  }
}
```

### CI/CD Environment
```json
{
  "enabled": {
    "health_check": true,
    "checkpoint": false,
    "vacuum": false
  },
  "notifications": {
    "enable_console_output": false
  }
}
```

## Monitoring

Check maintenance status:
```bash
# View maintenance logs
cat serena/database/maintenance.log

# Check current status
python -m serena.cli health --verbose

# Manual maintenance
python -m serena.scripts.maintenance --status
```