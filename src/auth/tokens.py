from datetime import UTC, datetime, timedelta

import jwt

from src.auth.configuracion import configuracion


# Genera un token jwt generico
def generarToken(datos: dict, minutosExpiracion: int, tipoToken: str) -> str:
    datosToken = datos.copy()

    fechaActual = datetime.now(UTC)
    fechaExpiracion = fechaActual + timedelta(minutes=minutosExpiracion)

    datosToken["exp"] = fechaExpiracion
    datosToken["iat"] = fechaActual
    datosToken["type"] = tipoToken

    return jwt.encode(
        datosToken, configuracion.JWTClaveSecreta, algorithm=configuracion.JWTAlgoritmo
    )


# Genera un access token
def generarTokenAcceso(datos: dict) -> str:
    return generarToken(
        datos=datos,
        minutosExpiracion=configuracion.JWTMinutosExpiracion,
        tipoToken="access",
    )


# Genera un refresh token
def generarTokenRefresh(datos: dict) -> str:
    return generarToken(
        datos=datos,
        minutosExpiracion=configuracion.JWTMinutosExpiracion * 24,
        tipoToken="refresh",
    )


# Decodifica y valida un jwt
def decodificarToken(token: str) -> dict:
    return jwt.decode(
        token,
        key=configuracion.JWTClaveSecreta,
        algorithms=[configuracion.JWTAlgoritmo],
        options={"require": ["exp", "iat", "sub", "type"]},
    )
