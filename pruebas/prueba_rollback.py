from datetime import date

from dominio.empleado import Empleado
from dominio.excepciones import EcoTechError
from dominio.seguridad import generar_hash
from repositorio.conexion import inicializar_bd, consultar
from repositorio.empleado_repo import EmpleadoRepositorio

inicializar_bd()
empleados = EmpleadoRepositorio()


def contar_usuarios():
    return consultar("SELECT COUNT(*) AS total FROM usuario")[0]["total"]


print("Prueba de transacción (commit / rollback)")
print("Usuarios antes:", contar_usuarios())

nuevo = Empleado("pedro.rojas", generar_hash("Clave1234"), "Pedro Rojas", "Av. Pedro de Valdivia 900",
                 "+56955556666", "pedro.rojas@ecotech.cl", date(2026, 5, 4), 820000, id_departamento=999)
try:
    empleados.guardar(nuevo)
except EcoTechError as error:
    print("Falló el segundo INSERT:", error)

print("Usuarios después:", contar_usuarios())
quedo = consultar("SELECT COUNT(*) AS total FROM usuario WHERE nombre_usuario = ?", ("pedro.rojas",))[0]["total"]
print("¿Quedó 'pedro.rojas' en la tabla usuario?", "Sí" if quedo else "No, se hizo rollback")
