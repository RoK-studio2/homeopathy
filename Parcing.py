import re
import json
from pathlib import Path
from pprint import pprint

def parse_homeopathy_text(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    data = {}
    i = 0
    while i < len(lines):
        line = lines[i]

        if i + 1 < len(lines) and re.match(r'^\([A-Za-z\s]+\)$', lines[i + 1]):
            russian_name = line
            latin_name = lines[i + 1].strip("()")
            i += 2
            symptoms = []

            while i < len(lines) and lines[i].startswith("-"):
                symptoms.append(lines[i].lstrip('-').strip())
                i += 1

            key = latin_name if latin_name else russian_name
            data[key] = {
                "russian": russian_name,
                "latin": latin_name,
                "symptoms": symptoms
            }
        else:
            i += 1

    return data

# Пример использования
if __name__ == "__main__":
    # Détection automatique du chemin du fichier source et destination
    base_dir = Path(__file__).parent
    txt_path = base_dir / "homeopathy.txt"
    json_path = Path.home() / "Documents" / "Bot" / "Homeopathy" / "homeopathy.json"

    if not txt_path.exists():
        print(f"❌ Файл {txt_path} не найден. Поместите homeopathy.txt рядом с Parcing.py.")
        exit(1)

    result = parse_homeopathy_text(str(txt_path))
    pprint(result, width=120)
    print(f"\n✅ Найдено препаратов: {len(result)}")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Данные сохранены в {json_path}")
    print("✅ Парсинг завершен успешно!")
