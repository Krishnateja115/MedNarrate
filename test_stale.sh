export HOST=127.0.0.1
export MEDNARRATE_VERSION=1.0.0
export MEDNARRATE_COMMIT=old_commit
cd mednarrate-backend && venv/bin/python3 run_server.py > /tmp/mednarrate_backend_test.log 2>&1 &
