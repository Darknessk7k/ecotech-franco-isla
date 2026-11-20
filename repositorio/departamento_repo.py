from dominio.departamento import Departamento
from dominio.excepciones import NoEncontradoError
from repositorio.conexion import consultar, ejecutar


def _fila_a_departamento(fila) -> Departamento:
    return Departamento(
        nombre=fila["nombre"],
        id_gerente=fila["id_gerente"],
        id_departamento=fila["id_departamento"],
    )


class DepartamentoRepositorio:

    def guardar(self, departamento: Departamento) -> int:
        cursor = ejecutar(
            "INSERT INTO departamento (nombre, id_gerente) VALUES (?, ?)",
            (departamento.nombre, departamento.id_gerente),
        )
        return cursor.lastrowid

    def obtener_por_id(self, id_departamento: int) -> Departamento:
        filas = consultar(
            "SELECT id_departamento, nombre, id_gerente FROM departamento WHERE id_departamento = ?",
            (id_departamento,),
        )
        if not filas:
            raise NoEncontradoError(f"No existe un departamento con ID {id_departamento}.")
        return _fila_a_departamento(filas[0])

    def buscar_por_nombre(self, texto: str) -> list:
        filas = consultar(
            "SELECT id_departamento, nombre, id_gerente FROM departamento "
            "WHERE nombre LIKE '%' || ? || '%' ORDER BY nombre",
            (texto,),
        )
        return [_fila_a_departamento(f) for f in filas]

    def listar(self) -> list:
        filas = consultar("SELECT id_departamento, nombre, id_gerente FROM departamento ORDER BY id_departamento")
        return [_fila_a_departamento(f) for f in filas]

    def actualizar(self, departamento: Departamento):
        cursor = ejecutar(
            "UPDATE departamento SET nombre = ?, id_gerente = ? WHERE id_departamento = ?",
            (departamento.nombre, departamento.id_gerente, departamento.id_departamento),
        )
        if cursor.rowcount == 0:
            raise NoEncontradoError(f"No existe un departamento con ID {departamento.id_departamento}.")

    def eliminar(self, id_departamento: int):
        cursor = ejecutar("DELETE FROM departamento WHERE id_departamento = ?", (id_departamento,))
        if cursor.rowcount == 0:
            raise NoEncontradoError(f"No existe un departamento con ID {id_departamento}.")
