import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import unicodedata
import pandas as pd
import pycountry
import spacy
import tldextract

# spaCy para detección país desde texto
nlp = spacy.load("es_core_news_lg")

###############################################################################
# Expresiones regulares de fechas
###############################################################################

REGEX_TEXTO = r"\b\d{1,2}\sde\s(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s(?:de|del)\s\d{4}\b"

REGEX_MES_ANTES = r"\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s\d{1,2},?\s\d{4}\b"
# dd/mm/yyyy o dd-mm-yyyy
REGEX_NUM = r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
# yyyy-mm-dd o yyyy/mm/dd
REGEX_ISO = r"\b\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\b"
REGEX_FECHAS = [REGEX_TEXTO, REGEX_MES_ANTES, REGEX_NUM, REGEX_ISO]

MESES = {
    "enero": 1, "ene": 1, "febrero": 2, "feb": 2,
    "marzo": 3, "mar": 3, "abril": 4, "abr": 4,
    "mayo": 5, "may": 5, "junio": 6, "jun": 6,
    "julio": 7, "jul": 7, "agosto": 8, "ago": 8,
    "septiembre": 9, "sep": 9, "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11, "diciembre": 12, "dic": 12,
}

def normalizar(texto: str) -> str:
    # Elimina acentos y normaliza espacios
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

def convertir_a_fecha(fecha_str: str) -> Optional[str]:
    fecha_str = fecha_str.strip()
    for regex in REGEX_FECHAS:
        m = re.search(regex, fecha_str, flags=re.IGNORECASE)
        if not m:
            continue
        token = m.group()
        try:
            if regex == REGEX_TEXTO:
                dia = int(re.search(r"\d{1,2}", token).group())
                mes_txt = re.search(r"[a-záéíóúñ]+", token, flags=re.IGNORECASE).group().lower()
                anio = int(re.search(r"\d{4}", token).group())
                mes = MESES[mes_txt]
            elif regex == REGEX_MES_ANTES:
                mes_txt = re.search(r"[a-záéíóúñ]+", token, flags=re.IGNORECASE).group().lower()
                dia = int(re.search(r"\d{1,2}", token).group())
                anio = int(re.search(r"\d{4}", token).group())
                mes = MESES[mes_txt]
            else:
                partes = list(map(int, re.split(r"[-/]", token)))
                candidatos = []
                for orden in [(0, 1, 2), (2, 1, 0), (1, 0, 2)]:
                    try:
                        d, m, y = partes[orden[0]], partes[orden[1]], partes[orden[2]]
                        if y < 100:
                            y += 2000
                        candidatos.append(datetime(y, m, d))
                    except ValueError:
                        continue
                if candidatos:
                    fecha_obj = sorted(candidatos)[0]
                    return fecha_obj.strftime("%d/%m/%Y")
                return None
            if anio < 100:
                anio += 2000
            fecha_obj = datetime(anio, mes, dia)
            return fecha_obj.strftime("%d/%m/%Y")
        except Exception:
            return None
    return None

def fechas_evento(fecha_archivo, evento, texto_lower):
    fechas_detectadas: List[str] = []
    for reg in REGEX_FECHAS:
        fechas_detectadas.extend(re.findall(reg, texto_lower))
    fechas_detectadas = list(set(fechas_detectadas))
    fechas_convertidas = [f for f in (convertir_a_fecha(f) for f in fechas_detectadas) if f]
    if fechas_convertidas:
        fecha_evento = min(fechas_convertidas, key=lambda f: datetime.strptime(f, "%d/%m/%Y"))
    else:
        fecha_evento = fecha_archivo
    return fecha_evento

def obtener_palabras_clave(path: Path) -> Dict[str, str]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        terms: List[str] = []
        for rows in reader:
            terms.extend(rows[0].split(","))
    return {t.strip().lower(): re.escape(t.strip().lower()) for t in terms if t.strip()}

def verificar_localizacion(localizacion: str, municipios: set[str], comunidades: set[str]) -> str:
    loc = localizacion.lower().strip()

    if loc in municipios:
        return "MUNICIPIO"
    if loc in comunidades:
        return "COMUNIDAD"
    return "NO_ENCONTRADO"

def obtener_comunidad(municipio: str, df_depmun: pd.DataFrame) -> str:
    municipio = normalizar(municipio)
    df = df_depmun.copy()
    df["MUNICIPIO_NORM"] = df["MUNICIPIO"].astype(str).apply(normalizar)
    fila = df[df["MUNICIPIO_NORM"] == municipio]
    return fila.iloc[0]["COMUNIDAD"] if not fila.empty else "Sin especificar comunidad"

def obtener_provincia(comunidad: str, df_depmun: pd.DataFrame) -> str:
    comunidad = normalizar(comunidad)
    df = df_depmun.copy()
    df["COMUNIDAD_NORM"] = df["COMUNIDAD"].astype(str).apply(normalizar)
    fila = df[df["COMUNIDAD_NORM"] == comunidad]
    return fila.iloc[0]["PROVINCIA"] if not fila.empty else "Sin especificar provincia"


def ubicacion_espana(doc, municipios, comunidades, df_depmun, evento):
    municipio = ""
    comunidad = ""
    provincia = ""

    for ent in doc.ents:
        if ent.label_ in ["LOC", "GPE"]:  # GPE ayuda a detectar regiones y países
            loc = ent.text
            tipo = verificar_localizacion(loc, municipios, comunidades)

            #print(f"Entidad detectada: '{ent.text}' | Normalizada: '{normalizar(loc)}' | Tipo: {tipo}")

            if tipo == "MUNICIPIO" and not municipio:
                municipio = ent.text
                comunidad = obtener_comunidad(loc, df_depmun)
                provincia = obtener_provincia(comunidad, df_depmun)

            elif tipo == "COMUNIDAD" and not comunidad and not municipio:
                comunidad = ent.text
                provincia = obtener_provincia(loc, df_depmun)

    # Si se detecta al menos una ubicación válida de España, actualiza el país
    if any([municipio, comunidad, provincia]):
        evento["país"] = "España"

    return evento, comunidad, provincia, municipio



def detectar_pais_desde_texto(doc, paises: set[str]) -> Optional[str]:
    #lineas = doc.text.splitlines()[:6]
    #doc_corto = nlp("\n".join(lineas))
    for ent in doc.ents:
        if ent.label_ == "LOC":
            texto = ent.text.lower()
            if texto in paises:
                try:
                    return pycountry.countries.lookup(texto).name
                except LookupError:
                    return ent.text.title()
    return None

def detectar_pais(url: str, paises: set[str]) -> Optional[str]:
    if not url:
        return None
    ext = tldextract.extract(url)
    dominio = ext.domain.lower()
    subdominio = ext.subdomain.lower()
    path = url.lower()
    for pais in paises:
        if pais in dominio or pais in subdominio or pais in path:
            return pais.title()
    return None
