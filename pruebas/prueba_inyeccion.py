from repositorio.conexion import inicializar_bd
from repositorio.empleado_repo import EmpleadoRepositorio
from repositorio.usuario_repo import UsuarioRepositorio

inicializar_bd()
empleados = EmpleadoRepositorio()
usuarios = UsuarioRepositorio()

payload = "' OR '1'='1"

print("Prueba de inyección SQL")
print("Payload usado:", payload)
print()
print("Empleados en la base de datos:", len(empleados.listar()))
print("obtener_por_usuario(payload) devolvió:", len(empleados.obtener_por_usuario(payload)), "empleados")
print("buscar_por_nombre(payload) devolvió:", len(empleados.buscar_por_nombre(payload)), "empleados")
print("Login con usuario = payload:", usuarios.obtener_por_nombre(payload))
print()
print("Búsqueda normal 'Ana':", [e.nombre for e in empleados.buscar_por_nombre("Ana")])
