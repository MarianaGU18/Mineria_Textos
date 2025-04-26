import csv

with open('datos_base\Terminos.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    terms_list = []  # Lista para almacenar los términos
    for rows in reader:
        terms_list.extend(rows[0].split(","))  # Agregar términos a la lista

# Formatear la salida como una lista de Python
formatted_output = f'[{", ".join(f"{term.strip()}" for term in terms_list)}]'
print(formatted_output)