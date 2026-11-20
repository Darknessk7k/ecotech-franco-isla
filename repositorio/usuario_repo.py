import sqlite3

from dominio.administrador import Administrador
from repositorio.conexion import obtener_conexion, consultar, traducir_error
from repositorio.empleado_repo import _fila_a_empleado


def _fila_a_admin(fila) -> Administrador:
    return Administrador(
        nombre_usuario=fila["nombre_usuario"],
        password_hash=fila["password_hash"],
        area_responsable=fila["area_responsable"],
        id_usuario=fila["id_usuario"],
    )


MAPPERS = {
    "ADMIN": _fila_a_admin,
    "EMPLEADO": _fila_a_empleado,
}


class UsuarioRepositorio:

    def obtener_por_nombre(self, nombre_usuario: str):
        filas = consultar(
            "SELECT u.id_usuario, u.nombre_usuario, u.password_hash, u.rol, a.area_responsable, "
            "e.nombre, e.direccion, e.telefono, e.email, e.fecha_inicio_contrato, e.salario, e.id_departamento "
            "FROM usuario u "
            "LEFT JOIN administrador a ON a.id_usuario = u.id_usuario "
            "LEFT JOIN empleado e ON e.id_usuario = u.id_usuario "
            "WHERE u.nombre_usuario = ?",
            (nombre_usuario.strip().lower(),),
        )
        if not filas:
            return None
        fila = filas[0]
        return MAPPERS[fila["rol"]](fila)

    def listar_todos(self) -> list:
        filas = consultar(
            "SELECT u.id_usuario, u.nombre_usuario, u.password_hash, u.rol, a.area_responsable, "
            "e.nombre, e.direccion, e.telefono, e.email, e.fecha_inicio_contrato, e.salario, e.id_departamento "
            "FROM usuario u "
            "LEFT JOIN administrador a ON a.id_usuario = u.id_usuario "
            "LEFT JOIN empleado e ON e.id_usuario = u.id_usuario "
            "ORDER BY u.id_usuario"
        )
        return [MAPPERS[f["rol"]](f) for f in filas]

    def existe_admin(self) -> bool:
        filas = consultar("SELECT COUNT(*) AS total FROM usuario WHERE rol = 'ADMIN'")
        return filas[0]["total"] > 0

    def guardar_admin(self, admin: Administrador) -> int:
        conexion = obtener_conexion()
        try:
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO usuario (nombre_usuario, password_hash, rol) VALUES (?, ?, 'ADMIN')",
                (admin.nombre_usuario, admin.password_hash),
            )
            nuevo_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO administrador (id_usuario, area_responsable) VALUES (?, ?)",
                (nuevo_id, admin.area_responsable),
            )
            conexion.commit()
            admin.id_usuario = nuevo_id
            return nuevo_id
        except sqlite3.Error as error:
            conexion.rollback()
            raise traducir_error(error) from error
        finally:
            conexion.close()
