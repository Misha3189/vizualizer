import sys
import yaml
import requests
import gzip
from io import BytesIO

def main():
    config_file = 'config.yaml'
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        if not isinstance(config, dict):
            raise ValueError("Конфигурационный файл должен быть в формате словаря YAML.")
    except FileNotFoundError:
        print(f"Ошибка: Файл конфигурации '{config_file}' не найден.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Ошибка парсинга YAML: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неизвестная ошибка при загрузке конфигурации: {e}")
        sys.exit(1)
    required_params = {
        'package_name': str,
        'repo_url': str,
        'test_mode': bool,
        'ascii_mode': bool,
        'max_depth': int
    }

    for param, param_type in required_params.items():
        if param not in config:
            print(f"Ошибка: Отсутствует обязательный параметр '{param}' в конфигурации.")
            sys.exit(1)
        if not isinstance(config[param], param_type):
            print(f"Ошибка: Параметр '{param}' должен быть типа {param_type.__name__}, но получен {type(config[param]).__name__}.")
            sys.exit(1)

    # Дополнительные проверки
    if config['max_depth'] < 1:
        print("Ошибка: 'max_depth' должен быть положительным целым числом (>=1).")
        sys.exit(1)
    if not config['repo_url']:
        print("Ошибка: 'repo_url' не может быть пустым.")
        sys.exit(1)

    # Вывод параметров (только для этого этапа)
    print("Настраиваемые параметры:")
    for key, value in config.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()