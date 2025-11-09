import sys
import yaml
import requests
import gzip
from io import BytesIO

# === Этап 3: Построение графа зависимостей с DFS, циклы, max_depth, test_mode ===

def load_config():
    """Загружает и валидирует config.yaml"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Ошибка: config.yaml не найден!")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Ошибка YAML: {e}")
        sys.exit(1)

    required = ['package_name', 'repo_url', 'test_mode', 'max_depth']
    for key in required:
        if key not in config:
            print(f"Ошибка: отсутствует параметр '{key}' в config.yaml")
            sys.exit(1)

    if not isinstance(config['test_mode'], bool):
        print("Ошибка: test_mode должен быть true/false")
        sys.exit(1)
    if not isinstance(config['max_depth'], int) or config['max_depth'] < 1:
        print("Ошибка: max_depth должен быть целым числом >= 1")
        sys.exit(1)

    return config


def build_dependency_graph(config):
    """
    Строит граф зависимостей:
    - Если test_mode=True: читает из файла (A: B C)
    - Если test_mode=False: парсит Packages.gz
    """
    graph = {}

    if config['test_mode']:
        # === Тестовый режим: читаем из файла ===
        path = config['repo_url']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or ':' not in line:
                        continue
                    pkg, deps_str = line.split(':', 1)
                    pkg = pkg.strip()
                    deps = [d.strip() for d in deps_str.split() if d.strip()]
                    graph[pkg] = set(deps)
            print(f"[TEST MODE] Загружен тестовый граф из {path}: {len(graph)} пакетов")
        except FileNotFoundError:
            print(f"Ошибка: тестовый файл '{path}' не найден!")
            sys.exit(1)

    else:
        # === Реальный репозиторий: парсим Packages.gz ===
        url = config['repo_url']
        print(f"[REAL MODE] Загружаем репозиторий: {url}")
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Ошибка сети: {e}")
            sys.exit(1)

        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
                text = f.read().decode('utf-8')
        except Exception as e:
            print(f"Ошибка распаковки GZIP: {e}")
            sys.exit(1)

        packages = {}
        for block in text.split('\n\n'):
            if not block.strip():
                continue
            info = {}
            for line in block.split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    info[k.strip()] = v.strip()
            if 'Package' in info:
                packages[info['Package']] = info

        if config['package_name'] not in packages:
            print(f"Ошибка: пакет '{config['package_name']}' не найден в репозитории!")
            sys.exit(1)

        # Строим граф
        for pkg, info in packages.items():
            deps_str = info.get('Depends', '')
            deps = set()
            for part in deps_str.split(','):
                part = part.strip()
                if not part:
                    continue
                # Берём первую альтернативу
                dep = part.split('|')[0].strip().split()[0]
                if dep and dep != pkg:
                    deps.add(dep)
            graph[pkg] = deps

        print(f"[REAL MODE] Построен граф: {len(graph)} пакетов")

    return graph


def dfs_build_subgraph(start_pkg, graph, max_depth):
    """
    DFS с рекурсией:
    - Учитывает max_depth
    - Обнаруживает циклы
    - Возвращает подграф зависимостей
    """
    subgraph = {}
    visited = set()
    visiting = set()  # для обнаружения циклов

    def dfs(pkg, depth):
        if depth > max_depth:
            return
        if pkg in visiting:
            raise RecursionError(f"Цикл обнаружен: ... -> {pkg}")
        if pkg in visited:
            return

        visiting.add(pkg)
        subgraph[pkg] = set()

        if pkg in graph:
            for dep in graph[pkg]:
                subgraph[pkg].add(dep)
                dfs(dep, depth + 1)

        visiting.remove(pkg)
        visited.add(pkg)

    try:
        dfs(start_pkg, 0)
        print(f"Граф зависимостей построен (глубина ≤ {max_depth})")
    except RecursionError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

    return subgraph


def print_graph(subgraph):
    """Красиво выводит граф"""
    print("\nГраф зависимостей:")
    for pkg in sorted(subgraph):
        deps = sorted(subgraph[pkg])
        print(f"  {pkg} → {', '.join(deps) if deps else 'нет'}")
    print(f"Всего узлов: {len(subgraph)}")


def main():
    config = load_config()
    print("Конфигурация загружена:")
    for k, v in config.items():
        print(f"  {k}: {v}")

    # Строим полный граф
    full_graph = build_dependency_graph(config)

    # Строим подграф от целевого пакета
    subgraph = dfs_build_subgraph(config['package_name'], full_graph, config['max_depth'])

    # Выводим результат
    print_graph(subgraph)


if __name__ == "__main__":
    main()