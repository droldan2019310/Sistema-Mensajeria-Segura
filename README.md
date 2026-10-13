# Sistema de Mensajería Segura

Sistema local de mensajería segura desarrollado en Python con FastAPI, PostgreSQL, Docker y React. El proyecto implementa autenticación segura, cifrado híbrido, firmas digitales, blockchain simplificado y autenticación multifactor con TOTP.

---

## Objetivo General

Construir una aplicación de mensajería segura que permita registrar usuarios, proteger sus credenciales y llaves, intercambiar mensajes cifrados y firmados, verificar la integridad de los mensajes y registrar cada transacción en una mini blockchain, todo dentro de un entorno local y reproducible con Docker.

---

## Funcionalidades Implementadas

### Gestión de Identidad y Hashing

- Registro de usuarios con nombre, correo único y contraseña
- Hashing de contraseñas con Argon2id
- Generación automática de par de llaves RSA 2048
- Almacenamiento de llave pública en formato PEM
- Cifrado de llave privada con clave derivada usando PBKDF2HMAC y AES GCM
- Login con verificación de credenciales
- Emisión de JWT

### Cifrado Híbrido de Mensajes

- Cifrado individual con AES-256 GCM
- Cifrado de clave AES con RSA-OAEP
- Descifrado end-to-end
- Mensajería grupal con una clave AES compartida y cifrada por miembro
- Recuperación de mensajes descifrados desde API

### Firmas Digitales y Blockchain

- Firma digital del hash SHA-256 del mensaje
- Verificación de firma al recuperar mensajes
- Detección de firma inválida y alerta al usuario
- Mini blockchain con bloque génesis
- Encadenamiento de hashes
- Proof of work simplificado
- Registro automático de transacciones al enviar mensajes
- Verificación de integridad de la cadena

### MFA e Integración Final

- Activación de MFA con TOTP compatible con Google Authenticator
- Flujo de login con MFA
- Access token y refresh token
- Endpoints protegidos con JWT
- Frontend React para demostrar el flujo completo
- Despliegue local con Docker Compose

---

## Tecnologías Utilizadas

### Backend

- Python 3.12.10
- FastAPI
- SQLAlchemy
- PostgreSQL
- Argon2id
- Cryptography
- PyJWT
- PyOTP
- Qrcode

### Frontend

- React
- Vite
- JavaScript
- CSS

### Infraestructura

- Docker
- Docker Compose

---

## Estructura del Proyecto

```text
proyecto2/
├─ README.md
├─ docker-compose.app.yml
├─ docker-compose.sonarqube.yml
├─ Dockerfile
├─ requirements.txt
├─ pytest.ini
├─ docs/
│  ├─ arquitectura.md
│  └─ analisis.md
├─ src/
│  ├─ api/
│  ├─ auth/
│  ├─ users/
│  ├─ crypto/
│  ├─ signatures/
│  ├─ blockchain/
│  └─ frontend/
│     ├─ package.json
│     ├─ vite.config.js
│     ├─ index.html
│     └─ src/
│        ├─ App.jsx
│        ├─ main.jsx
│        ├─ styles.css
│        └─ servicios/
│           └─ api.js
└─ tests/
```

---

## Endpoints Principales

### Autenticación

| Método | Endpoint           |
| ------ | ------------------ |
| `POST` | `/auth/register`   |
| `POST` | `/auth/login`      |
| `POST` | `/auth/mfa/enable` |
| `POST` | `/auth/mfa/verify` |
| `POST` | `/auth/mfa/login`  |
| `POST` | `/auth/refresh`    |

### Usuarios

| Método | Endpoint              |
| ------ | --------------------- |
| `GET`  | `/users/{userId}/key` |

### Mensajes

| Metodo | Endpoint                     |
| ------ | ---------------------------- |
| `POST` | `/groups`                    |
| `POST` | `/messages/{destId}`         |
| `POST` | `/groups/{groupId}/messages` |
| `GET`  | `/messages/{userId}`         |

### Grupos

| Metodo | Endpoint                     |
| ------ | ---------------------------- |
| `POST` | `/groups`                    |
| `POST` | `/messages/{destId}`         |
| `POST` | `/groups/{groupId}/messages` |
| `GET`  | `/messages/{userId}`         |

### Blockchain

| Método | Endpoint             |
| ------ | -------------------- |
| `GET`  | `/blockchain`        |
| `GET`  | `/blockchain/verify` |

---

## Levantar el proyecto y SonarQube

Necesitas Docker Desktop abierto y Node.js instalado. Los dos archivos Compose
están en la raíz: `docker-compose.app.yml` levanta la API y su PostgreSQL;
`docker-compose.sonarqube.yml` levanta SonarQube y su propio PostgreSQL. Ejecuta
los comandos siguientes en **PowerShell**, desde la raíz del repositorio.

1. **Preparar la aplicación (solo la primera vez).** Si ya tienes `.env`, omite
   este paso. Si no, créalo y reemplaza `JWTClaveSecreta` y
   `BaseDatosPassword` por valores privados. No subas `.env` a Git.

   ```powershell
   Copy-Item .env.example .env
   ```

2. **Levantar la API y su base de datos.**

   ```powershell
   docker compose -f docker-compose.app.yml up -d --build
   ```

   Comprueba la API en **http://localhost:17841/docs**.

3. **Levantar el frontend.** En otra terminal PowerShell, desde la raíz:

   ```powershell
   cd src/frontend

   npm ci

   npm run dev
   ```

   Abre **http://localhost:18473**. Deja abierta esta terminal mientras uses
   el frontend.

4. **Levantar SonarQube.** En una terminal PowerShell situada en la raíz:

   ```powershell
   docker compose -f docker-compose.sonarqube.yml -p sonar-lab up -d
   ```

   Abre **http://localhost:9000**. En una instalación nueva, entra con
   `admin` / `admin` y cambia la contraseña; si ya lo configuraste, usa tu
   contraseña actual. `-p sonar-lab` conserva los datos de la instalación
   previa del laboratorio.

**Para detener todo:** pulsa `Ctrl+C` en la terminal del frontend. Desde la
raíz, ejecuta estos dos comandos; `down` no borra los volúmenes de datos:

```powershell
docker compose -f docker-compose.app.yml down

docker compose -f docker-compose.sonarqube.yml -p sonar-lab down
```

---

### Para conectarse a la base de datos desde cli en caso se necesite verificar algo

```bash
docker exec -it sistema_mensajeria_db psql -U postgres -d sistema_mensajeria_segura
```

## Flujo Recomendado para Probar el Sistema

### Prueba Básica Completa

1. Registrar dos usuarios
2. Iniciar sesión con uno de ellos
3. Activar MFA si se desea probar la fase 4 completa
4. Completar login con MFA
5. Enviar mensaje individual firmado y cifrado a otro usuario
6. Iniciar sesión con el destinatario
7. Recuperar mensajes
8. Verificar que el mensaje se descifra y la firma aparece como **verificada**
9. Consultar blockchain
10. Verificar integridad de la cadena

### Prueba Grupal

1. Registrar tres usuarios
2. Iniciar sesión con el creador
3. Crear grupo
4. Enviar mensaje grupal
5. Iniciar sesión con otro miembro
6. Recuperar mensajes
7. Confirmar que el mensaje grupal se descifra correctamente

---

## Cómo Ejecutar los Tests del código actual

Con los contenedores arriba, crear una sola vez una base local exclusiva para
tests (si ya existe, omitir `createdb`) y ejecutar. La cobertura de
Fase 2 se guarda donde SonarQube la buscará:

```powershell
New-Item -ItemType Directory -Force artifacts\fase2 | Out-Null

docker compose -f docker-compose.app.yml exec -T db createdb -U postgres sistema_mensajeria_segura_test

docker compose -f docker-compose.app.yml run --rm --no-deps -e BaseDatosNombre=sistema_mensajeria_segura_test api pytest -v --cov=src --cov-branch --cov-report=xml:artifacts/fase2/coverage.xml
```

Esto corre todos los tests de:

- Módulo 1
- Módulo 2
- Módulo 3
- Módulo 4

---

## Preparación del laboratorio

Haz estos pasos en **PowerShell, desde la raíz del repositorio**. Ya están
incluidos `docker-compose.sonarqube.yml`, `docker-compose.app.yml` y
`sonar-project.properties`. Este último tiene la clave del proyecto, la versión
`fase2`, las rutas del código y los tests, las exclusiones y las rutas de
`artifacts/fase2/coverage.xml` y `artifacts/fase2/semgrep.sarif`. No guarda
credenciales. `artifacts/` está ignorado por Git: tendrás que crear la carpeta
y generar esos dos archivos después de clonar el proyecto.

### 1. Levantar SonarQube y entrar por primera vez

Con Docker Desktop abierto, ejecuta:

```powershell
docker compose -f docker-compose.sonarqube.yml -p sonar-lab up -d
```

Abre `http://localhost:9000` y espera a que cargue. Si es la primera vez,
entra con `admin` / `admin` y cambia la contraseña cuando SonarQube lo pida.
Si ya habías usado `sonar-lab`, entra con la contraseña que configuraste antes.
El proyecto, el Quality Gate y el token se crean en la interfaz la primera vez.

### 2. Configurar el Quality Gate y el proyecto

1. En **Quality Gates**, crea **Curso Desarrollo Seguro** y elige
   **Actions → Set as default**. Usa las condiciones que se configuraron para
   este proyecto: 0 incidencias nuevas, cobertura de código nuevo de al menos
   70 %, duplicación nueva de hasta 3 % y 100 % de _Security Hotspots_ nuevos
   revisados. Comprueba que el proyecto muestre **Curso Desarrollo Seguro**
   como gate.
2. En **Projects → Create Project → Local Project**, crea el proyecto con la
   clave `sistema-mensajeria-segura` y el nombre **Sistema de Mensajeria
   Segura**. Usa esa misma clave porque así aparece en `sonar-project.properties`.
3. En **Project Settings → New Code**, elige **Previous version**. El análisis
   de Fase 1 es la línea base; la versión actual del archivo es `fase2`.

### 3. Generar el token de análisis

En SonarQube, abre el menú de tu usuario (arriba a la derecha) → **My Account**
→ **Security**. Selecciona un token de tipo **Project Analysis** para
`sistema-mensajeria-segura`, asígnale un nombre y pulsa **Generate**. Tu
usuario necesita el permiso **Execute Analysis** en ese proyecto. Copia el
valor en ese momento: SonarQube lo muestra una sola vez.
Si instalas SonarQube en otro equipo, genera allí un token nuevo. **No lo
guardes** en `.env`, `sonar-project.properties`, scripts, Git, capturas ni
reportes. En el paso 6 lo pegas cuando la terminal lo pida; al terminar, se
quita de esa sesión.

### 4. Generar la cobertura que importará SonarQube

Levanta la aplicación con el paso 2 de **Levantar el proyecto y SonarQube**.
Después crea la carpeta local de Fase 2 y la base de pruebas, si todavía no
existe, y ejecuta los tests:

```powershell
New-Item -ItemType Directory -Force artifacts\fase2 | Out-Null

docker compose -f docker-compose.app.yml exec -T db createdb -U postgres sistema_mensajeria_segura_test

docker compose -f docker-compose.app.yml run --rm --no-deps -e BaseDatosNombre=sistema_mensajeria_segura_test api pytest -v --cov=src --cov-branch --cov-report=xml:artifacts/fase2/coverage.xml
```

Si la base de pruebas ya existe, salta el comando `createdb`. El último crea
`artifacts/fase2/coverage.xml`; SonarQube ya no lee el `coverage.xml` de la raíz.
Usa siempre `sistema_mensajeria_segura_test` para estas pruebas porque los tests
limpian sus tablas. Comprueba que el archivo se haya creado:

```powershell
Test-Path artifacts\fase2\coverage.xml
```

Debe devolver `True`.

### 5. Generar `semgrep.sarif` con el código actual

La carpeta `artifacts/fase2/` no viene al clonar el repositorio. Si no la
creaste en el paso anterior, créala ahora. Necesitas Internet para descargar
las reglas de Semgrep:

```powershell
New-Item -ItemType Directory -Force artifacts\fase2 | Out-Null

docker run --rm -v "${PWD}:/src" -w /src semgrep/semgrep semgrep scan --config auto --sarif-output artifacts/fase2/semgrep.sarif src

Test-Path artifacts\fase2\semgrep.sarif
```

El último comando debe devolver `True`. `semgrep.sarif` guarda los resultados
del análisis, incluso si Semgrep no encuentra hallazgos. SonarScanner lo
importará en el paso siguiente. Genera uno nuevo cada vez que analices una
versión distinta del código.

### 6. Ejecutar SonarScanner e importar Semgrep

Con SonarQube abierto y los dos archivos de `artifacts/fase2/` listos, ejecuta
este bloque. Cuando aparezca **Pega el token de SonarQube**, pega el token que
generaste en el paso 3.

```powershell
if (-not (Test-Path artifacts\fase2\coverage.xml)) { throw "Falta la cobertura de Fase 2; ejecuta el paso 4." }

if (-not (Test-Path artifacts\fase2\semgrep.sarif)) { throw "Falta semgrep.sarif de Fase 2; ejecuta el paso 5." }

$tokenSeguro = Read-Host "Pega el token de SonarQube" -AsSecureString

$env:SONAR_TOKEN = [System.Net.NetworkCredential]::new("", $tokenSeguro).Password

try {
    docker run --rm `
        -e SONAR_TOKEN `
        -e SONAR_HOST_URL=http://host.docker.internal:9000 `
        -v "${PWD}:/usr/src" `
        sonarsource/sonar-scanner-cli:latest `
        -Dsonar.working.directory=/tmp/.scannerwork `
        -Dsonar.sarifReportPaths=artifacts/fase2/semgrep.sarif

    if ($LASTEXITCODE -ne 0) { throw "SonarScanner falló; revisa el error anterior." }
} finally {
    Remove-Item Env:SONAR_TOKEN -ErrorAction SilentlyContinue

    Remove-Variable tokenSeguro -ErrorAction SilentlyContinue
}
```

Al terminar, busca **ANALYSIS SUCCESSFUL** en la salida y revisa que la
importación del SARIF no tenga errores. Luego abre el proyecto en
`http://localhost:9000` y revisa el Quality Gate, la cobertura y las
incidencias. SonarQube puede tardar un momento en mostrar el análisis.
**ANALYSIS SUCCESSFUL** indica que recibió el análisis; consulta el dashboard
para saber si el gate pasó. Guarda `semgrep.sarif`, las auditorías de
dependencias, los reportes ZAP y las capturas para entregarlos aparte.

Para ZAP, usar el frontend `http://localhost:18473` y la definición OpenAPI
`http://localhost:17841/openapi.json` para el API scan. Registrar dos usuarios
de prueba después de correr los tests; iniciar sesión sin MFA con uno de ellos
y usar su `accessToken` como encabezado `Authorization: Bearer <token>` en las
peticiones autenticadas de ZAP. El token vence según `JWTMinutosExpiracion` en
`.env`, así que hay que renovarlo antes de un escaneo prolongado. Los datos y
tokens de prueba deben mantenerse fuera del repositorio y de las capturas.
