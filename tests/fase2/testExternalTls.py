"""Prueba TLS real para la consulta del servicio externo."""

from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import ssl

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
import pytest

from src.api import main


class ServicioLocal(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"estado":"ok"}')

    def log_message(self, format, *args):
        pass


@pytest.fixture
def servidor_https(tmp_path):
    ahora = datetime.now(UTC)
    nombre_ca = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CA de prueba TLS")])
    clave_ca = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    certificado_ca = (
        x509.CertificateBuilder()
        .subject_name(nombre_ca)
        .issuer_name(nombre_ca)
        .public_key(clave_ca.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - timedelta(days=1))
        .not_valid_after(ahora + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(clave_ca, hashes.SHA256())
    )

    clave_servidor = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre_servidor = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    certificado_servidor = (
        x509.CertificateBuilder()
        .subject_name(nombre_servidor)
        .issuer_name(nombre_ca)
        .public_key(clave_servidor.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - timedelta(days=1))
        .not_valid_after(ahora + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .sign(clave_ca, hashes.SHA256())
    )

    ruta_ca = tmp_path / "ca.pem"
    ruta_certificado = tmp_path / "servidor.pem"
    ruta_clave = tmp_path / "servidor.key"
    ruta_ca.write_bytes(certificado_ca.public_bytes(serialization.Encoding.PEM))
    ruta_certificado.write_bytes(certificado_servidor.public_bytes(serialization.Encoding.PEM))
    ruta_clave.write_bytes(
        clave_servidor.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), ServicioLocal)
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto.load_cert_chain(ruta_certificado, ruta_clave)
    servidor.socket = contexto.wrap_socket(servidor.socket, server_side=True)
    hilo = Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()

    try:
        yield f"https://localhost:{servidor.server_port}", ruta_ca
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=2)


def test_certificado_no_confiable_es_rechazado(cliente, monkeypatch, servidor_https):
    url, _ = servidor_https
    monkeypatch.setattr(main, "URL_SALUD_EXTERNA", url)
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)

    respuesta = cliente.get("/salud/externa")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"detail": "Servicio externo no disponible"}


def test_certificado_confiable_sigue_funcionando(cliente, monkeypatch, servidor_https):
    url, ruta_ca = servidor_https
    monkeypatch.setattr(main, "URL_SALUD_EXTERNA", url)
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")
    monkeypatch.setenv("SSL_CERT_FILE", str(ruta_ca))

    respuesta = cliente.get("/salud/externa")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}
