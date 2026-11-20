from datetime import date

from dominio.excepciones import DatoInvalidoError, HorasInvalidasError


class RegistroTiempo:

    def __init__(self, fecha: date, horas_trabajadas: float, descripcion_tarea: str,
                 id_proyecto: int, id_registro: int = None):
        self._id_registro = id_registro
        self._fecha = fecha
        self._horas_trabajadas = horas_trabajadas
        self._descripcion_tarea = descripcion_tarea
        self._id_proyecto = id_proyecto
        self.validar_horas()

    @property
    def id_registro(self):
        return self._id_registro

    @property
    def fecha(self):
        return self._fecha

    @property
    def horas_trabajadas(self):
        return self._horas_trabajadas

    @property
    def descripcion_tarea(self):
        return self._descripcion_tarea

    @property
    def id_proyecto(self):
        return self._id_proyecto

    def validar_horas(self) -> bool:
        if not isinstance(self._fecha, date):
            raise DatoInvalidoError("La fecha del registro no es válida.")
        if self._fecha > date.today():
            raise DatoInvalidoError("No se pueden registrar horas en una fecha futura.")
        if not isinstance(self._horas_trabajadas, (int, float)):
            raise HorasInvalidasError("Las horas deben ser un número.")
        if self._horas_trabajadas <= 0 or self._horas_trabajadas > 24:
            raise HorasInvalidasError("Las horas deben ser mayores a 0 y como máximo 24.")
        if not self._descripcion_tarea or not self._descripcion_tarea.strip():
            raise DatoInvalidoError("La descripción de la tarea es obligatoria.")
        return True

    def __str__(self):
        return f"{self._fecha} | {self._horas_trabajadas} h | {self._descripcion_tarea}"
