import os

import requests
import urllib.parse

from requests.adapters import HTTPAdapter
from urllib3 import Retry

SOURCES = [
    # --- Добавляй новые источники сюда ---

    # Вариант 1: репозиторий с пронумерованными файлами
    # {
    #     "pattern": "https://example.com/configs/{i}.txt",
    #     "count": 50,              # файлы от 1 до 50
    #     # "indices": [1, 3, 7],  # или вручную, если нумерация с пропусками
    # },

    # Вариант 2: одиночный файл
    # {
    #     "url": "https://example.com/all-configs.txt",
    # },

    {
        "pattern": "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/{i}.txt",
        "count": 25,
    },
    {
        "pattern": "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-{i}.txt",
        "count": 36,
    },
]

OUTPUT_FILE = "my_vless_reality.txt"

ALLOWED_KEYWORDS = [
    # --- Северная Америка ---
    "🇺🇸", "usa", "united states", "america",
    "🇨🇦", "canada",
    # --- Северная Европа ---
    "🇸🇪", "sweden",
    "🇳🇴", "norway",
    "🇩🇰", "denmark",
    "🇫🇮", "finland",
    "🇱🇻", "latvia",
    # --- Западная Европа ---
    "🇬🇧", "uk", "united kingdom", "great britain", "england",
    "🇮🇪", "ireland",
    "🇫🇷", "france",
    "🇳🇱", "netherlands", "holland",
    "🇧🇪", "belgium",
    "🇱🇺", "luxembourg",
    # --- Центральная Европа ---
    "🇩🇪", "germany",
    "🇵🇱", "poland",
    "🇨🇿", "czech", "czechia",
    "🇸🇰", "slovakia",
    "🇭🇺", "hungary",
    # --- Южная Европа ---
    "🇪🇸", "spain",
    # --- Балканы и Восточная Европа ---
    "🇷🇴", "romania",
    "🇧🇬", "bulgaria",
    "🇭🇷", "croatia",
    "🇷🇸", "serbia",
    "🇸🇮", "slovenia",
    "🇦🇲", "armenia",
]
STOP_WORDS = [
    "🇷🇺", "russia",
    "🇮🇷", "iran",
    "🇨🇳", "china",
    "🇸🇪", "Sweden",
    "🇫🇮", "Finland",
    "🇱🇹", "lithuania",
    "🇪🇪", "estonia",
    "expire", "expired",
    "test", "traffic",
    "timeout", "error",
    "telegram", "channel",
    "v2ray_configs_pool", "vpn_ioss", "amir_rooman",
]


def extract_github_username(url):
    """Извлекает имя пользователя GitHub из URL вида github.com/USER/... или raw.githubusercontent.com/USER/..."""
    parsed = urllib.parse.urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if parts and parts[0]:
        return parts[0].lower()
    return "unknown"


def expand_sources(sources):
    """Разворачивает описания источников в список кортежей (url, output_filename, author)."""
    result = []
    for source in sources:
        if "url" in source:
            url = source["url"]
            author = extract_github_username(url)
            result.append((url, f"configs/{author}_1.txt", author))
        elif "pattern" in source:
            base_url = source["pattern"].replace("{i}", "0")
            author = extract_github_username(base_url)
            indices = source.get("indices") or range(1, source["count"] + 1)
            for idx, i in enumerate(indices, start=1):
                url = source["pattern"].format(i=i)
                result.append((url, f"configs/{author}_{idx}.txt", author))
    return result


def get_session():
    session = requests.Session()

    # 1. Маскировка под обычный браузер Chrome на Windows
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    # 2. Пул соединений и авто-повторы
    retries = Retry(
        total=3,  # Делаем 3 попытки
        backoff_factor=0.5,  # Пауза между попытками
        status_forcelist=[429, 500, 502, 503, 504]  # При каких ошибках сервера повторять запрос
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

def generate_readme(stats):
    # Группируем по автору, сохраняя порядок появления
    groups = {}
    for item in stats:
        groups.setdefault(item["author"], []).append(item)

    md_lines = []
    for author, items in groups.items():
        total_servers = sum(i["count"] for i in items)
        md_lines.append(f"## {author} — {len(items)} файлов, {total_servers} серверов")
        md_lines.append("")
        for item in items:
            filename = item["link"].split("/")[-1]
            md_lines.append(f"**{filename}** ({item['count']} серверов)")
            md_lines.append(f"```\n{item['link']}\n```")
            md_lines.append("")

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print("-> Файл README.md успешно обновлен!")

def fetch_and_filter_configs():
    os.makedirs("configs", exist_ok=True)
    session = get_session()
    stats = []
    for i, (url, output_filename, author) in enumerate(expand_sources(SOURCES), start=1):
        # создаем пустое множество для каждой новой ссылки, чтобы они не смешивались
        filtered_configs = set()

        try:
            print(f"Скачиваю базу: {url}")
            response = session.get(url, timeout=10)
            response.raise_for_status()

            lines = response.text.splitlines()

            for line in lines:
                line = line.strip()
                line_lower = line.lower()

                # 1. проверка протокола
                if not line_lower.startswith("vless://") or "reality" not in line_lower:
                    continue

                # расшифровываем всю строку целиком (чтобы url-коды превратились в текст)
                full_decoded_line = urllib.parse.unquote(line_lower)
                # 2. проверка небезопасных конфигов
                if "allowinsecure=1" in full_decoded_line or "allowinsecure=true" in full_decoded_line or "insecure=1" in full_decoded_line:
                    continue

                # 3. проверка стоп слов
                if any(stop_word in full_decoded_line for stop_word in STOP_WORDS):
                    continue

                # 4. разрешенные страны
                if "#" in line:
                    raw_name = line.split("#", 1)[1]
                    decoded_name = urllib.parse.unquote(raw_name).lower()
                    if any(keyword in decoded_name for keyword in ALLOWED_KEYWORDS):
                        filtered_configs.add(line)

            # сохраняем результат для текущей ссылки в её собственный файл
            with open(output_filename, "w", encoding="utf-8") as f:
                for config in filtered_configs:
                    f.write(config + "\n")

            print(f"-> Успешно! Сохранено {len(filtered_configs)} конфигов в файл {output_filename}\n")

            filename = os.path.basename(output_filename)
            raw_link = f"https://raw.githubusercontent.com/ZubovEvgeniy/cut-goida/main/configs/{filename}"

            stats.append({
                "num": i,
                "author": author,
                "link": raw_link,
                "count": len(filtered_configs)
            })

        except Exception as e:
            print(f"Ошибка при загрузке {url}: {e}")

    if stats:
        generate_readme(stats)


if __name__ == "__main__":
    fetch_and_filter_configs()
