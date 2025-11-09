import sys
import yaml
import requests
import gzip
from io import BytesIO

def get_direct_dependencies(package_name, repo_url):
    print(f"[DEBUG] Загружаем: {repo_url}")
    try:
        response = requests.get(repo_url, timeout=10)
        print(f"[DEBUG] Скачано: {len(response.content)} байт")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Ошибка сети: {e}")
        sys.exit(1)

    try:
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
            text = f.read().decode('utf-8')
        print(f"[DEBUG] Распаковано: {len(text)} символов")
    except Exception as e:
        print(f"Ошибка GZIP: {e}")
        sys.exit(1)

    packages = {}
    for block in text.split('\n\n'):
        if not block.strip(): continue
        info = {}
        for line in block.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                info[k.strip()] = v.strip()
        if 'Package' in info:
            packages[info['Package']] = info

    if package_name not in packages:
        print(f"Пакет '{package_name}' не найден!")
        print(f"Примеры: {list(packages.keys())[:5]}")
        sys.exit(1)

    deps_str = packages[package_name].get('Depends', '')
    deps = set()
    for part in deps_str.split(','):
        dep = part.strip().split('|')[0].split()[0]
        if dep and dep != package_name:
            deps.add(dep)

    return sorted(deps)

def main():
    try:
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Ошибка загрузки config.yaml: {e}")
        sys.exit(1)

    print("Конфигурация:")
    for k, v in config.items():
        print(f"  {k}: {v}")

    if config.get('test_mode', False):
        print("test_mode включён — сбор данных отключён.")
        return

    deps = get_direct_dependencies(config['package_name'], config['repo_url'])
    print("\nПрямые зависимости:")
    for d in deps:
        print(f"  - {d}")

if __name__ == "__main__":
    main()