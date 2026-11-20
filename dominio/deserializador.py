import math
from datetime import date

from dominio.datos_externos import Clima, Lugar, TipoCambio
from dominio.excepciones import NoEncontradoError, RespuestaInvalidaError
from dominio.validaciones import MONEDAS_SOPORTADAS


def _texto(valor, campo: str, maximo: int = 100) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise RespuestaInvalidaError(f"Falta el campo '{campo}' en la respuesta de la API.")
    return valor.strip()[:maximo]


def _numero(valor, campo: str, minimo: float, maximo: float) -> float:
    # bool es subclase de int en Python, por eso se descarta explícitamente
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise RespuestaInvalidaError(f"El campo '{campo}' no es un número.")
    if not math.isfinite(valor) or not minimo <= valor <= maximo:
        raise RespuestaInvalidaError(f"El campo '{campo}' está fuera del rango esperado.")
    return float(valor)


def _diccionario(valor, campo: str) -> dict:
    if not isinstance(valor, dict):
        raise RespuestaInvalidaError(f"La respuesta de la API no tiene la estructura esperada ('{campo}').")
    return valor


class DeserializadorClima:
    """Valida y convierte el JSON de Open-Meteo en objetos Lugar y Clima."""

    @staticmethod
    def lugar(datos) -> Lugar:
        datos = _diccionario(datos, "respuesta")
        resultados = datos.get("results")
        if not resultados:
            # la API de geocodificación omite "results" cuando no encuentra la ciudad
            raise NoEncontradoError("No se encontró esa ciudad. Revise el nombre o agregue el código de país.")
        if not isinstance(resultados, list):
            raise RespuestaInvalidaError("La respuesta de la API no tiene la estructura esperada ('results').")
        primero = _diccionario(resultados[0], "results[0]")
        return Lugar(
            nombre=_texto(primero.get("name"), "name"),
            pais=str(primero.get("country") or "").strip()[:60],
            codigo_pais=str(primero.get("country_code") or "").strip().upper()[:2],
            latitud=_numero(primero.get("latitude"), "latitude", -90, 90),
            longitud=_numero(primero.get("longitude"), "longitude", -180, 180),
        )

    @staticmethod
    def clima(datos, lugar: Lugar) -> Clima:
        datos = _diccionario(datos, "respuesta")
        actual = _diccionario(datos.get("current"), "current")
        return Clima(
            ciudad=lugar.nombre,
            pais=lugar.pais or lugar.codigo_pais,
            latitud=lugar.latitud,
            longitud=lugar.longitud,
            temperatura=_numero(actual.get("temperature_2m"), "temperature_2m", -90, 60),
            humedad=int(_numero(actual.get("relative_humidity_2m"), "relative_humidity_2m", 0, 100)),
            codigo_tiempo=int(_numero(actual.get("weather_code"), "weather_code", 0, 99)),
            fecha_api=_texto(actual.get("time"), "time"),
        )


class DeserializadorTipoCambio:
    """Valida y convierte el JSON de mindicador.cl en un objeto TipoCambio."""

    @staticmethod
    def tipo_cambio(datos, codigo_moneda: str) -> TipoCambio:
        datos = _diccionario(datos, "respuesta")
        if datos.get("codigo") != MONEDAS_SOPORTADAS[codigo_moneda]:
            raise RespuestaInvalidaError("La API devolvió un indicador distinto al solicitado.")
        serie = datos.get("serie")
        if not isinstance(serie, list) or not serie:
            raise RespuestaInvalidaError("La API no entregó valores para ese indicador.")
        ultimo = _diccionario(serie[0], "serie[0]")   # el primero es el más reciente
        try:
            fecha = date.fromisoformat(str(ultimo.get("fecha"))[:10]).isoformat()
        except ValueError:
            raise RespuestaInvalidaError("La fecha del tipo de cambio no es válida.") from None
        return TipoCambio(
            codigo=codigo_moneda,
            nombre=_texto(datos.get("nombre"), "nombre"),
            valor=_numero(ultimo.get("valor"), "valor", 0.0001, 1_000_000),
            fecha_valor=fecha,
        )
