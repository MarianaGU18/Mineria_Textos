# procesar_articulos.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from tqdm import tqdm  # Importar tqdm para la barra de progreso
import os
import time
import csv

origen = "ElPais"
count = 0
articuloError = []

# Leer las URLs desde el archivo generado
urlsArticulos = {}
with open('log_ejecuciones/ELPAIS_ESP/urlsExtraidas.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Saltar encabezado
    for row in reader:
        urlsArticulos[row[0]] = row[1]

# Configurar Selenium
options = webdriver.ChromeOptions()
options.add_argument('--disable-extensions')
options.add_argument('--blink-settings=imagesEnabled=false')
s = Service(os.path.dirname(os.path.abspath(__file__)) + '/chromedriver.exe')

#s = Service('C:/Servicio Social/Mineria_Textos/chromedriver.exe')


driver = webdriver.Chrome(options=options, service=s)

#for articulo, snap in urlsArticulos.items():
for articulo, snap in tqdm(urlsArticulos.items(), desc="Procesando artículos"):

    linkArticulo = f'https://web.archive.org/web/{snap}/{articulo}'
    try:
        driver.get(linkArticulo)
        time.sleep(5)
    except Exception as e:
        print(f"[ERROR] No se pudo acceder: {linkArticulo} - {e}")
        articuloError.append(linkArticulo)
        continue

    titulo, subtitulo, articuloContenido = "NONE", "NONE", "NONE"
    articuloFinal = []

    try:
        titulo = driver.find_element(By.TAG_NAME, "h1").text
        if titulo == "":
            el_titulo = driver.find_elements(By.TAG_NAME, "h1")
            if len(el_titulo) > 1:
                titulo = el_titulo[1].text
    except NoSuchElementException:
        pass

    try:
        subtitulo = driver.find_element(By.TAG_NAME, "h2").text
    except NoSuchElementException:
        pass

    contenido = driver.find_elements(By.CLASS_NAME, "articulo-contenido")
    if contenido:
        contenido = contenido[0].find_elements(By.CLASS_NAME, "contenido")
    else:
        contenido = driver.find_elements(By.CLASS_NAME, "paragraph")

    if titulo != "NONE" and subtitulo != "Hrm.":
        articuloFinal.extend([titulo, subtitulo])
        for itemContenido in contenido:
            textoLineas = itemContenido.text.strip().split('\n')
            for linea in textoLineas:
                if linea and not linea.startswith('-') and not (linea.startswith('(') and linea.endswith(')')):
                    articuloFinal.append(linea)

        df = pd.DataFrame({linkArticulo: articuloFinal})
        df.to_csv(f'articulos_x_procesar/ELPAIS_ESP/{origen}_{snap}_{count}_ESP.csv', index=False)
        count += 1
    else:
        articuloError.append(linkArticulo)

driver.quit()

if articuloError:
    df3 = pd.DataFrame({'': articuloError})
    df3.to_csv('log_ejecuciones/ELPAIS_ESP/articulosError_2020_2025_ESP.csv', index=False)

print("Procesamiento de artículos finalizado.")
