# Database Backup & Restore - Quick Reference

This is a quick reference guide for common backup and restore operations. For detailed documentation, see [Database Backup & Restore Runbook](admin_db.md).

---

## 🚀 Quick Start

### Manual Backup
```bash
# Create a backup
make db-backup

# Create backup with custom label
LABEL=pre-deployment make db-backup

# Create backup to custom directory
BACKUP_DIR=/var/backups make db-backup
```

### Manual Restore
```bash
# Restore from backup (non-production)
FILE=backups/scheduled-20250621020000.sql.gz make db-restore

# Restore to production (requires --force)
ENV=production FILE=backups/scheduled-20250621020000.sql.gz make db-restore
```

### API Operations
```bash
# Trigger backup via API
curl -X POST http://localhost:8000/admin/db/backup \
  -H "Authorization: Bearer <admin-jwt-token>"

# Upload and restore backup via API
curl -X POST http://localhost:8000/admin/db/restore \
  -H "Authorization: Bearer <admin-jwt-token>" \
  -F "file=@backups/scheduled-20250621020000.sql.gz"
```

---

## 📊 Monitoring

### Check Backup Status
```bash
# List recent backups
ls -la backups/

# Check backup integrity
sha256sum backups/scheduled-*.sql.gz

# View backup logs
grep "backup" /var/log/app/app.log | tail -20
```

### Monitor Metrics
```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics | grep db_backup

# View audit events
grep '"action":"db_backup"' /var/log/app/audit.log | jq .
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Backup directory
BACKUP_DIR=backups

# Retention period (days)
BACKUP_RETENTION_DAYS=7

# Schedule (cron format)
BACKUP_SCHEDULE_CRON="0 2 * * *"

# PostgreSQL tools path
BACKUP_PGDUMP_PATH=pg_dump
BACKUP_PGRESTORE_PATH=pg_restore
```

### Optional Features
```bash
# Enable S3 storage
BACKUP_STORAGE_ADAPTER=s3
BACKUP_S3_BUCKET=my-backups
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Enable encryption
BACKUP_ENCRYPTION_ENABLED=true
GPG_RECIPIENT_KEY_ID=0xDEADBEEF12345678

# Install optional dependencies
make install-s3
```

---

## 🧪 Testing

### Run E2E Tests
```bash
# Start test containers
docker-compose -f docker-compose.e2e.yml up -d

# Run E2E tests
cd backend
pytest tests/e2e/test_backup_restore_e2e.py -m e2e

# Run performance tests
pytest tests/e2e/test_performance.py -m performance
```

### Test Data Management
```bash
# Generate test data
cd backend
python -m tests.fixtures.test_data

# Create large test dataset
python -c "from tests.fixtures.test_data import create_large_test_dataset; create_large_test_dataset('postgresql://testuser:testpass@localhost:5432/testdb', 100)"
```

---

## 🚨 Emergency Procedures

### Database Unavailable
```bash
# Check PostgreSQL status
docker-compose ps postgres
# or
systemctl status postgresql

# Check logs
docker-compose logs postgres
# or
tail -f /var/log/postgresql/postgresql-*.log
```

### No Recent Backups
```bash
# Check backup directory
ls -la backups/

# Check Celery task status
celery -A app.core.celery_app inspect active

# Manually trigger backup
make db-backup
```

### Corrupted Backup
```bash
# Verify backup integrity
gunzip -t backups/scheduled-*.sql.gz

# Try previous backup
ls -la backups/ | grep scheduled | tail -5
```

---

## 📈 Performance Benchmarks

### Expected Performance
- **Backup:** < 30 seconds for 1GB dataset
- **Restore:** < 60 seconds for 1GB dataset
- **Memory Usage:** < 500MB peak
- **CPU Usage:** < 80% average

### Performance Testing
```bash
# Run performance benchmarks
cd backend
pytest tests/e2e/test_performance.py -m performance -v

# Monitor system resources
htop
iostat -x 1
```

---

## 🔍 Troubleshooting

### Common Issues

**Backup Fails:**
```bash
# Check PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1;"

# Verify environment variables
echo $DATABASE_URL
echo $BACKUP_DIR
```

**Restore Fails:**
```bash
# Check file permissions
ls -la backups/

# Verify backup file
file backups/scheduled-*.sql.gz
gunzip -t backups/scheduled-*.sql.gz
```

**Performance Issues:**
```bash
# Check system resources
df -h
free -h
ps aux | grep pg_dump

# Monitor PostgreSQL
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

---

## 📞 Support

For issues or questions:
1. Check the [full runbook](admin_db.md)
2. Review logs: `/var/log/app/app.log`
3. Check audit events: `/var/log/app/audit.log`
4. Open an issue in the repository

---

*This quick reference covers the most common operations. For detailed procedures, security considerations, and advanced features, see the [Database Backup & Restore Runbook](admin_db.md).* 