from datetime import date

from dominio.proyecto import Proyecto
from dominio.excepciones import NoEncontradoError
from repositorio.conexion import consultar, ejecutar


def _fila_a_proyecto(fila) -> Proyecto:
    return Proyecto(
        nombre=fila["nombre"],
        descripcion=fila["descripcion"],
        fecha_inicio=date.fromisoformat(fila["fecha_inicio"]),
        id_proyecto=fila["id_proyecto"],
    )


class ProyectoRepositorio:

    def guardar(self, proyecto: Proyecto) -> int:
        cursor = ejecutar(
            "INSERT INTO proyecto (nombre, descripcion, fecha_inicio) VALUES (?, ?, ?)",
            (proyecto.nombre, proyecto.descripcion, proyecto.fecha_inicio.isoformat()),
        )
        return cursor.lastrowid

    def obtener_por_id(self, id_proyecto: int) -> Proyecto:
        filas = consultar(
            "SELECT id_proyecto, nombre, descripcion, fecha_inicio FROM proyecto WHERE id_proyecto = ?",
            (id_proyecto,),
        )
        if not filas:
            raise NoEncontradoError(f"No existe un proyecto con ID {id_proyecto}.")
        return _fila_a_proyecto(filas[0])

    def listar(self) -> list:
        filas = consultar("SELECT id_proyecto, nombre, descripcion, fecha_inicio FROM proyecto ORDER BY id_proyecto")
        return [_fila_a_proyecto(f) for f in filas]

    def actualizar(self, proyecto: Proyecto):
        cursor = ejecutar(
            "UPDATE proyecto SET nombre = ?, descripcion = ?, fecha_inicio = ? WHERE id_proyecto = ?",
            (proyecto.nombre, proyecto.descripcion, proyecto.fecha_inicio.isoformat(), proyecto.id_proyecto),
        )
        if cursor.rowcount == 0:
            raise NoEncontradoError(f"No existe un proyecto con ID {proyecto.id_proyecto}.")

    def eliminar(self, id_proyecto: int):
        cursor = ejecutar("DELETE FROM proyecto WHERE id_proyecto = ?", (id_proyecto,))
        if cursor.rowcount == 0:
            raise NoEncontradoError(f"No existe un proyecto con ID {id_proyecto}.")

    def asignar_empleado(self, id_proyecto: int, id_usuario: int):
        ejecutar(
            "INSERT INTO empleado_proyecto (id_usuario, id_proyecto) VALUES (?, ?)",
            (id_usuario, id_proyecto),
        )

    def desasignar_empleado(self, id_proyecto: int, id_usuario: int):
        cursor = ejecutar(
            "DELETE FROM empleado_proyecto WHERE id_usuario = ? AND id_proyecto = ?",
            (id_usuario, id_proyecto),
        )
        if cursor.rowcount == 0:
            raise NoEncontradoError("Ese empleado no estaba asignado a ese proyecto.")

    def esta_asignado(self, id_proyecto: int, id_usuario: int) -> bool:
        filas = consultar(
            "SELECT 1 FROM empleado_proyecto WHERE id_usuario = ? AND id_proyecto = ?",
            (id_usuario, id_proyecto),
        )
        return len(filas) > 0

    def listar_por_empleado(self, id_usuario: int) -> list:
        filas = consultar(
            "SELECT p.id_proyecto, p.nombre, p.descripcion, p.fecha_inicio FROM proyecto p "
            "JOIN empleado_proyecto ep ON ep.id_proyecto = p.id_proyecto "
            "WHERE ep.id_usuario = ? ORDER BY p.nombre",
            (id_usuario,),
        )
        return [_fila_a_proyecto(f) for f in filas]

    def listar_empleados_asignados(self, id_proyecto: int) -> list:
        return consultar(
            "SELECT e.id_usuario, e.nombre FROM empleado e "
            "JOIN empleado_proyecto ep ON ep.id_usuario = e.id_usuario "
            "WHERE ep.id_proyecto = ? ORDER BY e.nombre",
            (id_proyecto,),
        )
