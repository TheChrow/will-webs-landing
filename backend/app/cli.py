"""Comandos de administración.

Crear un usuario del panel (la contraseña se pide por consola o se lee de ADMIN_PASSWORD):
    python -m app.cli create-admin --email ana@empresa.cl --name "Ana Pérez" --role admin
"""

import argparse
import asyncio
import getpass
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import MIN_PASSWORD_LENGTH, hash_password
from app.db.session import dispose_engine, get_engine
from app.models import AdminUser, Role


async def create_admin(email: str, name: str, role: str, password: str) -> str:
    maker = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with maker() as session, session.begin():
        role_obj = (
            await session.execute(select(Role).where(Role.name == role))
        ).scalar_one_or_none()
        if role_obj is None:
            raise SystemExit(f"Rol '{role}' no existe (¿se ejecutaron los seeds?)")
        exists = (
            await session.execute(select(AdminUser.id).where(AdminUser.email == email))
        ).scalar_one_or_none()
        if exists:
            raise SystemExit(f"Ya existe un usuario con email {email}")
        user = AdminUser(
            email=email, full_name=name, password_hash=hash_password(password), roles=[role_obj]
        )
        session.add(user)
    await dispose_engine()
    return user.public_id


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("create-admin", help="crear usuario del panel admin")
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--role", choices=["admin", "editor"], default="admin")
    args = parser.parse_args()

    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Contraseña: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")
    public_id = asyncio.run(
        create_admin(args.email.strip().lower(), args.name.strip(), args.role, password)
    )
    print(f"Usuario creado: {args.email} ({args.role}) id={public_id}")


if __name__ == "__main__":
    main()
