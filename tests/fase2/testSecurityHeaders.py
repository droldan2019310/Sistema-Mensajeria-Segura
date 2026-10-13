def test_nosniff_en_respuestas_de_api(cliente):
    for ruta in ("/", "/openapi.json", "/ruta-inexistente"):
        respuesta = cliente.get(ruta)
        assert respuesta.headers["X-Content-Type-Options"] == "nosniff"
