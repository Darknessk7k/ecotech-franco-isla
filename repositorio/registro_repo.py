from datetime import date

from dominio.registro_tiempo import RegistroTiempo
from dominio.excepciones import DatoInvalidoError
from repositorio.conexion import consultar, ejecutar


def _fila_a_registro(fila) -> RegistroTiempo:
    return RegistroTiempo(
        fecha=date.fromisoformat(fila["fecha"]),
        horas_trabajadas=fila["horas_trabajadas"],
        descripcion_tarea=fila["descripcion_tarea"],
        id_proyecto=fila["id_proyecto"],
        id_registro=fila["id_registro"],
    )


class RegistroRepositorio:

    def guardar(self, id_usuario: int, registro: RegistroTiempo) -> int:
        asignado = consultar(
            "SELECT 1 FROM empleado_proyecto WHERE id_usuario = ? AND id_proyecto = ?",
            (id_usuario, registro.id_proyecto),
        )
        if not asignado:
            raise DatoInvalidoError("El empleado no está asignado a ese proyecto, no puede registrar horas ahí.")
        cursor = ejecutar(
            "INSERT INTO registro_tiempo (id_usuario, id_proyecto, fecha, horas_trabajadas, descripcion_tarea) "
            "VALUES (?, ?, ?, ?, ?)",
            (id_usuario, registro.id_proyecto, registro.fecha.isoformat(),
             registro.horas_trabajadas, registro.descripcion_tarea),
        )
        return cursor.lastrowid

    def listar_por_empleado(self, id_usuario: int) -> list:
        filas = consultar(
            "SELECT id_registro, id_proyecto, fecha, horas_trabajadas, descripcion_tarea "
            "FROM registro_tiempo WHERE id_usuario = ? ORDER BY fecha",
            (id_usuario,),
        )
        return [_fila_a_registro(f) for f in filas]

    def listar_por_proyecto(self, id_proyecto: int) -> list:
        filas = consultar(
            "SELECT id_registro, id_proyecto, fecha, horas_trabajadas, descripcion_tarea "
            "FROM registro_tiempo WHERE id_proyecto = ? ORDER BY fecha",
            (id_proyecto,),
        )
        return [_fila_a_registro(f) for f in filas]

    def resumen_horas(self) -> list:
        filas = consultar(
            "SELECT p.nombre AS proyecto, e.nombre AS empleado, SUM(r.horas_trabajadas) AS total "
            "FROM registro_tiempo r "
            "JOIN proyecto p ON p.id_proyecto = r.id_proyecto "
            "JOIN empleado e ON e.id_usuario = r.id_usuario "
            "GROUP BY p.nombre, e.nombre ORDER BY p.nombre, e.nombre"
        )
        return [(f["proyecto"], f["empleado"], f["total"]) for f in filas]
