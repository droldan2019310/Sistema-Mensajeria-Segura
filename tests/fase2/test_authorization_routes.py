"""Pruebas de autorización y errores seguros en mensajes y grupos."""

import pytest

from src.crypto import rutas as crypto_routes


def authorization(cliente):
    response = cliente.post(
        "/auth/login",
        json={"email": "a@correo.com", "password": "ClaveSegura123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def test_no_se_puede_actuar_en_nombre_de_otro_usuario(cliente, usuariosPrueba, uuidInexistente):
    user_a = usuariosPrueba["a"]["id"]
    user_b = usuariosPrueba["b"]["id"]
    headers = authorization(cliente)

    responses = [
        cliente.post(
            "/groups",
            json={"nombre": "Ajeno", "creadoPor": user_b, "miembrosIds": [user_a]},
            headers=headers,
        ),
        cliente.post(
            f"/messages/{user_b}",
            json={
                "senderId": user_b,
                "senderPassword": "ClaveSegura123",
                "plaintext": "No autorizado",
            },
            headers=headers,
        ),
        cliente.post(
            f"/groups/{uuidInexistente}/messages",
            json={
                "senderId": user_b,
                "senderPassword": "ClaveSegura123",
                "plaintext": "No autorizado",
            },
            headers=headers,
        ),
        cliente.get(
            f"/messages/{user_b}?password=ClaveSegura123",
            headers=headers,
        ),
    ]

    assert [response.status_code for response in responses] == [403, 403, 403, 403]
    assert all("otro usuario" in response.json()["detail"] for response in responses)


def test_grupo_con_miembro_inexistente_no_se_crea(cliente, usuariosPrueba, uuidInexistente):
    response = cliente.post(
        "/groups",
        json={
            "nombre": "Grupo inválido",
            "creadoPor": usuariosPrueba["a"]["id"],
            "miembrosIds": [uuidInexistente],
        },
        headers=authorization(cliente),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Uno o mas miembros no existen"


def test_clave_incorrecta_no_envia_mensaje_individual(cliente, usuariosPrueba):
    response = cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveIncorrecta999",
            "plaintext": "No debe almacenarse",
        },
        headers=authorization(cliente),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No fue posible firmar y enviar el mensaje"


def test_no_se_envia_mensaje_a_grupo_inexistente(cliente, usuariosPrueba, uuidInexistente):
    response = cliente.post(
        f"/groups/{uuidInexistente}/messages",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "No debe almacenarse",
        },
        headers=authorization(cliente),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "El grupo no existe"


def test_clave_incorrecta_no_envia_mensaje_grupal(cliente, usuariosPrueba):
    headers = authorization(cliente)
    creator = usuariosPrueba["a"]["id"]
    group = cliente.post(
        "/groups",
        json={
            "nombre": "Grupo protegido",
            "creadoPor": creator,
            "miembrosIds": [usuariosPrueba["b"]["id"]],
        },
        headers=headers,
    )
    assert group.status_code == 201

    response = cliente.post(
        f"/groups/{group.json()['groupId']}/messages",
        json={
            "senderId": creator,
            "senderPassword": "ClaveIncorrecta999",
            "plaintext": "No debe almacenarse",
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No fue posible firmar y enviar el mensaje grupal"


@pytest.mark.parametrize(
    ("reason", "status_code"),
    [("Usuario no encontrado", 404), ("Datos de mensaje inválidos", 400)],
)
def test_errores_de_recuperacion_no_exponen_mensajes(
    cliente, usuariosPrueba, monkeypatch, reason, status_code
):
    def fail_recovery(**_kwargs):
        raise ValueError(reason)

    monkeypatch.setattr(crypto_routes, "recuperarMensajesDescifradosUsuario", fail_recovery)
    response = cliente.get(
        f"/messages/{usuariosPrueba['a']['id']}?password=ClaveSegura123",
        headers=authorization(cliente),
    )

    assert response.status_code == status_code
    assert response.json()["detail"] == reason


def test_salud_de_base_de_datos_responde_sin_revelar_credenciales(cliente):
    response = cliente.get("/salud/db")

    assert response.status_code == 200
    assert response.json() == {"estado": "ok", "baseDatos": "conectada"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
