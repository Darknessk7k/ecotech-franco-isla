import re
import unicodedata

from dominio.excepciones import DatoInvalidoError

# código que usa nuestro sistema -> código que usa la API de mindicador.cl
MONEDAS_SOPORTADAS = {"USD": "dolar", "EUR": "euro"}

PATRON_USUARIO = re.compile(r"[a-z0-9._-]{3,30}")
PATRON_CIUDAD = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'\-]{1,59}")
PATRON_PAIS = re.compile(r"[A-Z]{2}")
LARGO_MAXIMO_CLAVE = 72


def validar_ciudad(valor) -> str:
    if not isinstance(valor, str):
        raise DatoInvalidoError("La ciudad debe ser un texto.")
    texto = " ".join(valor.split())
    if not PATRON_CIUDAD.fullmatch(texto):
        raise DatoInvalidoError(
            "La ciudad solo puede tener letras, espacios, guion, punto y apóstrofe (2 a 60 caracteres)."
        )
    return texto


def validar_pais(valor) -> str:
    texto = str(valor or "").strip().upper()
    if texto == "":
        return ""
    if not PATRON_PAIS.fullmatch(texto):
        raise DatoInvalidoError("El país debe ser un código de 2 letras (ej: CL, AR, PE).")
    return texto


def validar_moneda(valor) -> str:
    texto = str(valor or "").strip().upper()
    if texto not in MONEDAS_SOPORTADAS:
        raise DatoInvalidoError(f"Moneda no soportada. Use una de: {', '.join(MONEDAS_SOPORTADAS)}.")
    return texto


def credenciales_validas(nombre: str, clave: str) -> bool:
    """Revisa el formato antes de consultar la base. Devuelve bool para no revelar qué falló."""
    if not isinstance(nombre, str) or not isinstance(clave, str):
        return False
    if not clave or len(clave.encode("utf-8")) > LARGO_MAXIMO_CLAVE:
        return False
    return PATRON_USUARIO.fullmatch(nombre.strip().lower()) is not None


def clave_busqueda(ciudad: str, pais: str) -> str:
    """Llave estable para guardar y encontrar una ciudad en la base (sin tildes ni mayúsculas)."""
    sin_tildes = unicodedata.normalize("NFKD", ciudad).encode("ascii", "ignore").decode("ascii")
    return f"{' '.join(sin_tildes.lower().split())}|{pais.upper()}"
