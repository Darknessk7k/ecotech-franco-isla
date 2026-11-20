import re
from datetime import date

from dominio.usuario import Usuario
from dominio.registro_tiempo import RegistroTiempo
from dominio.excepciones import DatoInvalidoError, SalarioInvalidoError


class Empleado(Usuario):

    CAMPOS_EDITABLES = ("nombre", "direccion", "telefono", "email")

    def __init__(self, nombre_usuario: str, password_hash: str, nombre: str, direccion: str,
                 telefono: str, email: str, fecha_inicio_contrato: date, salario: float,
                 id_departamento: int = None, id_usuario: int = None):
        super().__init__(nombre_usuario, password_hash, id_usuario)
        self._rol = "EMPLEADO"
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.email = email
        self.fecha_inicio_contrato = fecha_inicio_contrato
        self.salario = salario
        self.id_departamento = id_departamento
        self._registros = []

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError("El nombre debe tener al menos 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            raise DatoInvalidoError("La dirección es obligatoria.")
        self._direccion = valor.strip()

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        valor = str(valor).strip().replace(" ", "")
        if not re.fullmatch(r"\+?\d{8,12}", valor):
            raise DatoInvalidoError("El teléfono debe tener entre 8 y 12 dígitos (puede empezar con +).")
        self._telefono = valor

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        valor = str(valor).strip().lower()
        if not re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.]+", valor):
            raise DatoInvalidoError("El correo no tiene un formato válido.")
        self._email = valor

    @property
    def fecha_inicio_contrato(self):
        return self._fecha_inicio_contrato

    @fecha_inicio_contrato.setter
    def fecha_inicio_contrato(self, valor):
        if not isinstance(valor, date):
            raise DatoInvalidoError("La fecha de inicio de contrato no es válida.")
        if valor > date.today():
            raise DatoInvalidoError("La fecha de inicio de contrato no puede ser futura.")
        self._fecha_inicio_contrato = valor

    @property
    def salario(self):
        return self._salario

    @salario.setter
    def salario(self, valor):
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise SalarioInvalidoError("El salario debe ser un número.")
        if valor <= 0:
            raise SalarioInvalidoError("El salario debe ser mayor a 0.")
        self._salario = float(valor)

    @property
    def id_departamento(self):
        return self._id_departamento

    @id_departamento.setter
    def id_departamento(self, valor):
        self._id_departamento = valor

    @property
    def registros(self):
        return list(self._registros)

    def registrar_horas(self, fecha: date, horas: float, tarea: str, id_proyecto: int) -> RegistroTiempo:
        registro = RegistroTiempo(fecha, horas, tarea, id_proyecto)
        self._registros.append(registro)
        return registro

    def cargar_registros(self, registros: list):
        self._registros = list(registros)

    def total_horas(self) -> float:
        return sum(r.horas_trabajadas for r in self._registros)

    def actualizar_datos(self, datos: dict):
        for campo in datos:
            if campo not in self.CAMPOS_EDITABLES:
                raise DatoInvalidoError(f"El campo '{campo}' no se puede editar por aquí.")
        respaldo = {campo: getattr(self, campo) for campo in datos}
        try:
            for campo, valor in datos.items():
                setattr(self, campo, valor)
        except DatoInvalidoError:
            for campo, valor in respaldo.items():
                setattr(self, campo, valor)
            raise

    def modulos_permitidos(self) -> list:
        return ["perfil", "horas", "clima"]

    def descripcion(self) -> str:
        return f"[EMPLEADO] {self.nombre_usuario} - {self.nombre} ({self.email})"

    def __str__(self):
        return (f"{self.id_usuario:>3} | {self.nombre:<20} | {self.email:<25} | "
                f"{self.telefono:<12} | ${self.salario:,.0f}")
