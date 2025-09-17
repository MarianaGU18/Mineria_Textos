from text_mining_pipeline import TextMiningPipeline

# Crear instancia con fechas de solo 1 día (para limitar la prueba)
pipeline = TextMiningPipeline(

    sitio="https://www.elmundo.es/t/vi/violencia.html", 
    origen="ELMUNDO_violencia",
    from_date="20240101",
    to_date="20250917",

    palabras_clave_path="datos_base/Terminos.csv"
)

# Ejecutar la tubería paso a paso (esto tomará unos minutos)
pipeline.obtener_snapshots()
pipeline.filtrar_urls_relevantes()
pipeline.procesar_articulos()

'''ABC
    abc.es/noticias/violencia-de-genero/
    https://www.abc.es/noticias/mujeres/
    https://www.abc.es/noticias/violencia/
    https://www.abc.es/noticias/acoso/
'''

''' ElPais
    sitio="elpais.com/noticias/violencia-machista",
    from_date="20200214",
    to_date="20250717",
'''

'''PUBLICO 
    #from_date="20180301",
    #to_date="20250812",
    #sitio="https://www.abc.es/noticias/violencia-de-genero/",
'''

'''LA RAZON
https://www.larazon.es/tags/violencia-de-genero/
https://www.larazon.es/tags/agresion/

'''

'''EL MUNDO
https://www.elmundo.es/t/vi/violencia-de-genero.html
https://www.elmundo.es/t/vi/violencia.html
'''