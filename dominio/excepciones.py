class EcoTechError(Exception):
    pass


class DatoInvalidoError(EcoTechError, ValueError):
    pass


class SalarioInvalidoError(DatoInvalidoError):
    pass


class HorasInvalidasError(DatoInvalidoError):
    pass


class RegistroDuplicadoError(EcoTechError):
    pass


class NoEncontradoError(EcoTechError):
    pass


class AccesoDenegadoError(EcoTechError):
    pass


class BaseDatosError(EcoTechError):
    pass


class ApiError(EcoTechError):
    pass


class ApiClienteError(ApiError):
    """Respuesta 4xx o URL mal formada: no tiene sentido reintentar."""


class ApiNoDisponibleError(ApiError):
    """Sin red, timeout, error 5xx o límite 429 agotado después de los reintentos."""


class RespuestaInvalidaError(ApiError):
    """La API respondió, pero el JSON no tiene la forma esperada."""


class SinDatosError(EcoTechError):
    pass
