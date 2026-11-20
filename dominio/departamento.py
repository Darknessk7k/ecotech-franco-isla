from dominio.excepciones import DatoInvalidoError


class Departamento:

    def __init__(self, nombre: str, id_gerente: int = None, id_departamento: int = None):
        self._id_departamento = id_departamento
        self.nombre = nombre
        self._id_gerente = id_gerente
        self._empleados = []

    @property
    def id_departamento(self):
        return self._id_departamento

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 2:
            raise DatoInvalidoError("El nombre del departamento debe tener al menos 2 caracteres.")
        self._nombre = valor.strip()

    @property
    def id_gerente(self):
        return self._id_gerente

    @id_gerente.setter
    def id_gerente(self, valor):
        self._id_gerente = valor

    def agregar_empleado(self, empleado):
        if empleado not in self._empleados:
            self._empleados.append(empleado)
            empleado.id_departamento = self._id_departamento

    def quitar_empleado(self, empleado):
        if empleado in self._empleados:
            self._empleados.remove(empleado)
            empleado.id_departamento = None

    def listar_empleados(self) -> list:
        return list(self._empleados)

    def __str__(self):
        gerente = self._id_gerente if self._id_gerente else "sin gerente"
        return f"{self._id_departamento:>3} | {self._nombre:<25} | gerente: {gerente}"
