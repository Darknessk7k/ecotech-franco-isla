from repositorio.conexion import inicializar_bd, consultar

inicializar_bd()
print("Tabla usuario (así se guardan las contraseñas):\n")
for fila in consultar("SELECT id_usuario, nombre_usuario, rol, password_hash FROM usuario ORDER BY id_usuario"):
    print(f"{fila['id_usuario']:>3} | {fila['nombre_usuario']:<12} | {fila['rol']:<8} | {fila['password_hash']}")
print("\nTodas deben empezar con $2b$12$ (bcrypt con salt). Ninguna debe verse como una clave normal.")
