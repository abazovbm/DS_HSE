# logging here
"""
Простой CLI менеджер паролей с шифрованием.
"""
import json
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
import hashlib
import argparse


VAULT_PATH = Path.home() / ".vault.enc"


def derive_key(master_password: str) -> bytes:
    digest = hashlib.sha256(master_password.encode()).digest()
    return urlsafe_b64encode(digest)


def load_vault(master: str) -> dict:
    if not VAULT_PATH.exists():
        return {}
    fernet = Fernet(derive_key(master))
    encrypted = VAULT_PATH.read_bytes()
    try:
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted)
    except Exception:
        print("Неверный мастер-пароль или повреждённое хранилище.")
        return None


def save_vault(vault: dict, master: str) -> None:
    fernet = Fernet(derive_key(master))
    encrypted = fernet.encrypt(json.dumps(vault).encode())
    VAULT_PATH.write_bytes(encrypted)


def cmd_add(args, master):
    vault = load_vault(master)
    if vault is None:
        return
    password = getpass.getpass(f"Пароль для {args.service}: ")
    vault[args.service] = {"login": args.login, "password": password}
    save_vault(vault, master)
    print(f"Сохранено: {args.service}")


def cmd_get(args, master):
    vault = load_vault(master)
    if vault is None:
        return
    entry = vault.get(args.service)
    if entry:
        print(f"Логин: {entry['login']}")
        print(f"Пароль: {entry['password']}")
    else:
        print("Не найдено.")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p_add = sub.add_parser("add")
    p_add.add_argument("service")
    p_add.add_argument("login")
    p_get = sub.add_parser("get")
    p_get.add_argument("service")
    args = parser.parse_args()

    master = getpass.getpass("Мастер-пароль: ")
    if args.cmd == "add":
        cmd_add(args, master)
    elif args.cmd == "get":
        cmd_get(args, master)


if __name__ == "__main__":
    main()
