import bcrypt

from dominio.excepciones import DatoInvalidoError

COSTO = 12          # rondas de bcrypt (2^12). Más alto = más lento de adivinar.
LARGO_MAXIMO = 72   # bcrypt solo usa los primeros 72 bytes de la clave


def generar_hash(clave: str) -> str:
    datos = clave.encode("utf-8")
    if len(datos) > LARGO_MAXIMO:
        raise DatoInvalidoError(f"La contraseña no puede superar {LARGO_MAXIMO} caracteres.")
    # gensalt() crea un salt aleatorio distinto para cada contraseña;
    # bcrypt lo deja guardado dentro del propio hash ($2b$12$<salt><hash>).
    return bcrypt.hashpw(datos, bcrypt.gensalt(rounds=COSTO)).decode("ascii")


def verificar_clave(clave: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(clave.encode("utf-8"), hash_guardado.encode("ascii"))
    except (ValueError, TypeError, AttributeError):
        # hash corrupto, clave demasiado larga o tipos incorrectos: se trata como clave incorrecta
        return False
