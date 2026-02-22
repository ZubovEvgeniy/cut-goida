import os

import requests
import urllib.parse

from requests.adapters import HTTPAdapter
from urllib3 import Retry

SOURCES = {
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/1.txt": "configs/my_configs_1.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/2.txt": "configs/my_configs_2.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/3.txt": "configs/my_configs_3.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/4.txt": "configs/my_configs_4.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/5.txt": "configs/my_configs_5.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/6.txt": "configs/my_configs_6.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/7.txt": "configs/my_configs_7.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/8.txt": "configs/my_configs_8.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/9.txt": "configs/my_configs_9.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/11.txt": "configs/my_configs_11.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/12.txt": "configs/my_configs_12.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/13.txt": "configs/my_configs_13.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/14.txt": "configs/my_configs_14.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/15.txt": "configs/my_configs_15.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/16.txt": "configs/my_configs_16.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/17.txt": "configs/my_configs_17.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/19.txt": "configs/my_configs_19.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/20.txt": "configs/my_configs_20.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/21.txt": "configs/my_configs_21.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/22.txt": "configs/my_configs_22.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/23.txt": "configs/my_configs_23.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/24.txt": "configs/my_configs_24.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/githubmirror/25.txt": "configs/my_configs_25.txt",
}

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
    "🇪🇪", "estonia",
    "🇱🇻", "latvia",
    "🇱🇹", "lithuania",
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
    "expire", "expired",
    "test", "traffic",
    "timeout", "error",
    "telegram", "channel",
    "v2ray_configs_pool", "vpn_ioss", "amir_rooman",
]


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

def fetch_and_filter_configs():
    os.makedirs("configs", exist_ok=True)
    session = get_session()
    for url, output_filename in SOURCES.items():
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

        except Exception as e:
            print(f"Ошибка при загрузке {url}: {e}")


if __name__ == "__main__":
    fetch_and_filter_configs()
