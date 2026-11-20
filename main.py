import logging
import os
import sys
from datetime import datetime
from getpass import getpass

from dominio.administrador import Administrador
from dominio.departamento import Departamento
from dominio.empleado import Empleado
from dominio.proyecto import Proyecto
from dominio.excepciones import EcoTechError, DatoInvalidoError, AccesoDenegadoError
from dominio.datos_externos import describir_antiguedad, formatear_fecha_local
from dominio.seguridad import generar_hash
from dominio.validaciones import credenciales_validas
from repositorio.conexion import inicializar_bd
from repositorio.usuario_repo import UsuarioRepositorio
from repositorio.empleado_repo import EmpleadoRepositorio
from repositorio.departamento_repo import DepartamentoRepositorio
from repositorio.proyecto_repo import ProyectoRepositorio
from repositorio.registro_repo import RegistroRepositorio
from registro import configurar_logging
from servicio_externo import ServicioExterno

logger = logging.getLogger("ecotech.main")

usuarios = UsuarioRepositorio()
empleados = EmpleadoRepositorio()
departamentos = DepartamentoRepositorio()
proyectos = ProyectoRepositorio()
registros = RegistroRepositorio()
externo = ServicioExterno()


def pedir_texto(mensaje, obligatorio=True):
    while True:
        valor = input(mensaje).strip()
        if valor or not obligatorio:
            return valor
        print("  Este campo es obligatorio.")


def pedir_entero(mensaje, obligatorio=True):
    while True:
        valor = input(mensaje).strip()
        if not valor and not obligatorio:
            return None
        try:
            return int(valor)
        except ValueError:
            print("  Debe ingresar un número entero.")


def pedir_decimal(mensaje):
    while True:
        valor = input(mensaje).strip().replace(",", ".")
        try:
            return float(valor)
        except ValueError:
            print("  Debe ingresar un número (ej: 850000 o 7.5).")


def pedir_fecha(mensaje):
    while True:
        valor = input(mensaje).strip()
        try:
            return datetime.strptime(valor, "%d-%m-%Y").date()
        except ValueError:
            print("  Formato de fecha inválido, use DD-MM-AAAA.")


def pedir_clave(mensaje):
    if sys.stdin.isatty():
        return getpass(mensaje)
    return input(mensaje)


def confirmar(mensaje):
    return input(f"{mensaje} (s/n): ").strip().lower() == "s"


def crear_admin_inicial():
    if usuarios.existe_admin():
        return
    nombre = os.getenv("ECOTECH_ADMIN_USUARIO", "admin")
    clave = os.getenv("ECOTECH_ADMIN_PASSWORD")
    if not clave or len(clave) < 8:
        print("Falta ECOTECH_ADMIN_PASSWORD en el archivo .env (mínimo 8 caracteres).")
        print("Copie .env.example a .env y complete los datos.")
        sys.exit(1)
    admin = Administrador(nombre, generar_hash(clave), "Recursos Humanos")
    usuarios.guardar_admin(admin)
    print(f"Se creó el administrador inicial '{nombre}'.")


def iniciar_sesion():
    for intento in range(1, 4):
        nombre = pedir_texto("Usuario: ")
        clave = pedir_clave("Contraseña: ")
        # primero se valida el formato; si es inválido se cuenta como intento fallido sin consultar la base
        if credenciales_validas(nombre, clave):
            usuario = usuarios.obtener_por_nombre(nombre)
            if usuario is not None and usuario.autenticar(clave):
                return usuario
        print(f"  Usuario o contraseña incorrectos (intento {intento} de 3).")
    raise AccesoDenegadoError("Se superó el número de intentos.")


def ver_perfil(usuario):
    print("\n" + usuario.descripcion())


def registrar_horas(usuario):
    mis_proyectos = proyectos.listar_por_empleado(usuario.id_usuario)
    if not mis_proyectos:
        print("No tienes proyectos asignados.")
        return
    for p in mis_proyectos:
        print(" ", p)
    id_proyecto = pedir_entero("ID del proyecto: ")
    fecha = pedir_fecha("Fecha (DD-MM-AAAA): ")
    horas = pedir_decimal("Horas trabajadas: ")
    tarea = pedir_texto("Descripción de la tarea: ")
    registro = usuario.registrar_horas(fecha, horas, tarea, id_proyecto)
    registros.guardar(usuario.id_usuario, registro)
    print("Horas registradas correctamente.")


def ver_mis_registros(usuario):
    usuario.cargar_registros(registros.listar_por_empleado(usuario.id_usuario))
    if not usuario.registros:
        print("No tienes horas registradas.")
        return
    for r in usuario.registros:
        print(" ", r)
    print(f"Total: {usuario.total_horas()} horas")


def mostrar_empleados(lista):
    if not lista:
        print("No hay empleados para mostrar.")
    for e in lista:
        print(" ", e)


def listar_empleados():
    mostrar_empleados(empleados.listar())


def buscar_empleado():
    mostrar_empleados(empleados.buscar_por_nombre(pedir_texto("Texto a buscar: ")))


def crear_empleado():
    nombre_usuario = pedir_texto("Nombre de usuario: ")
    clave = pedir_clave("Contraseña (mín. 8 caracteres): ")
    if len(clave) < 8:
        raise DatoInvalidoError("La contraseña debe tener al menos 8 caracteres.")
    empleado = Empleado(
        nombre_usuario=nombre_usuario,
        password_hash=generar_hash(clave),
        nombre=pedir_texto("Nombre completo: "),
        direccion=pedir_texto("Dirección: "),
        telefono=pedir_texto("Teléfono: "),
        email=pedir_texto("Correo: "),
        fecha_inicio_contrato=pedir_fecha("Fecha inicio contrato (DD-MM-AAAA): "),
        salario=pedir_decimal("Salario: "),
        id_departamento=pedir_entero("ID departamento (Enter para ninguno): ", obligatorio=False),
    )
    nuevo_id = empleados.guardar(empleado)
    print(f"Empleado creado con ID {nuevo_id}.")


def editar_empleado():
    empleado = empleados.obtener_por_id(pedir_entero("ID del empleado: "))
    print("Deje en blanco lo que no quiera cambiar.")
    datos = {}
    for campo in Empleado.CAMPOS_EDITABLES:
        valor = pedir_texto(f"{campo} [{getattr(empleado, campo)}]: ", obligatorio=False)
        if valor:
            datos[campo] = valor
    empleado.actualizar_datos(datos)
    if confirmar("¿Cambiar salario?"):
        empleado.salario = pedir_decimal("Nuevo salario: ")
    empleados.actualizar(empleado)
    print("Empleado actualizado.")


def eliminar_empleado():
    empleado = empleados.obtener_por_id(pedir_entero("ID del empleado: "))
    if confirmar(f"¿Eliminar a {empleado.nombre}? También se borran sus horas"):
        empleados.eliminar(empleado.id_usuario)
        print("Empleado eliminado.")


def menu_empleados(usuario):
    opciones = {
        "1": ("Listar empleados", listar_empleados),
        "2": ("Buscar por nombre", buscar_empleado),
        "3": ("Registrar empleado", crear_empleado),
        "4": ("Editar empleado", editar_empleado),
        "5": ("Eliminar empleado", eliminar_empleado),
    }
    submenu("Empleados", opciones)


def listar_departamentos():
    lista = departamentos.listar()
    if not lista:
        print("No hay departamentos.")
    for d in lista:
        print(" ", d)


def crear_departamento():
    departamento = Departamento(pedir_texto("Nombre del departamento: "))
    nuevo_id = departamentos.guardar(departamento)
    print(f"Departamento creado con ID {nuevo_id}.")


def editar_departamento():
    departamento = departamentos.obtener_por_id(pedir_entero("ID del departamento: "))
    nuevo_nombre = pedir_texto(f"Nombre [{departamento.nombre}]: ", obligatorio=False)
    if nuevo_nombre:
        departamento.nombre = nuevo_nombre
    id_gerente = pedir_entero("ID del empleado gerente (Enter para no cambiar): ", obligatorio=False)
    if id_gerente is not None:
        empleados.obtener_por_id(id_gerente)
        departamento.id_gerente = id_gerente
    departamentos.actualizar(departamento)
    print("Departamento actualizado.")


def eliminar_departamento():
    departamento = departamentos.obtener_por_id(pedir_entero("ID del departamento: "))
    if confirmar(f"¿Eliminar {departamento.nombre}? Sus empleados quedan sin departamento"):
        departamentos.eliminar(departamento.id_departamento)
        print("Departamento eliminado.")


def asignar_a_departamento():
    departamento = departamentos.obtener_por_id(pedir_entero("ID del departamento: "))
    empleado = empleados.obtener_por_id(pedir_entero("ID del empleado: "))
    departamento.agregar_empleado(empleado)
    empleados.actualizar(empleado)
    print(f"{empleado.nombre} ahora pertenece a {departamento.nombre}.")


def ver_empleados_departamento():
    departamento = departamentos.obtener_por_id(pedir_entero("ID del departamento: "))
    for e in empleados.listar_por_departamento(departamento.id_departamento):
        departamento.agregar_empleado(e)
    print(f"Empleados de {departamento.nombre}:")
    mostrar_empleados(departamento.listar_empleados())


def menu_departamentos(usuario):
    opciones = {
        "1": ("Listar departamentos", listar_departamentos),
        "2": ("Crear departamento", crear_departamento),
        "3": ("Editar departamento / gerente", editar_departamento),
        "4": ("Eliminar departamento", eliminar_departamento),
        "5": ("Asignar empleado a departamento", asignar_a_departamento),
        "6": ("Ver empleados de un departamento", ver_empleados_departamento),
    }
    submenu("Departamentos", opciones)


def listar_proyectos():
    lista = proyectos.listar()
    if not lista:
        print("No hay proyectos.")
    for p in lista:
        print(" ", p)


def crear_proyecto():
    proyecto = Proyecto(
        nombre=pedir_texto("Nombre del proyecto: "),
        descripcion=pedir_texto("Descripción: ", obligatorio=False),
        fecha_inicio=pedir_fecha("Fecha de inicio (DD-MM-AAAA): "),
    )
    nuevo_id = proyectos.guardar(proyecto)
    print(f"Proyecto creado con ID {nuevo_id}.")


def editar_proyecto():
    proyecto = proyectos.obtener_por_id(pedir_entero("ID del proyecto: "))
    nombre = pedir_texto(f"Nombre [{proyecto.nombre}]: ", obligatorio=False)
    descripcion = pedir_texto(f"Descripción [{proyecto.descripcion}]: ", obligatorio=False)
    if nombre:
        proyecto.nombre = nombre
    if descripcion:
        proyecto.descripcion = descripcion
    proyectos.actualizar(proyecto)
    print("Proyecto actualizado.")


def eliminar_proyecto():
    proyecto = proyectos.obtener_por_id(pedir_entero("ID del proyecto: "))
    if confirmar(f"¿Eliminar {proyecto.nombre}? Se borran sus asignaciones y horas"):
        proyectos.eliminar(proyecto.id_proyecto)
        print("Proyecto eliminado.")


def asignar_a_proyecto():
    proyecto = proyectos.obtener_por_id(pedir_entero("ID del proyecto: "))
    empleado = empleados.obtener_por_id(pedir_entero("ID del empleado: "))
    proyectos.asignar_empleado(proyecto.id_proyecto, empleado.id_usuario)
    print(f"{empleado.nombre} asignado a {proyecto.nombre}.")


def desasignar_de_proyecto():
    proyecto = proyectos.obtener_por_id(pedir_entero("ID del proyecto: "))
    empleado = empleados.obtener_por_id(pedir_entero("ID del empleado: "))
    proyectos.desasignar_empleado(proyecto.id_proyecto, empleado.id_usuario)
    print(f"{empleado.nombre} ya no está en {proyecto.nombre}.")


def detalle_proyecto():
    proyecto = proyectos.obtener_por_id(pedir_entero("ID del proyecto: "))
    proyecto.cargar_registros(registros.listar_por_proyecto(proyecto.id_proyecto))
    print(proyecto)
    print("Empleados asignados:")
    for fila in proyectos.listar_empleados_asignados(proyecto.id_proyecto):
        print(f"   {fila['id_usuario']} - {fila['nombre']}")
    print(f"Total horas registradas: {proyecto.total_horas_registradas()}")


def menu_proyectos(usuario):
    opciones = {
        "1": ("Listar proyectos", listar_proyectos),
        "2": ("Crear proyecto", crear_proyecto),
        "3": ("Editar proyecto", editar_proyecto),
        "4": ("Eliminar proyecto", eliminar_proyecto),
        "5": ("Asignar empleado", asignar_a_proyecto),
        "6": ("Quitar empleado", desasignar_de_proyecto),
        "7": ("Ver detalle y horas", detalle_proyecto),
    }
    submenu("Proyectos", opciones)


def generar_informe(usuario):
    filas = registros.resumen_horas()
    if not filas:
        print("Todavía no hay horas registradas.")
        return
    formato = pedir_texto("Formato (csv/txt): ")
    informe = usuario.generar_informe("horas", formato, filas)
    ruta = informe.exportar()
    print(f"Informe generado en: {ruta}")


def mostrar_origen(resultado):
    cuando = f"{formatear_fecha_local(resultado.obtenido_en)} ({describir_antiguedad(resultado.obtenido_en)})"
    if resultado.en_vivo:
        print(f"  Origen: servicio externo, consultado ahora - {cuando}")
    else:
        print("  AVISO: no hay conexión con el servicio externo. Se muestran datos guardados localmente.")
        print(f"  Datos obtenidos el: {cuando}")


def consultar_clima(usuario):
    ciudad = pedir_texto("Ciudad: ")
    pais = pedir_texto("Código de país de 2 letras (Enter para omitir): ", obligatorio=False)
    resultado = externo.consultar_clima(usuario, ciudad, pais)
    c = resultado.datos
    print(f"\n  Clima en {c.ciudad}, {c.pais}")
    print(f"  Temperatura: {c.temperatura:.1f} °C")
    print(f"  Estado:      {c.estado}")
    print(f"  Humedad:     {c.humedad} %")
    print(f"  Recomendación: {c.recomendacion()}")
    mostrar_origen(resultado)


def consultar_cambio(usuario):
    moneda = pedir_texto("Moneda (USD o EUR): ")
    resultado = externo.consultar_cambio(usuario, moneda)
    t = resultado.datos
    print(f"\n  {t.nombre}: 1 {t.codigo} = ${t.valor:,.2f} CLP (valor del {t.fecha_valor})")
    mostrar_origen(resultado)


def calcular_pago(usuario):
    empleado = empleados.obtener_por_id(pedir_entero("ID del empleado: "))
    moneda = pedir_texto("Moneda de pago (USD o EUR): ")
    pago = externo.calcular_pago(usuario, empleado, moneda)
    print(f"\n  Empleado: {empleado.nombre}")
    print(f"  Salario base: ${pago.salario_clp:,.0f} CLP")
    print(f"  Tipo de cambio: 1 {pago.moneda} = ${pago.cambio.datos.valor:,.2f} CLP "
          f"(valor del {pago.cambio.datos.fecha_valor})")
    print(f"  Pago equivalente: {pago.monto:,.2f} {pago.moneda}")
    mostrar_origen(pago.cambio)


def sincronizar_datos(usuario):
    informe = externo.sincronizar(usuario)
    print("\nActualización de datos externos")
    for moneda, resultado in informe["cambios"]:
        origen = "en vivo" if resultado.en_vivo else "datos locales"
        print(f"  {moneda}: ${resultado.datos.valor:,.2f} CLP ({origen}, {describir_antiguedad(resultado.obtenido_en)})")
    for ciudad, resultado in informe["climas"]:
        origen = "en vivo" if resultado.en_vivo else "datos locales"
        c = resultado.datos
        print(f"  {ciudad}: {c.temperatura:.1f} °C, {c.estado} ({origen}, {describir_antiguedad(resultado.obtenido_en)})")
    for mensaje in informe["errores"]:
        print(f"  No se pudo actualizar -> {mensaje}")
    print(f"Registros guardados: clima = {informe['total_clima']}, tipo_cambio = {informe['total_cambio']}")


def listar_usuarios(usuario):
    for u in usuarios.listar_todos():
        print(" ", u.descripcion())


def submenu(titulo, opciones):
    while True:
        print(f"\n--- {titulo} ---")
        for clave, (texto, _) in opciones.items():
            print(f"{clave}. {texto}")
        print("0. Volver")
        eleccion = input("Opción: ").strip()
        if eleccion == "0":
            return
        if eleccion not in opciones:
            print("Opción no válida.")
            continue
        ejecutar_accion(opciones[eleccion][1])


def ejecutar_accion(accion, *args):
    try:
        accion(*args)
    except EcoTechError as error:
        print(f"Error: {error}")
    except EOFError:
        raise   # cierre de la entrada: lo maneja main()
    except Exception:
        # último recurso: el detalle técnico va al log, el usuario solo ve un mensaje genérico
        logger.exception("Error inesperado al ejecutar una acción")
        print("Ocurrió un error inesperado. Intente nuevamente o contacte al administrador.")


MENU_PRINCIPAL = [
    ("perfil", "Ver mi perfil", ver_perfil),
    ("horas", "Registrar horas", registrar_horas),
    ("horas", "Ver mis horas", ver_mis_registros),
    ("empleados", "Gestionar empleados", menu_empleados),
    ("departamentos", "Gestionar departamentos", menu_departamentos),
    ("proyectos", "Gestionar proyectos", menu_proyectos),
    ("informes", "Generar informe de horas", generar_informe),
    ("usuarios", "Ver usuarios del sistema", listar_usuarios),
    ("clima", "Consultar clima de una ciudad", consultar_clima),
    ("pagos", "Consultar tipo de cambio", consultar_cambio),
    ("pagos", "Calcular pago internacional de un empleado", calcular_pago),
    ("pagos", "Actualizar datos externos (clima y monedas)", sincronizar_datos),
]


def menu_principal(usuario):
    opciones = [op for op in MENU_PRINCIPAL if usuario.tiene_acceso(op[0])]
    while True:
        print("\n===== EcoTech Solutions =====")
        for i, (_, texto, _) in enumerate(opciones, start=1):
            print(f"{i}. {texto}")
        print("0. Salir")
        eleccion = input("Opción: ").strip()
        if eleccion == "0":
            print("Hasta luego.")
            return
        if not eleccion.isdigit() or not 1 <= int(eleccion) <= len(opciones):
            print("Opción no válida.")
            continue
        if not usuario.sesion_activa():
            print("Su sesión expiró por inactividad. Vuelva a iniciar el programa.")
            return
        ejecutar_accion(opciones[int(eleccion) - 1][2], usuario)


def main():
    configurar_logging()
    try:
        inicializar_bd()
        crear_admin_inicial()
        print("\nSistema de Gestión de Empleados - EcoTech Solutions")
        usuario = iniciar_sesion()
        print(f"Bienvenido/a, {usuario.nombre_usuario}.")
        if "--sincronizar" in sys.argv:
            # modo script: inicia sesión, actualiza datos externos y termina (útil para ejecutarlo dos veces)
            if not usuario.tiene_acceso("pagos"):
                raise AccesoDenegadoError("Solo un administrador puede actualizar los datos externos.")
            ejecutar_accion(sincronizar_datos, usuario)
            return
        menu_principal(usuario)
    except EcoTechError as error:
        print(f"Error: {error}")
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma cerrado por el usuario.")
    except Exception:
        logger.exception("Error inesperado en el programa")
        print("Ocurrió un error inesperado y el programa se cerrará. Revise logs/ecotech.log.")
        sys.exit(1)


if __name__ == "__main__":
    main()
