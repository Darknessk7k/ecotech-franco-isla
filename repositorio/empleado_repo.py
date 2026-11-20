import sqlite3
from datetime import date

from dominio.empleado import Empleado
from dominio.excepciones import NoEncontradoError
from repositorio.conexion import obtener_conexion, consultar, ejecutar, traducir_error


def _fila_a_empleado(fila) -> Empleado:
    return Empleado(
        nombre_usuario=fila["nombre_usuario"],
        password_hash=fila["password_hash"],
        nombre=fila["nombre"],
        direccion=fila["direccion"],
        telefono=fila["telefono"],
        email=fila["email"],
        fecha_inicio_contrato=date.fromisoformat(fila["fecha_inicio_contrato"]),
        salario=fila["salario"],
        id_departamento=fila["id_departamento"],
        id_usuario=fila["id_usuario"],
    )


class EmpleadoRepositorio:

    def guardar(self, empleado: Empleado) -> int:
        conexion = obtener_conexion()
        try:
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO usuario (nombre_usuario, password_hash, rol) VALUES (?, ?, 'EMPLEADO')",
                (empleado.nombre_usuario, empleado.password_hash),
            )
            nuevo_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO empleado (id_usuario, nombre, direccion, telefono, email, "
                "fecha_inicio_contrato, salario, id_departamento) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (nuevo_id, empleado.nombre, empleado.direccion, empleado.telefono, empleado.email,
                 empleado.fecha_inicio_contrato.isoformat(), empleado.salario, empleado.id_departamento),
            )
            conexion.commit()
            empleado.id_usuario = nuevo_id
            return nuevo_id
        except sqlite3.Error as error:
            conexion.rollback()
            raise traducir_error(error) from error
        finally:
            conexion.close()

    def obtener_por_id(self, id_usuario: int) -> Empleado:
        filas = consultar(
            "SELECT u.id_usuario, u.nombre_usuario, u.password_hash, e.nombre, e.direccion, e.telefono, "
            "e.email, e.fecha_inicio_contrato, e.salario, e.id_departamento "
            "FROM empleado e JOIN usuario u ON u.id_usuario = e.id_usuario WHERE e.id_usuario = ?",
            (id_usuario,),
        )
        if not filas:
            raise NoEncontradoError(f"No existe un empleado con ID {id_usuario}.")
        return _fila_a_empleado(filas[0])

    def obtener_por_usuario(self, nombre_usuario: str) -> list:
        filas = consultar(
            "SELECT u.id_usuario, u.nombre_usuario, u.password_hash, e.nombre, e.direccion, e.telefono, "
            "e.email, e.fecha_inicio_contrato, e.salario, e.id_departamento "
            "FROM empleado e JOIN usuario u ON u.id_usuario = e.id_usuario WHERE u.nombre_usuario = ?",
            (nombre_usuario,),
        )
        return [_fila_a_empleado(f) for f in filas]

    def buscar_por_nombre(self, texto: str) -> list:
        filas = consultar(
            "SELECT u.id_usuario, u.nombre_usuario, u.password_hash, e.nombre, e.direccion, e.telefono, "
            "e.email, e.fecha_inicio_contrato, e.salario, e.id_departamento "
            "FROM empleado e JOIN usuario u ON u.id_usuario = e.id_usuario "
            "WHERE e.nombre LIKE '%' || ? || '%' ORDER BY e.nombre",
            (texto,),
        )
        return [_fila_a_empleado(f) for f in filas]

    def listar(self) -> list:
        filas = consultar(
            "SELECT u.id_usuario, u.nombre_usuario, u.password_hash, e.nombre, e.direccion, e.telefono, "
            "e.email, e.fecha_inicio_contrato, e.salario, e.id_departamento "
            "FROM empleado e JOIN usuario u ON u.id_usuario = e.id_usuario ORDER BY e.id_usuario"
        )
        return [_fila_a_empleado(f) for f in filas]

    def listar_por_departamento(self, id_departamento: int) -> list:
        filas = consultar(
            "SELECT u.id_usuario, u.nombre_usuario, u.password_hash, e.nombre, e.direccion, e.telefono, "
            "e.email, e.fecha_inicio_contrato, e.salario, e.id_departamento "
            "FROM empleado e JOIN usuario u ON u.id_usuario = e.id_usuario "
            "WHERE e.id_departamento = ? ORDER BY e.nombre",
            (id_departamento,),
        )
        return [_fila_a_empleado(f) for f in filas]

    def actualizar(self, empleado: Empleado):
        cursor = ejecutar(
            "UPDATE empleado SET nombre = ?, direccion = ?, telefono = ?, email = ?, salario = ?, "
            "id_departamento = ? WHERE id_usuario = ?",
            (empleado.nombre, empleado.direccion, empleado.telefono, empleado.email,
             empleado.salario, empleado.id_departamento, empleado.id_usuario),
        )
        if cursor.rowcount == 0:
            raise NoEncontradoError(f"No existe un empleado con ID {empleado.id_usuario}.")

    def eliminar(self, id_usuario: int):
        cursor = ejecutar(
            "DELETE FROM usuario WHERE id_usuario = ? AND rol = 'EMPLEADO'",
            (id_usuario,),
        )
        if cursor.rowcount == 0:
            raise NoEncontradoError(f"No existe un empleado con ID {id_usuario}.")
