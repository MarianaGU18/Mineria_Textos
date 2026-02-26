from text_mining_pipeline import TextMiningPipeline
"""
    =========================================================
    FUENTES DE NOTICIAS CONSULTADAS
    =========================================================
        ABC
            https://www.abc.es/noticias/violencia-de-genero/
            https://www.abc.es/noticias/mujeres/
            https://www.abc.es/noticias/violencia/
            https://www.abc.es/noticias/acoso/

        ElPais
            elpais.com/noticias/violencia-machista

        Publico
            https://www.abc.es/noticias/violencia-de-genero/
        
        La Razon
            https://www.larazon.es/tags/violencia-de-genero/
            https://www.larazon.es/tags/agresion/
        El Mundo
            https://www.elmundo.es/t/vi/violencia-de-genero.html
            https://www.elmundo.es/t/vi/violencia.html
"""
"""    
     ⚠️ IMPORTANTE:
        - Asegurate de usar una sección que agrupe noticias por temática.
            (por ejemplo: violencia, agresiones, acoso, etc.).

        - Cuanto más amplio sea el rango de fecha, mayor será el tiempo
          de ejecución del proceso (puede tardar varios minutos y horas).

        - Revisa archivo 'text_mining_pipeline.py' y verifica que las etiquetas 
         HTML configuradas coincida con la estructura del portal que quieres 
         analizar.

         Cada periódico puede usara clases y etiquetas distintas.
"""

#===========================================================
# CREACIÓN DEL PIPELINE
#===========================================================
# Crear instancia del pipeline indicando:
#   - sitio: URL base de la sección de noricias a analizar
#   - origen: nombre identificador que se usará para etiquetar los resultados
#   - from_date: fecha inicial (formato YYYMMDD)
#   - palabras_clave_path: ruta al archivo CSV con términos para filtrar artículos

pipeline = TextMiningPipeline(

    sitio="https://www.elmundo.es/t/vi/violencia.html", 
    origen="Prueba_ELMUNDO",
    from_date="20150101",
    to_date="20151231",

    palabras_clave_path="datos_base/Terminos.csv"
)
# ============================================================
#   EJECUCIÓN DEL PIPELINE PASO A PASO
# ============================================================   

#   Obtener snapshots históricos del sitio en el rango de fechas indicado
#       Consulta versiones archivadas del sitio
#pipeline.obtener_snapshots()

#   Filtrar las URLs encontras
#       Se eliminana enlaces irrelevantes y se conservan solo los articulo con potencial
#pipeline.filtrar_urls_relevantes()

#   Procesar los articulos finales
#       Se descarga el contenido, se limpia el texto y se aplican los filtros.
pipeline.procesar_articulos()
