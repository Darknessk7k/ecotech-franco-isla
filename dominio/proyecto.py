from datetime import date

from dominio.excepciones import DatoInvalidoError


class Proyecto:

    def __init__(self, nombre: str, descripcion: str, fecha_inicio: date, id_proyecto: int = None):
        self._id_proyecto = id_proyecto
        self.nombre = nombre
        self.descripcion = descripcion
        self.fecha_inicio = fecha_inicio
        self._empleados = []
        self._registros = []

    @property
    def id_proyecto(self):
        return self._id_proyecto

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError("El nombre del proyecto debe tener al menos 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def descripcion(self):
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor):
        self._descripcion = (valor or "").strip()

    @property
    def fecha_inicio(self):
        return self._fecha_inicio

    @fecha_inicio.setter
    def fecha_inicio(self, valor):
        if not isinstance(valor, date):
            raise DatoInvalidoError("La fecha de inicio del proyecto no es válida.")
        self._fecha_inicio = valor

    def asignar_empleado(self, empleado):
        if empleado in self._empleados:
            raise DatoInvalidoError("El empleado ya está asignado a este proyecto.")
        self._empleados.append(empleado)

    def desasignar_empleado(self, empleado):
        if empleado not in self._empleados:
            raise DatoInvalidoError("El empleado no está asignado a este proyecto.")
        self._empleados.remove(empleado)

    def cargar_registros(self, registros: list):
        self._registros = list(registros)

    def total_horas_registradas(self) -> float:
        return sum(r.horas_trabajadas for r in self._registros)

    def __str__(self):
        return f"{self._id_proyecto:>3} | {self._nombre:<25} | inicio {self._fecha_inicio}"
