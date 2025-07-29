import os
import pandas as pd
import json

# Carpeta con los artículos procesados en CSV
carpeta_csv = 'articulos_x_procesar/ELPAIS_ESP'
archivos_csv = [f for f in os.listdir(carpeta_csv) if f.endswith('.csv')]

articulos = []

for archivo in archivos_csv:
    ruta = os.path.join(carpeta_csv, archivo)
    try:
        df = pd.read_csv(ruta)
        # La URL del artículo está en el nombre de la única columna
        url = df.columns[0]
        contenido = df.iloc[:, 0].dropna().tolist()  # El contenido del artículo

        articulos.append({
            'url': url,
            'contenido': contenido
        })
    except Exception as e:
        print(f"❌ Error procesando {archivo}: {e}")

# Guardar como JSON
with open('articulos_x_procesar/ELPAIS_ESP/articulos_procesados_ELPAIS_ESP.json', 'w', encoding='utf-8') as json_file:
    json.dump(articulos, json_file, ensure_ascii=False, indent=4)

print("✅ JSON generado: articulos_procesados_ELPAIS_ESP.json")
