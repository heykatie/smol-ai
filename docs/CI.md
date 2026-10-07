# Automated checks

GitHub Actions checks run on main pushes, pull requests and manual dispatch. Repository access is read-only, checkout credentials are not persisted, and no provider or production database secrets are used. Superseded runs are cancelled; each job has a bounded timeout.

SQLite checks cover Python 3.9 and 3.12. The database job uses Python 3.12 and PostgreSQL 16 on Ubuntu 24.04. It initializes a private Unix-socket cluster with no TCP listener, runs the full suite, rejects skipped tests, and stops the started cluster. Synthetic logs remain in temporary job storage.

Run the same database helper locally with installed initdb/pg_ctl tools:

    .venv/bin/python scripts/check_postgres.py --pg-bin /path/to/postgres/bin --work-dir /path/to/test-results

The CI-only publishing snapshot passed 156 tests without skips using local Python 3.9.4/PostgreSQL 14.15. Pending app changes are excluded from that snapshot. Hosted checks passed on Ubuntu 24.04: Python 3.9 and 3.12 SQLite jobs each passed 139 tests; Python 3.12/PostgreSQL 16 passed 156 tests with zero skips. [Run evidence](https://github.com/heykatie/smolstuff/actions/runs/37578657780). This workflow neither deploys nor configures required merge checks. Dependency installation uses version ranges; it is not a lockfile.
