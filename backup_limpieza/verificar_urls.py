import re

with open('farmacia/urls.py', 'r') as f:
    content = f.read()

# Extraer todos los nombres de URL
pattern = r"name=['\"]([^'\"]+)['\"]"
url_names = re.findall(pattern, content)

print("Todos los nombres de URL en farmacia/urls.py:")
for name in sorted(url_names):
    print(f"  - {name}")

print("\nURLs relacionadas con recetas:")
for name in url_names:
    if 'receta' in name.lower() or 'pago' in name.lower():
        print(f"  - {name}")
