import json

def extract_names():
    with open('dictionary.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    dictionary = data.get('DICTIONARY', {})

    for item in dictionary.values():
        ru_name = item.get('ru')
        if ru_name and any(char in 'abcdefghijklmnopqrstuvwxyz' for char in ru_name.lower()):
            if not ru_name.startswith("Реликвия"):
                print(ru_name)

if __name__ == "__main__":
    extract_names()
