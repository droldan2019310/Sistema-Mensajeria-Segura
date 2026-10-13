"""Regresiones de seguridad para la validación de access y refresh tokens."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.auth.configuracion import configuracion
from src.auth.dependencias import obtenerTokenActual
from src.auth.servicio import refrescarSesionUsuario
from src.auth.tokens import decodificarToken, generarTokenAcceso, generarTokenRefresh


@pytest.fixture(autouse=True)
def limpiarBaseDatos():
    """Estos tests no usan la base de datos ni deben activar su fixture global."""
    pass


def crear_token(tipo="access", clave=None, algoritmo=None, expira_en=5, headers=None):
    ahora = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": "usuario-de-prueba",
            "email": "prueba@example.invalid",
            "displayName": "Prueba",
            "type": tipo,
            "iat": ahora,
            "exp": ahora + timedelta(minutes=expira_en),
        },
        clave if clave is not None else configuracion.JWTClaveSecreta,
        algorithm=algoritmo or configuracion.JWTAlgoritmo,
        headers=headers,
    )


def test_token_de_otra_clave_no_autoriza_acceso():
    token = crear_token(clave="clave-de-prueba-distinta-de-mas-de-32-bytes")
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as error:
        obtenerTokenActual(credenciales)

    assert error.value.status_code == 401


def test_refresh_firmado_con_otra_clave_no_crea_sesion():
    token = crear_token(tipo="refresh", clave="clave-de-prueba-distinta-de-mas-de-32-bytes")

    with pytest.raises(jwt.InvalidTokenError):
        refrescarSesionUsuario(token)


@pytest.mark.parametrize(
    "token",
    [
        lambda: crear_token(expira_en=-5),
        lambda: crear_token(algoritmo="HS384"),
    ],
)
def test_token_vencido_o_de_algoritmo_inesperado_se_rechaza(token):
    token_preparado = token()
    with pytest.raises(jwt.InvalidTokenError):
        decodificarToken(token_preparado)


def test_token_sin_expiracion_se_rechaza():
    token = jwt.encode(
        {"sub": "usuario-de-prueba", "iat": datetime.now(UTC), "type": "access"},
        configuracion.JWTClaveSecreta,
        algorithm=configuracion.JWTAlgoritmo,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decodificarToken(token)


def test_extension_crit_desconocida_se_rechaza():
    token = crear_token(headers={"crit": ["politica-desconocida"], "politica-desconocida": True})

    with pytest.raises(jwt.InvalidTokenError):
        decodificarToken(token)


def test_tokens_legitimos_siguen_funcionando():
    datos = {"sub": "usuario-de-prueba", "email": "prueba@example.invalid", "displayName": "Prueba"}

    assert decodificarToken(generarTokenAcceso(datos))["type"] == "access"
    assert decodificarToken(generarTokenRefresh(datos))["type"] == "refresh"
