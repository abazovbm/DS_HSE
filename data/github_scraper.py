"""
Скрипт сбора Python-кода с GitHub по поисковым запросам.

Использование:
    1. Получить персональный токен GitHub: https://github.com/settings/tokens
       (нужен скоуп public_repo).
    2. Сохранить в переменной окружения:
           export GITHUB_TOKEN=ghp_xxxxx
    3. Запустить:
           python github_scraper.py

Что делает:
    - Ищет репозитории по списку поисковых запросов (LEGIT_QUERIES, ILLEGIT_QUERIES).
    - Для каждого репозитория скачивает .py файлы (с ограничением размера).
    - Сохраняет в data/raw/<label>/<repo_name>/<file>.py
    - Логирует прогресс.

Важно про этичность и API:
    - Используем ТОЛЬКО публичные репозитории.
    - Соблюдаем rate limits GitHub (5000 запросов/час с токеном).
    - Не скачиваем приватный код.
    - Цель — обучение детектора, а не сбор готовых решений.

Найденные данные нужно потом ВРУЧНУЮ просмотреть и разметить:
    - убрать из легитимных случайно попавшие криптоказино;
    - убрать из нелегитимных просто библиотеки (web3.py, ccxt и т.п.);
    - удалить дубликаты, пустые файлы.

Это полностью согласуется с указанием руководителя:
"можно просто по github по ключевым словам поискать, там такого много"
"""

import os
import time
import logging
import re
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("Установите requests: pip install requests")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    logger.warning(
        "GITHUB_TOKEN не задан. Без него лимит = 60 запросов/час."
    )

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

OUT_DIR = Path(__file__).parent / "raw"
MAX_FILE_BYTES = 50_000  # игнорируем большие файлы
MAX_FILES_PER_REPO = 5
MAX_REPOS_PER_QUERY = 10

# ВНИМАНИЕ: нужно подбирать запросы под язык программирования и тип бота.
# Это лишь примеры — добавляйте свои варианты.

LEGIT_QUERIES = [
    "telegram bot weather python",
    "telegram bot reminder python",
    "flask blog example python",
    "fastapi crud python",
    "telegram bot quote python",
    "rss parser python",
    "discord bot music python",
    "telegram bot todo python",
    "image converter cli python",
    "smtp email sender python",
]

ILLEGIT_QUERIES = [
    "telegram bot crypto casino python",
    "dice game USDT bot python",
    "telegram crash game python",
    "roulette telegram bot python crypto",
    "slots bot python crypto",
    "aviator clone python bot",
    "mines game bot python crypto",
    "casino telegram bot TRX",
    "lottery bot crypto python",
]


def search_repos(query: str, max_repos: int) -> list:
    """Ищет публичные репозитории по запросу через GitHub Search API."""
    url = "https://api.github.com/search/repositories"
    params = {"q": query + " language:python", "per_page": max_repos, "sort": "stars"}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if resp.status_code == 403:
        logger.warning("Rate limit. Спим 60 секунд.")
        time.sleep(60)
        return search_repos(query, max_repos)
    resp.raise_for_status()
    return resp.json().get("items", [])


def list_python_files(owner: str, repo: str, max_files: int) -> list:
    """Возвращает до max_files путей к .py файлам в репозитории."""
    # Используем Git Tree API — рекурсивный листинг
    repo_info = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=HEADERS, timeout=30
    ).json()
    default_branch = repo_info.get("default_branch", "main")
    tree_url = (
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/"
        f"{default_branch}?recursive=1"
    )
    resp = requests.get(tree_url, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        return []
    tree = resp.json().get("tree", [])
    py_files = [
        t for t in tree
        if t.get("type") == "blob"
        and t.get("path", "").endswith(".py")
        and t.get("size", 0) < MAX_FILE_BYTES
        and t.get("size", 0) > 200  # пропускаем совсем пустые
    ]
    # Сортируем по размеру и берём средние (не самые маленькие, не самые большие)
    py_files.sort(key=lambda x: x.get("size", 0))
    middle = py_files[len(py_files) // 4 : 3 * len(py_files) // 4]
    return middle[:max_files]


def download_file(owner: str, repo: str, branch: str, path: str) -> str:
    """Скачивает содержимое файла."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 200:
        return resp.text
    return ""


def safe_filename(s: str) -> str:
    """Делает строку безопасной для использования в имени файла."""
    return re.sub(r"[^\w\-_.]", "_", s)[:100]


def collect_for_label(queries: list, label: str):
    label_dir = OUT_DIR / label
    label_dir.mkdir(parents=True, exist_ok=True)
    total_files = 0

    for q in queries:
        logger.info(f"[{label}] Поиск: {q}")
        try:
            repos = search_repos(q, MAX_REPOS_PER_QUERY)
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            continue

        for repo in repos:
            owner = repo["owner"]["login"]
            name = repo["name"]
            branch = repo.get("default_branch", "main")
            repo_dir = label_dir / safe_filename(f"{owner}__{name}")
            if repo_dir.exists():
                continue
            try:
                files = list_python_files(owner, name, MAX_FILES_PER_REPO)
            except Exception as e:
                logger.error(f"Ошибка листинга {owner}/{name}: {e}")
                continue

            if not files:
                continue
            repo_dir.mkdir(exist_ok=True)
            for f in files:
                content = download_file(owner, name, branch, f["path"])
                if not content:
                    continue
                out_name = safe_filename(f["path"].replace("/", "__"))
                (repo_dir / out_name).write_text(content, encoding="utf-8", errors="ignore")
                total_files += 1
            time.sleep(1)  # вежливая задержка
        time.sleep(2)
    logger.info(f"[{label}] Всего файлов: {total_files}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    collect_for_label(LEGIT_QUERIES, "legitimate")
    collect_for_label(ILLEGIT_QUERIES, "illegitimate")
    logger.info("Готово. Просмотрите и при необходимости отредактируйте данные вручную.")
    logger.info(f"Результат: {OUT_DIR}")


if __name__ == "__main__":
    main()
