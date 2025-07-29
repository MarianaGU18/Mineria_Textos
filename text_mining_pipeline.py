import os
import csv
import time
import requests
import pandas as pd
from datetime import datetime
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm
from datetime import datetime

class TextMiningPipeline:
    def __init__(self, sitio, origen, from_date, to_date, palabras_clave_path):
        self.sitio = sitio
        self.origen = origen
        self.from_date = from_date
        self.to_date = to_date
        self.snapshots = {}
        self.urls_articulos = {}
        self.snap_errors = []
        self.articulo_errors = []
        self.palabras_clave = self._cargar_palabras_clave(palabras_clave_path)
        self._crear_directorios()

    def _crear_directorios(self):
        os.makedirs(f'articulos_x_procesar/{self.origen}', exist_ok=True)
        os.makedirs(f'log_ejecuciones/{self.origen}', exist_ok=True)

    def _cargar_palabras_clave(self, path):
        terms_list = []
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.reader(f):
                if row:
                    terms_list.extend(t.strip().lower() for t in row[0].split(',') if t.strip())
        return terms_list

    def obtener_snapshots(self):
        url = 'https://web.archive.org/cdx/search/cdx'
        params = {'url': self.sitio, 'from': self.from_date, 'to': self.to_date}
        try:
            r = requests.get(url, params=params, timeout=100)
            r.raise_for_status()
            for snap in r.text.strip().split('\n'):
                partes = snap.split(' ')
                if len(partes) < 2:
                    continue  # línea malformada
                snap_fecha = partes[1]
                fecha = datetime.strptime(snap_fecha, "%Y%m%d%H%M%S")
                self.snapshots[fecha.date()] = snap_fecha
        except Exception as e:
            print(f"Error obteniendo snapshots: {e}")

    def filtrar_urls_relevantes(self):
        for fecha, snap in tqdm(self.snapshots.items(), desc="Filtrando URLs"):
            url_archivo = f'https://web.archive.org/web/{snap}/https://{self.sitio}'
            try:
                r = requests.get(url_archivo, timeout=100)
                if r.status_code != 200:
                    self.snap_errors.append(snap)
                    continue
                doc = html.fromstring(r.text)
                enlaces = doc.xpath('//a')
                for e in enlaces:
                    href = e.get('href')
                    if href and any(p in e.text_content().lower() for p in self.palabras_clave):
                        href = href[href.find('http'):]
                        self.urls_articulos[href.replace("http:", "https:")] = snap
            except Exception:
                self.snap_errors.append(snap)
                continue
        self._guardar_log_urls()

    def _guardar_log_urls(self):
        df = pd.DataFrame({'': [f"Fecha: {snap}, Artículo: {url}" for url, snap in self.urls_articulos.items()]})
        df.to_csv(f'log_ejecuciones/{self.origen}/archivoControl.csv', index=False)

        df2 = pd.DataFrame({'': self.snap_errors})
        df2.to_csv(f'log_ejecuciones/{self.origen}/erroresSnapshots.csv', index=False)

        with open(f'log_ejecuciones/{self.origen}/urlsExtraidas.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'snapshot'])
            for url, snap in self.urls_articulos.items():
                writer.writerow([url, snap])

    def procesar_articulos(self):
        path_csv = f'log_ejecuciones/{self.origen}/urlsExtraidas.csv'
        with open(path_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            self.urls_articulos = {row[0]: row[1] for row in reader}

        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--headless')

        driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe')

        count = 0
        for url, snap in tqdm(self.urls_articulos.items(), desc="Procesando artículos"):
            full_url = f'https://web.archive.org/web/{snap}/{url}'
  
            driver = webdriver.Chrome(options=options, service=Service(driver_path))

            try:
                driver.get(full_url)
                time.sleep(5)
            except Exception as e:
                print(f"[ERROR] No se pudo acceder: {full_url} - {e}")                
                self.articulo_errors.append(full_url)
                continue

            try:
                titulo = driver.find_element(By.TAG_NAME, 'h1').text
                if titulo == "":
                    el_titulo = driver.find_elements(By.TAG_NAME, 'h1')
                    if len(el_titulo) > 1:
                        titulo = el_titulo[1].text
            except NoSuchElementException:
                titulo = 'NONE'


            try:
                h2s = driver.find_elements(By.TAG_NAME, 'h2')
                h3s = driver.find_elements(By.TAG_NAME, 'h3')
                subtitulos = [elem.text.strip() for elem in h2s + h3s if elem.text.strip()]
                subtitulo = ' '.join(subtitulos) if subtitulos else 'NONE'
            except Exception:
                h2s = 'NONE'
                h3s = 'NONE'
                subtitulo = 'NONE'



            try:
                etiqueta = driver.find_elements(By.CSS_SELECTOR, ".cs_t_l, ._db, .a_k, ._df, .k, .kicker, .uppercase")

                if etiqueta:  # Verifica si se encontró al menos un elemento
                    etiqueta = etiqueta[0].text  # Obtiene el texto del primer elemento
                else:
                    etiqueta = "No encontrada etiqueta"
            except NoSuchElementException:
                etiqueta = 'NONE'

            try:
                #localizacion = driver.find_element(By.CSS_SELECTOR, '.capitalize color_black, .capitalize,.articulo-localizacion,.color_black').text
                localizacion = driver.find_element(By.XPATH, '//span[contains(@class, "capitalize") or contains(@class, "articulo-localizacion") or contains(@class, "color_black")]').text

            except NoSuchElementException:
                localizacion = 'No localizacion'

            try:
                # 1️⃣ Elementos <p> sin clase o con class=""
                parrafos_sin_clase = driver.find_elements(
                    By.CSS_SELECTOR,
                    'p:not([class]), p[class=""]'
                )

                # 2️⃣ Otros posibles contenedores del cuerpo del artículo
                contenedores_extra = driver.find_elements(
                    By.XPATH,
                    '//*[contains(@class, "articulo-cuerpo") or '
                    'contains(@class, "a_b") or '
                    'contains(@class, "article_body") or '
                    'contains(@class, "color_gray_dark") or '
                    'contains(@class, "a_c") or '
                    'contains(@class, "clearfix") or '
                    'contains(@class, "c_d")]'
                )

                # Combina ambas listas, eliminando duplicados
                elementos_contenido = list(dict.fromkeys(parrafos_sin_clase + contenedores_extra))

                articuloContenido = (
                    ' '.join(e.text.strip() for e in elementos_contenido if e.text.strip())
                    if elementos_contenido else
                    'No encontrado contenido'
                )

            except Exception as e:
                articuloContenido = f'No encontrado artículo ({e})'


            articulo = [titulo, subtitulo, etiqueta, localizacion, articuloContenido]
            df = pd.DataFrame({full_url: articulo})
            df.to_csv(f'articulos_x_procesar/{self.origen}/{self.origen}_{snap}_{count}.csv', index=False)
            count += 1
            driver.quit()

        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')

        if self.articulo_errors:
            pd.DataFrame({'': self.articulo_errors}).to_csv(
                f'log_ejecuciones/{self.origen}/articulosError{fecha}.csv', index=False)
