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

#urlsArticulos = dict(list(urlsArticulos.items())[:10])  # Limitar a los primeros 100 artículos


# Configurar Selenium
options = webdriver.ChromeOptions()
options.add_argument('--disable-extensions')
options.add_argument('--blink-settings=imagesEnabled=false')
chromedriver_path = Service(os.path.dirname(os.path.abspath(__file__)) + '/chromedriver.exe')

#s = Service('C:/Servicio Social/Mineria_Textos/chromedriver.exe')


driver = webdriver.Chrome(options=options, service=chromedriver_path)

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

    titulo, subtitulo, localizacion, articuloContenido, etiqueta = ["NONE"] * 5
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

    try:
        etiqueta = driver.find_elements(By.CSS_SELECTOR, ".cs_t_l, ._db, .a_k, ._df, .k, .kicker, .uppercase")

        if etiqueta:  # Verifica si se encontró al menos un elemento
            etiqueta = etiqueta[0].text  # Obtiene el texto del primer elemento
        else:
            etiqueta = "No encontrada etiqueta"
    except NoSuchElementException:
        pass


    # Extraer la etiqueta, puede ser una categoría o algo similar (Cambio realizado aquí)
    try:
        localizacion = driver.find_elements(By.CSS_SELECTOR, ".articulo-localizacion,.capitalize,.color_black")
        
        if localizacion:  # Verifica si se encontró al menos un elemento
            localizacion = localizacion[0].text  # Obtiene el texto del primer elemento
        else:
            localizacion = "No encontrada ubicación"
    except NoSuchElementException:
        pass
   
    
    try:
        articuloContenido = driver.find_elements(By.CSS_SELECTOR, '.articulo-cuerpo, .a_b, .article_body, .color_gray_dark, .a_c, .clearfix, .c_d, p[class=""]')
        
        if articuloContenido:  # Si encontró al menos uno con las clases
            articuloContenido = articuloContenido[0].text
        else:
            # Si NO encontró nada, buscar en todos los <p>
            parrafos = driver.find_elements(By.TAG_NAME, "p")
            if parrafos:
                articuloContenido = " ".join(p.text for p in parrafos if p.text.strip())
            else:
                articuloContenido = "No encontrada contenido"
    except NoSuchElementException:
        articuloContenido = "No encontrada aticulo"


    
    articulo = articuloFinal.extend([titulo, subtitulo, etiqueta,localizacion,articuloContenido])
    print(articulo)

    df = pd.DataFrame({linkArticulo: articuloFinal})
   
    df.to_csv(f'articulos_x_procesar/ELPAIS_ESP1/{origen}_{snap}_{count}_ESP.csv', index=False)
    count += 1

    '''    
  
    if titulo != "NONE" and subtitulo != "Hrm.":
        articuloFinal.extend([titulo, subtitulo, etiqueta])
        for itemContenido in contenido:
            textoLineas = itemContenido.text.strip().split('\n')
            for linea in textoLineas:
                if linea and not linea.startswith('-') and not (linea.startswith('(') and linea.endswith(')')):
                    articuloFinal.append(linea)

        df = pd.DataFrame({linkArticulo: articuloFinal})
        df.to_csv(f'articulos_x_procesar/ELPAIS_ESP1/{origen}_{snap}_{count}_ESP.csv', index=False)
        count += 1
    else:
        articuloError.append(linkArticulo)
    '''

driver.quit()

if articuloError:
    df3 = pd.DataFrame({'': articuloError})
    df3.to_csv('log_ejecuciones/ELPAIS_ESP1/articulosError_2020_2025_ESP.csv', index=False)

print("Procesamiento de artículos finalizado.")
