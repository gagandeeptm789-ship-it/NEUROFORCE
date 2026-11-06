"""
Admin Seed Script
Controlled bootstrap utility to create initial university administrators.
Run from the backend directory:
    python scripts/seed_admin.py
Or with explicit arguments:
    python scripts/seed_admin.py --email admin@gmu.edu --name "Chief Administrator" --password "AdminPass123!" --role super_admin
"""

import argparse
import os
import sys

# Ensure backend root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal, init_db
from app.models.admin import Admin
from app.services.auth_service import get_admin_by_email, register_admin
from app.schemas.admin import AdminCreate


def seed_admin(email: str, full_name: str, password: str, role: str = "super_admin"):
    """Create initial administrator account."""
    init_db()
    db = SessionLocal()
    try:
        existing = get_admin_by_email(db, email)
        if existing:
            print(f"[!] Administrator with email '{email}' already exists (ID: {existing.id}, Role: {existing.role}).")
            return existing

        admin_in = AdminCreate(
            email=email,
            full_name=full_name,
            password=password,
            role=role,
        )
        new_admin = register_admin(db, admin_in)
        print("=" * 60)
        print("[+] SUCCESS: Administrator Account Created Successfully!")
        print(f"    ID:        {new_admin.id}")
        print(f"    Name:      {new_admin.full_name}")
        print(f"    Email:     {new_admin.email}")
        print(f"    Role:      {new_admin.role}")
        print(f"    Active:    {new_admin.is_active}")
        print("=" * 60)
        print("You can now authenticate via POST /api/admin/login.")
        return new_admin
    except Exception as e:
        print(f"[-] ERROR creating administrator: {e}")
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed initial administrator for The Forwarded Seal.")
    parser.add_argument("--email", default="admin@gmu.edu", help="Admin email address (default: admin@gmu.edu)")
    parser.add_argument("--name", default="University Registrar", help="Admin full name (default: University Registrar)")
    parser.add_argument("--password", default="AdminSecure2026!", help="Admin password (default: AdminSecure2026!)")
    parser.add_argument("--role", default="super_admin", help="Admin role (default: super_admin)")

    args = parser.parse_args()
    seed_admin(
        email=args.email,
        full_name=args.name,
        password=args.password,
        role=args.role,
    )


if __name__ == "__main__":
    main()

