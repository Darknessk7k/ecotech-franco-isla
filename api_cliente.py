import logging
import os
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from dominio.excepciones import ApiClienteError, ApiNoDisponibleError, RespuestaInvalidaError

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

logger = logging.getLogger("ecotech.api")

ESPERA_MAXIMA = 30   # nunca esperar más de 30 s, aunque la API pida más en Retry-After


def _entero_env(nombre: str, defecto: int, minimo: int, maximo: int) -> int:
    try:
        valor = int(os.getenv(nombre, str(defecto)))
    except ValueError:
        valor = defecto
    return max(minimo, min(maximo, valor))


class ClienteAPI:
    """Cliente HTTP con timeout, reintentos con backoff exponencial y manejo por código de estado."""

    def __init__(self, timeout=None, max_intentos=None, espera_base=None):
        self.timeout = timeout if timeout is not None else _entero_env("API_TIMEOUT_SEGUNDOS", 8, 1, 30)
        self.max_intentos = max_intentos if max_intentos is not None else _entero_env("API_MAX_INTENTOS", 4, 1, 4)
        self.espera_base = espera_base if espera_base is not None else _entero_env("API_ESPERA_BASE_SEGUNDOS", 1, 0, 10)
        self._dormir = time.sleep
        self._sesion = requests.Session()   # la verificación del certificado TLS queda activada (verify=True)

    def obtener_json(self, url: str, parametros: dict = None):
        motivo = "sin detalle"
        for intento in range(1, self.max_intentos + 1):
            espera = self.espera_base * (2 ** (intento - 1))   # 1, 2, 4, 8 s
            try:
                respuesta = self._sesion.get(url, params=parametros, timeout=(self.timeout, self.timeout))
            except (requests.ConnectionError, requests.Timeout) as error:
                # error de red o tiempo agotado: se reintenta
                motivo = "sin conexión o tiempo de espera agotado"
                logger.warning("Intento %s/%s falló (%s) en %s", intento, self.max_intentos, type(error).__name__, url)
            except requests.RequestException as error:
                # URL mal formada, esquema no soportado, etc.: reintentar no sirve
                logger.error("Solicitud inválida (%s) en %s", type(error).__name__, url)
                raise ApiClienteError("La dirección del servicio externo no es válida.") from error
            else:
                codigo = respuesta.status_code
                if codigo == 200:
                    return self._leer_json(respuesta, url)
                if codigo == 429:
                    espera = self._leer_retry_after(respuesta, espera)
                    motivo = "límite de consultas alcanzado (429)"
                elif 500 <= codigo <= 599:
                    motivo = f"error del servidor ({codigo})"
                elif 400 <= codigo <= 499:
                    logger.error("La API respondió %s en %s", codigo, url)
                    raise ApiClienteError(f"El servicio externo rechazó la solicitud (código {codigo}).")
                else:
                    logger.error("Código inesperado %s en %s", codigo, url)
                    raise ApiClienteError(f"Respuesta inesperada del servicio externo (código {codigo}).")
                logger.warning("Intento %s/%s: %s en %s", intento, self.max_intentos, motivo, url)
            if intento < self.max_intentos:
                self._dormir(espera)
        raise ApiNoDisponibleError(f"El servicio externo no responde ({motivo}).")

    @staticmethod
    def _leer_json(respuesta, url: str):
        try:
            return respuesta.json()
        except ValueError as error:
            logger.error("JSON inválido recibido desde %s", url)
            raise RespuestaInvalidaError("El servicio externo devolvió datos con formato inesperado.") from error

    @staticmethod
    def _leer_retry_after(respuesta, espera_por_defecto: float) -> float:
        valor = respuesta.headers.get("Retry-After", "").strip()
        segundos = None
        if valor.isdigit():
            segundos = int(valor)
        elif valor:
            try:
                fecha = parsedate_to_datetime(valor)
                if fecha.tzinfo is None:
                    fecha = fecha.replace(tzinfo=timezone.utc)
                segundos = int((fecha - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError):
                segundos = None
        if segundos is None:
            return espera_por_defecto
        return max(0, min(segundos, ESPERA_MAXIMA))
