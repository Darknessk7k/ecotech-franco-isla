import logging
import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from api_cliente import ClienteAPI
from dominio.datos_externos import Clima, TipoCambio
from dominio.deserializador import DeserializadorClima, DeserializadorTipoCambio
from dominio.excepciones import (AccesoDenegadoError, ApiError, DatoInvalidoError,
                                 NoEncontradoError, SinDatosError)
from dominio.validaciones import (MONEDAS_SOPORTADAS, clave_busqueda, validar_ciudad,
                                  validar_moneda, validar_pais)
from repositorio.externo_repo import ClimaRepositorio, TipoCambioRepositorio

logger = logging.getLogger("ecotech.servicio")


@dataclass
class Resultado:
    datos: object
    en_vivo: bool          # True = vino de la API ahora; False = Plan B (base local)
    obtenido_en: str


@dataclass
class ResultadoPago:
    salario_clp: float
    moneda: str
    monto: Decimal
    cambio: Resultado


class ServicioExterno:
    """Une API + deserializador + base de datos. Nada se ejecuta sin sesión activa y permiso."""

    def __init__(self, cliente=None, clima_repo=None, cambio_repo=None):
        self.cliente = cliente or ClienteAPI()
        self.clima_repo = clima_repo or ClimaRepositorio()
        self.cambio_repo = cambio_repo or TipoCambioRepositorio()

    # ---------- control de acceso ----------
    @staticmethod
    def _exigir_acceso(usuario, modulo: str):
        if usuario is None or not usuario.sesion_activa():
            raise AccesoDenegadoError("Debe iniciar sesión para consultar servicios externos.")
        if not usuario.tiene_acceso(modulo):
            raise AccesoDenegadoError("Su rol no tiene permiso para esta función.")

    # ---------- URLs desde .env ----------
    @staticmethod
    def _url(nombre: str, defecto: str) -> str:
        return os.getenv(nombre, defecto)

    # ---------- clima ----------
    def consultar_clima(self, usuario, ciudad: str, pais: str = "") -> Resultado:
        self._exigir_acceso(usuario, "clima")
        ciudad = validar_ciudad(ciudad)
        pais = validar_pais(pais)
        clave = clave_busqueda(ciudad, pais)
        try:
            parametros = {"name": ciudad, "count": 1, "language": "es", "format": "json"}
            if pais:
                parametros["countryCode"] = pais
            geo = self.cliente.obtener_json(
                self._url("API_CLIMA_GEO_URL", "https://geocoding-api.open-meteo.com/v1/search"), parametros)
            lugar = DeserializadorClima.lugar(geo)
            datos = self.cliente.obtener_json(
                self._url("API_CLIMA_URL", "https://api.open-meteo.com/v1/forecast"),
                {"latitude": lugar.latitud, "longitude": lugar.longitud, "timezone": "auto",
                 "current": "temperature_2m,relative_humidity_2m,weather_code"})
            clima = DeserializadorClima.clima(datos, lugar)
            obtenido_en = self.clima_repo.guardar(clave, ciudad, pais, clima)
            return Resultado(clima, True, obtenido_en)
        except ApiError as error:
            logger.warning("Clima de '%s' desde la API falló: %s", ciudad, error)
            guardado = self.clima_repo.obtener(clave)
            if guardado is None:
                raise SinDatosError(
                    "No se pudo contactar el servicio de clima y no hay datos guardados de esa ciudad.") from error
            return Resultado(guardado, False, guardado.obtenido_en)

    # ---------- tipo de cambio ----------
    def consultar_cambio(self, usuario, moneda: str) -> Resultado:
        self._exigir_acceso(usuario, "pagos")
        moneda = validar_moneda(moneda)
        try:
            url = f"{self._url('API_CAMBIO_URL', 'https://mindicador.cl/api')}/{MONEDAS_SOPORTADAS[moneda]}"
            datos = self.cliente.obtener_json(url)
            cambio = DeserializadorTipoCambio.tipo_cambio(datos, moneda)
            obtenido_en = self.cambio_repo.guardar(cambio)
            return Resultado(cambio, True, obtenido_en)
        except ApiError as error:
            logger.warning("Tipo de cambio %s desde la API falló: %s", moneda, error)
            guardado = self.cambio_repo.obtener_ultimo(moneda)
            if guardado is None:
                raise SinDatosError(
                    "No se pudo contactar el servicio de tipo de cambio y no hay valores guardados.") from error
            return Resultado(guardado, False, guardado.obtenido_en)

    def calcular_pago(self, usuario, empleado, moneda: str) -> ResultadoPago:
        resultado = self.consultar_cambio(usuario, moneda)
        valor = Decimal(str(resultado.datos.valor))
        monto = (Decimal(str(empleado.salario)) / valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return ResultadoPago(empleado.salario, resultado.datos.codigo, monto, resultado)

    # ---------- actualización completa ----------
    def sincronizar(self, usuario) -> dict:
        """Actualiza monedas y ciudades configuradas. Se puede repetir sin duplicar filas."""
        self._exigir_acceso(usuario, "pagos")
        informe = {"cambios": [], "climas": [], "errores": []}
        for moneda in MONEDAS_SOPORTADAS:
            try:
                informe["cambios"].append((moneda, self.consultar_cambio(usuario, moneda)))
            except (ApiError, SinDatosError, DatoInvalidoError, NoEncontradoError) as error:
                informe["errores"].append(f"{moneda}: {error}")
        for texto in os.getenv("CIUDADES_SINCRONIZAR", "").split(","):
            texto = texto.strip()
            if not texto:
                continue
            ciudad, _, pais = texto.partition(":")
            try:
                informe["climas"].append((ciudad.strip(), self.consultar_clima(usuario, ciudad, pais)))
            except (ApiError, SinDatosError, DatoInvalidoError, NoEncontradoError) as error:
                informe["errores"].append(f"{ciudad.strip()}: {error}")
        informe["total_clima"] = self.clima_repo.contar()
        informe["total_cambio"] = self.cambio_repo.contar()
        return informe
