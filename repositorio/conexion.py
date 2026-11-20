import os
import sqlite3

from dotenv import load_dotenv

from dominio.excepciones import BaseDatosError, DatoInvalidoError, RegistroDuplicadoError

CARPETA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_SCHEMA = os.path.join(CARPETA_PROYECTO, "datos", "schema.sql")

load_dotenv(os.path.join(CARPETA_PROYECTO, ".env"))


def ruta_bd() -> str:
    ruta = os.getenv("ECOTECH_DB_PATH", "datos/ecotech.db")
    if not os.path.isabs(ruta):
        ruta = os.path.join(CARPETA_PROYECTO, ruta)
    return ruta


def obtener_conexion() -> sqlite3.Connection:
    try:
        conexion = sqlite3.connect(ruta_bd(), timeout=5)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion
    except sqlite3.Error as error:
        raise BaseDatosError(f"No se pudo conectar a la base de datos: {error}") from error


def inicializar_bd():
    try:
        with open(RUTA_SCHEMA, encoding="utf-8") as archivo:
            script = archivo.read()
    except OSError as error:
        raise BaseDatosError(f"No se encontró el archivo schema.sql: {error}") from error
    conexion = obtener_conexion()
    try:
        conexion.executescript(script)
        conexion.commit()
    except sqlite3.Error as error:
        raise BaseDatosError(f"Error al crear las tablas: {error}") from error
    finally:
        conexion.close()


def traducir_error(error: sqlite3.Error) -> Exception:
    mensaje = str(error)
    if isinstance(error, sqlite3.IntegrityError):
        if "UNIQUE" in mensaje:
            return RegistroDuplicadoError("Ya existe un registro con ese dato único (usuario, correo o nombre).")
        if "FOREIGN KEY" in mensaje:
            return DatoInvalidoError("El registro relacionado no existe o tiene datos asociados.")
        if "CHECK" in mensaje:
            return DatoInvalidoError("Un valor no cumple las reglas de la base de datos.")
        return DatoInvalidoError(f"Error de integridad: {mensaje}")
    return BaseDatosError(f"Error de base de datos: {mensaje}")


def ejecutar(sql: str, parametros: tuple = ()) -> sqlite3.Cursor:
    conexion = obtener_conexion()
    try:
        with conexion:
            cursor = conexion.execute(sql, parametros)
        return cursor
    except sqlite3.Error as error:
        raise traducir_error(error) from error
    finally:
        conexion.close()


def consultar(sql: str, parametros: tuple = ()) -> list:
    conexion = obtener_conexion()
    try:
        return conexion.execute(sql, parametros).fetchall()
    except sqlite3.Error as error:
        raise traducir_error(error) from error
    finally:
        conexion.close()
