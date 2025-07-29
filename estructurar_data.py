"""
Procesamiento de noticias 
------------------------------------------------
• Extrae fechas, ubicaciones, delitos y país
• Funciona para El País (España) pero es fácilmente extensible a otros medios/países
• Salida: JSON con la estructura solicitada
"""
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
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
# Configuración de rutas y constantes
###############################################################################
DATA_ESP_PATH = Path("datos_base/DATA_ESP/data_ESP.csv")
ARTICLES_DIR = Path("articulos_x_procesar/PRUEBA_ELPAIS")
TERMS_CSV_PATH = Path("datos_base/Terminos.csv")
OUTPUT_DIR = Path("TFM")
OUTPUT_FILE = OUTPUT_DIR / "noticias_estandarizadas_ESP.json"
ORIGEN = "ElPaís"
eventos = []

def obtener_una_url(csv_file: Path) -> Optional[str]:
    df = pd.read_csv(csv_file, header=None)
    if not df.empty:
        return str(df.iloc[0, 0])
    return None

###############################################################################
# Función principal
###############################################################################

def main() -> None:
    # Validaciones básicas
    if not DATA_ESP_PATH.is_file():
        print(f"[ERROR] No existe {DATA_ESP_PATH}")
        sys.exit(1)
    if not ARTICLES_DIR.is_dir():
        print(f"[ERROR] No existe {ARTICLES_DIR}")
        sys.exit(1)
    if not TERMS_CSV_PATH.is_file():
        print(f"[ERROR] No existe {TERMS_CSV_PATH}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
 
    nlp = spacy.load("es_core_news_lg")

    # DataFrame de referencia
    df_depmun = pd.read_csv(DATA_ESP_PATH)
    municipios = set(df_depmun["MUNICIPIO"].str.lower())
    comunidades = set(df_depmun["COMUNIDAD"].str.lower())

    # Paises
    global PAIS_SET
    PAIS_SET = {c.name.lower() for c in pycountry.countries}
    # Alias conocidos
    PAIS_SET.update({"españa", "espana", "méxico", "eua", "turquía", "islandia", "brasil"})

    # Patrones de delitos
    patrones_delitos = obtener_palabras_clave(TERMS_CSV_PATH)

    for csv_file in ARTICLES_DIR.glob("*.csv"):
        # Estructura básica del evento
        filename = csv_file.stem.replace("PRUEBA_ELPAIS_", "")
        evento: Dict[str, object] = {
            "ID_noticia": f"ESP_{filename}",
            "diario": ORIGEN,
        }

        # Fecha desde nombre de archivo
        try:
            fecha_archivo = datetime.strptime(csv_file.name.split("_")[1], "%Y%m%d%H%M%S").strftime("%d/%m/%Y")
        except Exception:
            fecha_archivo = "None"

        # Leer texto
        df = pd.read_csv(csv_file)
        texto_completo = df.to_string()
        texto_lower = texto_completo.lower()

        # ---------------- Fechas ---------------- #
        evento["fecha"] = fechas_evento(fecha_archivo,evento,texto_lower)

        # ---------------- Delitos (token) ---------------- #
        conteo_delitos = {term: 0 for term in patrones_delitos}
        for termino, patron in patrones_delitos.items():
            conteo_delitos[termino] = len(re.findall(patron, texto_lower))
        evento["token"] = conteo_delitos

        # ---------------- NLP ---------------- #
        doc = nlp(texto_completo)
        doc.ents = [ent for ent in doc.ents if ent.label_ in {"LOC", "PER"}]


        # País
        pais_texto = detectar_pais_desde_texto(doc, PAIS_SET)
        url_articulo = obtener_una_url(csv_file)
        pais_url = detectar_pais(url_articulo,PAIS_SET) if url_articulo else None

        pais_texto_valido = pais_texto.lower() if pais_texto else None
        pais_url_valido = pais_url.lower() if pais_url else None

        if pais_texto_valido in {"españa", "espana"}:
            print("1")
            evento["país"] = "España"

        elif pais_url_valido in {"españa", "espana"}:
            print("2")
            evento["país"] = "España"

        elif pais_texto_valido and pais_texto_valido not in {"españa", "espana"}:
            print("3")
            if pais_texto_valido in PAIS_SET:
                evento["país"] = pais_texto
            else:
                evento["país"] = "No encontrado"

        elif pais_url_valido and pais_url_valido not in {"españa", "espana"}:
            print("4")
            evento["país"] = pais_url

        else:
            print("5")
            evento["país"] = "No encontrado"



        print("2 evento[país]:",  evento["país"])

        # Ubicaciones
        evento,municipio, comunidad, provincia = ubicacion_espana(
            doc, municipios, comunidades, df_depmun, evento)
        
        # Limpiar ubicación final
        ubicacion = ", ".join(part for part in [comunidad, municipio, provincia] if part)
        evento["ubicacion_noticia"] = ubicacion if ubicacion else "No especificada"

        
        #print("csv_file:", csv_file)
        #print("filename:", filename)
        #print("url_articulo:", url_articulo)
        print("1 evento[país]:",  evento["país"])
        #print("[comunidad, municipio, provincia]:",  [comunidad, municipio, provincia])
        #print("pais_url:",  pais_url)
        print("============================")
        eventos.append(evento)




  # ---------------- Guardar JSON ---------------- #
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(eventos, f, ensure_ascii=False, indent=4)
        print(f"[OK] Se generó {OUTPUT_FILE} con {len(eventos)} eventos")

###############################################################################
if __name__ == "__main__":
    main()
