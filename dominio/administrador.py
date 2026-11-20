from datetime import date

from dominio.usuario import Usuario
from dominio.informe import Informe
from dominio.excepciones import DatoInvalidoError


class Administrador(Usuario):

    def __init__(self, nombre_usuario: str, password_hash: str, area_responsable: str,
                 id_usuario: int = None):
        super().__init__(nombre_usuario, password_hash, id_usuario)
        self._rol = "ADMIN"
        self.area_responsable = area_responsable

    @property
    def area_responsable(self):
        return self._area_responsable

    @area_responsable.setter
    def area_responsable(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            raise DatoInvalidoError("El área responsable es obligatoria.")
        self._area_responsable = valor.strip()

    def generar_informe(self, tipo: str, formato: str, filas: list) -> Informe:
        return Informe(tipo, formato, date.today(), filas)

    def gestionar_departamento(self, departamento, nuevo_nombre: str):
        departamento.nombre = nuevo_nombre

    def modulos_permitidos(self) -> list:
        return ["perfil", "empleados", "departamentos", "proyectos", "informes", "usuarios", "clima", "pagos"]

    def descripcion(self) -> str:
        return f"[ADMIN] {self.nombre_usuario} - área {self.area_responsable}"
