import os
import pandas as pd
import pycountry
import tldextract

# Carpeta que contiene los CSVs
carpeta_csv = "articulos_x_procesar/ELPAIS_ESP"

# Conjunto de nombres de países en minúsculas
paises = {country.name.lower() for country in pycountry.countries}

paises.add("españa")  # Agregar "España" a la lista de países
paises.add("España")  # Agregar "España" a la lista de países
paises.add("espana")  # Agregar "España" a la lista de países
paises.add("Espana")  # Agregar "España" a la lista de países
paises.add("México")  # Agregar "España" a la lista de países
paises.add("Turquia")  # Agregar "España" a la lista de países
'''
# Función para detectar país desde la URL
def detectar_pais(url):
    ext = tldextract.extract(url)
    dominio = ext.domain.lower()
    subdominio = ext.subdomain.lower()
    path = url.lower()

    for pais in paises:
        if pais in dominio or pais in subdominio or pais in path:
            return pais.title()


def obtener_una_url(archivo,carpeta_csv):
        
    if archivo.endswith(".csv"):
        ruta_archivo = os.path.join(carpeta_csv, archivo)
        df = pd.read_csv(ruta_archivo, header=None)
        if not df.empty:
            url = df.iloc[0, 0]
            return url  # Sale al encontrar la primera URL
    return None  # Si no se encuentra ninguna


for archivo in os.listdir(carpeta_csv):

    url= obtener_una_url(archivo,carpeta_csv)

    #print(f"URL encontrada: {url}")

    paisuwu =  detectar_pais(url)


#detectar_pais(url)

'''
print("Lista de países en minúsculas:")
for pais in paises:
    print(pais)
