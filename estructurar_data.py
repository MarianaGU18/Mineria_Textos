"""
   =======================================================
        PROCESAMIENTO Y ESTANDARIZACIÓN DE NOTICIAS
   -----------------------------------------------------
    - Extrae fechas, ubicación, delitos y país.
    - Diseñado para noticias de España.
    - Fácilmente extensible a otros medios o países.
    - Salida final: archivo JSON estructurado.
   ========================================================

    """
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import pycountry
import spacy

from procesamiento_utils import (
    obtener_palabras_clave,
    fechas_evento,
    detectar_pais,
    detectar_pais_desde_texto,
    ubicacion_espana,
)
###############################################################################
# CONFIGURACIÓN GENERAL
###############################################################################

# ""Base de datos"" de municipios y comunidades de España
DATA_ESP_PATH = Path("datos_base/DATA_ESP/data_ESP.csv")

# Identificador del medio procesado
ORIGEN = "PUBLICO"

#Guardar version del dataset
GUARDAR_JSON_COMPLETO = True
GUARDAR_JSON_FILTRADO = True

# Carpeta donde están los articulos previamente scrapeados
ARTICLES_DIR = Path(f"articulos_x_procesar/{ORIGEN}")

# Archivo con términos de delitos
TERMS_CSV_PATH = Path("datos_base/Terminos.csv")

# Carpeta y nombre del JSON final
OUTPUT_DIR = Path("TFM")
OUTPUT_FILE = OUTPUT_DIR / f"noticias_estandarizadas_ESP_{ORIGEN}.json"

OUTPUT_FILTERED_DIR = Path("TFM_filtrado")
OUTPUT_FILTERED_FILE = OUTPUT_FILTERED_DIR / f"noticias_filtradas_ESP_{ORIGEN}.json"

# Lista donde se almacenarán todos los eventos procesados


###############################################################################
# FUNCIONES AUXILIARES
###############################################################################
def obtener_una_url(csv_file: Path) -> Optional[str]:
    """
    Obtiene la URL original almacenada en el CSV del artículo.
    Se asume que la URL está en la primera celda.
    """
    df = pd.read_csv(csv_file, header=None)
    if not df.empty:
        return str(df.iloc[0, 0])
    return None

###############################################################################
# FUNCIÓN PRINCIPAL
###############################################################################

def main() -> None:
    """
        Flujo principal:
            - Validar modelo NLP.
            - Cargar modelo NLP.
            - Preparar diccionarios de municipios, comunidades y países.
            - Recorrer cada artículo CSV.
            - Extraer:
                - Fecha
                - Delitos
                - País
                - Ubicación
            - Guardar todo en un JSON final.
    """
    eventos = []
    # ---------------------------------------
    # 1. VALIDACIONES BÁSICAS
    # ---------------------------------------
    if not DATA_ESP_PATH.is_file():
        print(f"[ERROR] No existe {DATA_ESP_PATH}")
        sys.exit(1)

    if not ARTICLES_DIR.is_dir():
        print(f"[ERROR] No existe {ARTICLES_DIR}")
        sys.exit(1)

    if not TERMS_CSV_PATH.is_file():
        print(f"[ERROR] No existe {TERMS_CSV_PATH}")
        sys.exit(1)

    # Crear carpetas de salida
    if GUARDAR_JSON_COMPLETO:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if GUARDAR_JSON_FILTRADO:
        OUTPUT_FILTERED_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------
    # 2. CARGAR MODELO NLP
    # ---------------------------------------
    nlp = spacy.load("es_core_news_lg")

    # ---------------------------------------
    # 3. CARGAR DATOS GEOGRÁFICOS DE REFERENCIA
    # ---------------------------------------
    df_depmun = pd.read_csv(DATA_ESP_PATH)
    municipios = set(df_depmun["MUNICIPIO"].str.lower())
    comunidades = set(df_depmun["COMUNIDAD"].str.lower())

    # ---------------------------------------
    # 4. LISTA DE PAÍSES
    # ---------------------------------------
    #global PAIS_SET
    PAIS_SET = {c.name.lower() for c in pycountry.countries}
    
    # Alias conocidos
    PAIS_SET.update({
        "españa", "espana", "méxico", "eua",
          "turquía", "islandia", "brasil"
        })

    # ---------------------------------------
    #   5. PATRONES DE DELITOS
    # ---------------------------------------
    patrones_delitos = obtener_palabras_clave(TERMS_CSV_PATH)
   
    # ---------------------------------------
    #   6. PROCESAR CADA ARTÍCULO
    # ---------------------------------------

    for csv_file in ARTICLES_DIR.glob("*.csv"):

        filename = csv_file.stem.replace(ORIGEN, "")

        evento: Dict[str, object] = {
            "ID_noticia": f"ESP_{filename}",
            "diario": ORIGEN,
        }

        # ---------------------------------------
        #   FECHA DESDE NOMBRE DE ARCHIVO
        # ---------------------------------------
        try:
            fecha_archivo = datetime.strptime(csv_file.name.split("_")[1], "%Y%m%d%H%M%S").strftime("%d/%m/%Y")

            #timestamp = re.search(r"\d{14}", csv_file.name).group()
            #fecha_archivo = datetime.strptime(timestamp, "%Y%m%d%H%M%S").strftime("%d/%m/%Y")
        except Exception:
            fecha_archivo = None

        # ---------------------------------------
        #   LEER CONTENIDO COMPLETO
        # ---------------------------------------
        df = pd.read_csv(csv_file)
        texto_completo = df.to_string()
        texto_lower = texto_completo.lower()

        # ---------------------------------------
        #   FECHA DEL EVENTO
        # ---------------------------------------
        evento["fecha"] = fechas_evento(
            fecha_archivo,
            evento,
            texto_lower
        )

        # ---------------------------------------
        #   DELITOS
        # ---------------------------------------
        conteo_delitos = {term: 0 for term in patrones_delitos}
        for termino, patron in patrones_delitos.items():
            conteo_delitos[termino] = len(
                re.findall(patron, texto_lower)
            )
        
        evento["conteo_delitos"] = conteo_delitos

        # ---------------------------------------
        #   NLP: DETECCIÓN DE ENTIDADES
        # ---------------------------------------
        doc = nlp(texto_completo)

        # Filtrar solo entidades relevantes
        doc.ents = [
            ent for ent in doc.ents 
            if ent.label_ in {"LOC", "PER"}
        ]

        # ---------------------------------------
        #   DETECCIÓN DE PAÍS
        # ---------------------------------------
        pais_texto = detectar_pais_desde_texto(doc, PAIS_SET)
        
        url_articulo = obtener_una_url(csv_file)
        pais_url = detectar_pais(url_articulo,PAIS_SET) if url_articulo else None

        pais_texto_valido = pais_texto.lower() if pais_texto else None
        pais_url_valido = pais_url.lower() if pais_url else None

        # Lógica jerárquica de decisión
        if pais_texto_valido in {"españa", "espana"}:
            evento["país"] = "España"

        elif pais_url_valido in {"españa", "espana"}:
            evento["país"] = "España"

        elif pais_texto_valido and pais_texto_valido not in {"españa", "espana"}:
            if pais_texto_valido in PAIS_SET:
                evento["país"] = pais_texto
            else:
                evento["país"] = "No encontrado"

        elif pais_url_valido and pais_url_valido not in {"españa", "espana"}:
            evento["país"] = pais_url

        else:
            evento["país"] = "No encontrado"

        # ----------------------------------
        # UBICACIÓN DENTRO DE ESPAÑA
        # ----------------------------------
        
        evento,municipio, comunidad, provincia = ubicacion_espana(
            doc, 
            municipios, 
            comunidades, 
            df_depmun, 
            evento
        )
        
        ubicacion = ", ".join(
            part for part in [comunidad, municipio, provincia] if part
        )

        evento["ubicacion_noticia"] = ubicacion if ubicacion else "No especificada"

        eventos.append(evento)

        # -----------------------------
        #  Eventos Filtrados
        # -----------------------------
        eventos_filtrados = []

        for e in eventos:
            delitos_detectados = {
                delito: valor
                for delito, valor in e["conteo_delitos"].items()
                if valor >=1
            }

            if delitos_detectados:
                evento_filtrado = e.copy()
                evento_filtrado["conteo_delitos"] = delitos_detectados
                eventos_filtrados.append(evento_filtrado)
        """
    for e in eventos_filtrados:
        e["conteo_delitos"] = {
            delito: valor
            for delito, valor in e["conteo_delitos"].items()
            if valor >= 1
        }
   """
    print("Total eventos:", len(eventos))
    print("Eventos filtrados:", len(eventos_filtrados))
    # -----------------------------
    #   7. GUARDAR JSON FINAL
    # -----------------------------
    # JSON completo
    if GUARDAR_JSON_COMPLETO:
        with OUTPUT_FILE.open("w", encoding="utf-8") as f:
            json.dump(eventos, f, ensure_ascii=False, indent=4)
            print(f"[OK] Se generó {OUTPUT_FILE} con {len(eventos)} eventos")

    # JSON filtrado
    if GUARDAR_JSON_FILTRADO:
        with OUTPUT_FILTERED_FILE.open("w", encoding="utf-8") as f:
            json.dump(eventos_filtrados, f, ensure_ascii=False, indent=4)

            print(f"[OK] Se generó {OUTPUT_FILTERED_FILE} con {len(eventos_filtrados)} eventos filtrados")

if __name__ == "__main__":
    main()
