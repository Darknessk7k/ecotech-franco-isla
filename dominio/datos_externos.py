from dataclasses import dataclass
from datetime import datetime, timezone

DESCRIPCION_TIEMPO = {
    0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
    45: "Niebla", 48: "Niebla con escarcha",
    51: "Llovizna ligera", 53: "Llovizna moderada", 55: "Llovizna intensa",
    56: "Llovizna helada", 57: "Llovizna helada intensa",
    61: "Lluvia ligera", 63: "Lluvia moderada", 65: "Lluvia intensa",
    66: "Lluvia helada", 67: "Lluvia helada intensa",
    71: "Nevada ligera", 73: "Nevada moderada", 75: "Nevada intensa", 77: "Granizo fino",
    80: "Chubascos ligeros", 81: "Chubascos moderados", 82: "Chubascos violentos",
    85: "Chubascos de nieve", 86: "Chubascos de nieve intensos",
    95: "Tormenta eléctrica", 96: "Tormenta con granizo", 99: "Tormenta con granizo fuerte",
}


@dataclass
class Lugar:
    nombre: str
    pais: str
    codigo_pais: str
    latitud: float
    longitud: float


@dataclass
class Clima:
    ciudad: str
    pais: str
    latitud: float
    longitud: float
    temperatura: float
    humedad: int
    codigo_tiempo: int
    fecha_api: str
    obtenido_en: str = ""

    @property
    def estado(self) -> str:
        return DESCRIPCION_TIEMPO.get(self.codigo_tiempo, "Condición desconocida")

    def recomendacion(self) -> str:
        if self.codigo_tiempo >= 51:
            return "Precipitaciones o tormenta: se recomienda reprogramar las actividades al aire libre."
        if self.codigo_tiempo in (45, 48):
            return "Visibilidad reducida: precaución en trabajos en terreno."
        if self.temperatura >= 35 or self.temperatura <= 0:
            return "Temperatura extrema: limitar el trabajo prolongado al aire libre."
        return "Condiciones adecuadas para trabajar en terreno."


@dataclass
class TipoCambio:
    codigo: str
    nombre: str
    valor: float          # cuántos pesos chilenos (CLP) vale 1 unidad de la moneda
    fecha_valor: str      # AAAA-MM-DD, fecha a la que corresponde el valor
    obtenido_en: str = ""


def ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _leer_momento(obtenido_en: str):
    momento = datetime.fromisoformat(obtenido_en)
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento


def describir_antiguedad(obtenido_en: str) -> str:
    try:
        momento = _leer_momento(obtenido_en)
    except (ValueError, TypeError):
        return "antigüedad desconocida"
    segundos = int((datetime.now(timezone.utc) - momento).total_seconds())
    if segundos < 60:
        return "hace menos de 1 minuto"
    minutos = segundos // 60
    if minutos < 60:
        return f"hace {minutos} min"
    horas = minutos // 60
    if horas < 48:
        return f"hace {horas} h"
    return f"hace {horas // 24} días"


def formatear_fecha_local(obtenido_en: str) -> str:
    try:
        return _leer_momento(obtenido_en).astimezone().strftime("%d-%m-%Y %H:%M")
    except (ValueError, TypeError):
        return obtenido_en
