import os
import asyncio
from alembic.config import Config
from alembic import command
import shutil

# Configure Alembic to use a disposable database
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///disposable.db"

# Clear existing disposable DB if it exists
if os.path.exists("disposable.db"):
    os.remove("disposable.db")

alembic_cfg = Config("alembic.ini")

def test_migrations():
    print("--- Upgrading to head ---")
    command.upgrade(alembic_cfg, "head")
    
    print("--- Downgrading ---")
    command.downgrade(alembic_cfg, "cebe80380c15")
    
    print("--- Upgrading to head again ---")
    command.upgrade(alembic_cfg, "head")
    
    print("--- Checking current head ---")
    command.current(alembic_cfg)
    
if __name__ == "__main__":
    test_migrations()
