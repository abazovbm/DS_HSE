# experimental
"""
Утилита генерации и управления Ethereum-кошельками для разработки/тестирования.
Только локальное хранение ключей.
"""
from web3 import Web3
from eth_account import Account
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
import argparse
import getpass


WALLET_DIR = Path.home() / ".dev_wallets"
RPC_URL = os.environ.get("ETH_RPC", "https://mainnet.infura.io/v3/PROJECT_ID")
w3 = Web3(Web3.HTTPProvider(RPC_URL))


def generate_wallet():
    """Создаёт новый ETH-кошелёк."""
    Account.enable_unaudited_hdwallet_features()
    acct, mnemonic = Account.create_with_mnemonic()
    return {
        "address": acct.address,
        "private_key": acct.key.hex(),
        "mnemonic": mnemonic,
    }


def encrypt_wallet(wallet: dict, password: str) -> bytes:
    key = Fernet.generate_key()
    f = Fernet(key)
    return f.encrypt(json.dumps(wallet).encode()), key


def get_balance(address: str) -> float:
    balance_wei = w3.eth.get_balance(address)
    return w3.from_wei(balance_wei, "ether")


def list_wallets():
    if not WALLET_DIR.exists():
        return []
    return [p.stem for p in WALLET_DIR.glob("*.json")]


def cmd_create(args):
    WALLET_DIR.mkdir(exist_ok=True)
    wallet = generate_wallet()
    password = getpass.getpass("Пароль для шифрования: ")
    encrypted, key = encrypt_wallet(wallet, password)
    out_path = WALLET_DIR / f"{args.name}.json"
    out_path.write_bytes(encrypted)
    print(f"Создан: {wallet['address']}")
    print(f"Сохранён в: {out_path}")
    print(f"Ключ: {key.decode()}")


def cmd_balance(args):
    balance = get_balance(args.address)
    print(f"Баланс {args.address}: {balance} ETH")


def cmd_list(args):
    wallets = list_wallets()
    print(f"Сохранено кошельков: {len(wallets)}")
    for w in wallets:
        print(f"  - {w}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p_create = sub.add_parser("create")
    p_create.add_argument("name")
    p_balance = sub.add_parser("balance")
    p_balance.add_argument("address")
    sub.add_parser("list")
    args = parser.parse_args()

    handlers = {"create": cmd_create, "balance": cmd_balance, "list": cmd_list}
    handler = handlers.get(args.cmd)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
