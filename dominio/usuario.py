import os
import time
from abc import ABC, abstractmethod

from dominio.excepciones import DatoInvalidoError
from dominio.seguridad import verificar_clave
from dominio.validaciones import PATRON_USUARIO


class Usuario(ABC):

    def __init__(self, nombre_usuario: str, password_hash: str, id_usuario: int = None):
        self._id_usuario = id_usuario
        self.nombre_usuario = nombre_usuario
        self._password_hash = password_hash
        self._rol = ""
        self._autenticado_en = None

    @property
    def id_usuario(self):
        return self._id_usuario

    @id_usuario.setter
    def id_usuario(self, valor):
        if self._id_usuario is not None:
            raise DatoInvalidoError("El ID de usuario no se puede cambiar.")
        self._id_usuario = valor

    @property
    def nombre_usuario(self):
        return self._nombre_usuario

    @nombre_usuario.setter
    def nombre_usuario(self, valor):
        if not isinstance(valor, str):
            raise DatoInvalidoError("El nombre de usuario debe ser un texto.")
        valor = valor.strip().lower()
        if not PATRON_USUARIO.fullmatch(valor):
            raise DatoInvalidoError(
                "El nombre de usuario debe tener de 3 a 30 caracteres: letras sin tilde, números, punto, guion o guion bajo."
            )
        self._nombre_usuario = valor

    @property
    def password_hash(self):
        return self._password_hash

    @property
    def rol(self):
        return self._rol

    def autenticar(self, clave: str) -> bool:
        correcta = verificar_clave(clave, self._password_hash)
        self._autenticado_en = time.monotonic() if correcta else None
        return correcta

    def sesion_activa(self) -> bool:
        """True si inició sesión y no pasó el tiempo máximo de inactividad."""
        if self._autenticado_en is None:
            return False
        try:
            minutos = int(os.getenv("SESION_MINUTOS", "15"))
        except ValueError:
            minutos = 15
        if time.monotonic() - self._autenticado_en > minutos * 60:
            self._autenticado_en = None
            return False
        self._autenticado_en = time.monotonic()
        return True

    def cerrar_sesion(self):
        self._autenticado_en = None

    def tiene_acceso(self, modulo: str) -> bool:
        return modulo in self.modulos_permitidos()

    @abstractmethod
    def modulos_permitidos(self) -> list:
        pass

    @abstractmethod
    def descripcion(self) -> str:
        pass
