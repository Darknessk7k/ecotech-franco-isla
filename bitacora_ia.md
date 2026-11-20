# Bitácora de uso de IA - ES3 TI3021

**Estudiante:** Franco Isla  **Rama:** `e3/isla`  **Fecha:** 20-11-2026
**Herramienta:** Claude (Anthropic), chat web. Única IA usada en esta evaluación.

## 1. Prompts y qué generó la IA

| N° | Prompt (resumen) | Qué generó la IA |
|----|------------------|------------------|
| 1 | Entregué el enunciado de la ES3, la guía del docente, la rúbrica y mi proyecto EcoTech de la ES2, y pedí un paso a paso para extenderlo. | Plan de trabajo y el código nuevo: `api_cliente.py`, `servicio_externo.py`, `dominio/deserializador.py`, `dominio/datos_externos.py`, `dominio/validaciones.py`, `repositorio/externo_repo.py`, tablas `clima` y `tipo_cambio`, cambios en `main.py`, `seguridad.py` y `usuario.py`, y pruebas automáticas. |

APIs elegidas (ambas gratuitas y sin llave): **Open-Meteo** (clima, con geocodificación) y **mindicador.cl** (dólar y euro en pesos chilenos).

## 2. Cómo funciona el código sugerido (lo que debo poder explicar)

- **`ClienteAPI.obtener_json`**: hace `GET` con `timeout=(8, 8)` explícito. Si hay error de red o timeout, o la API responde 5xx, espera 1, 2, 4 s (backoff exponencial) y reintenta, hasta 4 intentos. Si responde 429, espera lo que diga `Retry-After` (máximo 30 s). Si responde otro 4xx, lanza `ApiClienteError` sin reintentar, porque repetir una solicitud mal hecha no la arregla.
- **Deserializadores**: reciben el JSON crudo y lo convierten en objetos `Clima`, `Lugar` y `TipoCambio`, comprobando que cada campo exista, tenga el tipo correcto y esté en un rango razonable (ej. humedad 0-100). Si algo falla lanzan `RespuestaInvalidaError`.
- **Plan B**: `ServicioExterno` captura los errores de la API y, si hay datos guardados, los muestra con su `obtenido_en` y antigüedad. Si no hay nada guardado, muestra un mensaje claro (nunca una pantalla vacía ni un traceback).
- **Persistencia idempotente**: `INSERT ... ON CONFLICT DO UPDATE` sobre columnas `UNIQUE`; ejecutar dos veces actualiza la fila en vez de duplicarla. Todas las consultas usan `?`.
- **Seguridad**: contraseñas con `bcrypt` (el salt aleatorio queda dentro del hash), login con validación de formato y 3 intentos, sesión con expiración por inactividad, y cada función de API exige sesión activa y permiso de rol.

## 3. Auditoría de las 5 señales de riesgo

Revisé el código final con `grep` sobre todo el proyecto, con `bandit` (0 hallazgos, 1655 líneas) y comprobando cada dependencia en PyPI.

| # | Señal de riesgo | Cómo lo revisé | Resultado | Decisión |
|---|-----------------|----------------|-----------|----------|
| 1 | f-strings / concatenación en SQL | `grep` de `f"`, `.format(`, `%` y `+` dentro de `execute`/`ejecutar`/`consultar`; bandit B608 | 0 casos. Todo SQL usa `?` con tupla de parámetros (incluye el `UPSERT`). El `LIKE` de búsqueda usa `'%' \|\| ? \|\| '%'`. | **Descartado** el patrón inseguro; mantenido el estilo parametrizado de la ES2. |
| 2 | `verify=False` | `grep "verify"` | 0 casos. `requests.Session()` verifica el certificado TLS por defecto. | **Descartado.** Es el "arreglo rápido" típico de errores SSL, pero deja la conexión expuesta a un atacante intermedio. |
| 3 | `except: pass` / excepciones tragadas | `grep` de `except:` y `except ...: pass` | 0 casos. Los `pass` encontrados son cuerpos de clases de excepciones y métodos abstractos. Cada `except` captura un tipo concreto y lanza una excepción propia, o registra en `logs/ecotech.log`. | **Modificado.** Dejé un único `except Exception` de último recurso en `ejecutar_accion` y `main`, que registra el detalle con `logger.exception` y muestra un mensaje genérico. `EOFError` se relanza para no ocultarlo. |
| 4 | Llamadas sin `timeout` | `grep` de `requests.get`/`_sesion.get` | Hay una sola llamada HTTP en todo el proyecto (`api_cliente.py`) y siempre lleva `timeout`. | **Aceptado**, con `timeout` configurable en `.env` entre 1 y 30 s. |
| 5 | Librerías inexistentes en PyPI | `pip index versions` de cada paquete de `requirements.txt` | `requests 2.32.3`, `bcrypt 4.2.1` y `python-dotenv 1.0.1` existen en PyPI. No hay otros paquetes de terceros. | **Aceptado.** Versiones fijadas (`==`) para no instalar por error un paquete falso con nombre parecido. |

## 4. Qué acepté, modifiqué y descarté (con justificación técnica)

**Aceptado**
- Estructura en capas de la ES2 (dominio sin SQL, repositorio con SQL), porque ya estaba probada.
- Open-Meteo y mindicador.cl: no requieren llave, así no hay secretos de API que proteger ni filtrar. Las URLs, timeouts y reintentos igual van en `.env`.

**Modificado**
- **PBKDF2 (ES2) -> bcrypt:** la guía exige `bcrypt` o `argon2`. bcrypt es lento a propósito (costo 12) y guarda el salt en el hash. Se limita la clave a 72 bytes porque bcrypt ignora el resto.
- **`Retry-After` limitado a 30 s:** sin tope, una API defectuosa podría dejar el programa esperando mucho tiempo.
- **Máximo de intentos limitado a 1-4 desde `.env`:** evita reintentos infinitos por una mala configuración.
- **Validación con lista blanca (regex) en vez de lista negra:** la ciudad solo admite letras, espacios, guion, punto y apóstrofe. Bloquea `;`, `--`, `<`, comillas y similares sin intentar adivinar cada ataque.
- **Mensajes de error genéricos hacia el usuario**; detalles técnicos y URL consultadas solo en `logs/ecotech.log` (ignorado por Git).
- **Nombre de usuario** restringido a `[a-z0-9._-]{3,30}`, igual que la validación del login.
- Durante las pruebas se detectó que el `except Exception` general ocultaba el cierre de la entrada (`EOFError`); se corrigió.

**Descartado**
- Guardar un historial con una fila nueva por cada consulta: duplicaría registros en cada ejecución y rompería la idempotencia. Se usa `UPSERT`.
- Reintentar los errores 4xx: no se arreglan solos y solo gastarían cuota de la API.
- Mostrar la excepción original de `requests` al usuario: puede revelar URLs y detalles internos.
- Usar una API de pago con llave (ej. OpenWeatherMap): no era necesario y agregaba riesgo de filtrar la llave.

## 5. Evidencia de pruebas

- `python -m pruebas.prueba_api_cliente`: 19 pruebas contra un servidor local simulado. Cubren 200, 404 sin reintento, 5xx con backoff 1-2-4 s, 429 con `Retry-After`, sin red, timeout, URL mal formada, JSON inválido, Plan B, ciudad inexistente, entradas maliciosas, acceso sin sesión, idempotencia y hash bcrypt con salt distinto.
- `python main.py --sincronizar` ejecutado dos veces: los conteos de `clima` y `tipo_cambio` no cambian.
- Tabla `usuario`: todos los `password_hash` empiezan con `$2b$12$` (ninguna clave en texto plano).

## 6. Mis observaciones personales

Usé Claude para armar la extensión de la ES3 sobre mi proyecto de la ES2, y después fui probando las cosas yo mismo en mi PC. Corrí las pruebas y el --sincronizar dos veces para ver que no se duplicaran datos.

Lo que más cambié fue la contraseña: en la ES2 usaba PBKDF2 y ahora uso bcrypt porque lo pide la guía. También entendí que no se reintentan los errores 4xx porque repetir la misma petición mal hecha da el mismo error, en cambio con los 5xx o si se cae la red sí tiene sentido.

Lo que me costó fue entender cómo funciona el Plan B y el UPSERT (ON CONFLICT) para que no se dupliquen los registros. Revisé el código buscando las 5 señales de riesgo y no encontré ninguna, pero igual dejé fijadas las versiones en requirements.txt.

Me faltó probar más casos con las APIs reales, porque las pruebas automáticas usan un servidor falso.
