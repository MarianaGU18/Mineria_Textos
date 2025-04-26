import pandas as pd

# Leer el archivo con municipios
df = pd.read_csv('datos_base/DATA_ESP/municipios_espana.csv', dtype=str)

# Asegurar formato con ceros a la izquierda
df['CODAUTO'] = df['CODAUTO'].str.zfill(2)
df['CPRO'] = df['CPRO'].str.zfill(2)
df['CMUN'] = df['CMUN'].str.zfill(3)
df['DC'] = df['DC'].str.zfill(1)

# Crear el código INE
df['INE'] = df['CPRO'] + df['CMUN'] + df['DC']

# Eliminar columnas que ya no se necesitan
df.drop(columns=['CMUN', 'DC'], inplace=True)

# Renombrar columna de nombre del municipio
df.rename(columns={'NOMBRE': 'MUNICIPIO'}, inplace=True)

# Leer comunidades y provincias
comunidades = pd.read_csv('datos_base/DATA_ESP/comunidades.csv', dtype=str)
comunidades['CODAUTO'] = comunidades['CODAUTO'].str.zfill(2)

provincias = pd.read_csv('datos_base/DATA_ESP/provincias.csv', dtype=str)
provincias['CPRO'] = provincias['CPRO'].str.zfill(2)

# Crear diccionarios de mapeo
dict_comunidades = dict(zip(comunidades['CODAUTO'], comunidades['COMUNIDAD']))
dict_provincias = dict(zip(provincias['CPRO'], provincias['PROVINCIA']))

# Reemplazar en las columnas originales
df['CODAUTO'] = df['CODAUTO'].map(dict_comunidades)
df['CPRO'] = df['CPRO'].map(dict_provincias)

# Renombrar columnas
df.rename(columns={
    'CODAUTO': 'COMUNIDAD',
    'CPRO': 'PROVINCIA'
}, inplace=True)

# Guardar el archivo final como CSV
df.to_csv('datos_base/DATA_ESP/data_ESP.csv', index=False)

# Guardar también como JSON (lista de diccionarios)
df.to_json('datos_base/DATA_ESP/data_ESP.json', orient='records', force_ascii=False, indent=2)

print("✅ Archivos creados en: datos_base/DATA_ESP")