from datetime import date

from dominio.departamento import Departamento
from dominio.empleado import Empleado
from dominio.proyecto import Proyecto
from dominio.seguridad import generar_hash
from repositorio.conexion import inicializar_bd
from repositorio.empleado_repo import EmpleadoRepositorio
from repositorio.departamento_repo import DepartamentoRepositorio
from repositorio.proyecto_repo import ProyectoRepositorio
from repositorio.registro_repo import RegistroRepositorio

inicializar_bd()
empleados = EmpleadoRepositorio()
departamentos = DepartamentoRepositorio()
proyectos = ProyectoRepositorio()
registros = RegistroRepositorio()

if departamentos.listar():
    print("Los datos de prueba ya estaban cargados.")
    raise SystemExit

id_id = departamentos.guardar(Departamento("Investigación y Desarrollo"))
id_op = departamentos.guardar(Departamento("Operaciones"))

ana = Empleado("ana.perez", generar_hash("Clave1234"), "Ana Pérez", "Los Carrera 120, Concepción",
               "+56911112222", "ana.perez@ecotech.cl", date(2024, 3, 1), 950000, id_id)
luis = Empleado("luis.soto", generar_hash("Clave1234"), "Luis Soto", "Michimalonco 455, San Pedro de la Paz",
                "+56933334444", "luis.soto@ecotech.cl", date(2025, 1, 15), 780000, id_op)
empleados.guardar(ana)
empleados.guardar(luis)

panel = Proyecto("Panel Solar Modular v2", "Rediseño de paneles solares", date(2026, 3, 2))
panel_id = proyectos.guardar(panel)
proyectos.asignar_empleado(panel_id, ana.id_usuario)
proyectos.asignar_empleado(panel_id, luis.id_usuario)

registro = ana.registrar_horas(date(2026, 8, 12), 6, "Revisión de planos eléctricos", panel_id)
registros.guardar(ana.id_usuario, registro)
registro = luis.registrar_horas(date(2026, 8, 13), 4.5, "Pruebas de eficiencia", panel_id)
registros.guardar(luis.id_usuario, registro)

print("Datos de prueba cargados.")
