# Sistema de Gestión de Empleados - EcoTech Solutions

ES2 TI3021 Programación Orientada a Objeto Seguro - Franco Isla

Aplicación CRUD por consola en Python, con base de datos SQLite (librería oficial `sqlite3`).
No necesita instalar ningún servidor de base de datos: la base se crea sola en `datos/ecotech.db`.

## Requisitos

- Python 3.10 o superior (probado con Python 3.13).
- Para revisar si está instalado, abrir una terminal y escribir `python --version`.
  Si dice "Python was not found", instalarlo desde https://www.python.org/downloads/
  y en la primera pantalla del instalador marcar **"Add python.exe to PATH"**.
  Después cerrar y volver a abrir la terminal (o VS Code).

## Pasos para ejecutarlo (Windows)

Todos los comandos se escriben en una terminal abierta **dentro de la carpeta `ecotech_franco_isla`**
(en VS Code: Archivo > Abrir carpeta, y luego Terminal > Nueva terminal).

**1. Crear y activar el entorno virtual**

```
python -m venv venv
venv\Scripts\activate
```

Si al activar aparece el error "la ejecución de scripts está deshabilitada en este sistema",
ejecutar una sola vez este comando y volver a activar:

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
venv\Scripts\activate
```

Cuando está activo, la línea de la terminal empieza con `(venv)`.

**2. Instalar la dependencia**

```
pip install -r requirements.txt
```

(Instala `python-dotenv`, `requests` y `bcrypt`; `sqlite3` ya viene con Python.)

**3. Crear el archivo `.env`**

```
copy .env.example .env
```

Abrir el archivo `.env` y, si se quiere, cambiar la contraseña del administrador
(mínimo 8 caracteres) y **guardar con Ctrl+S**. Si no se cambia, la contraseña es `cambiar_esta_clave`.

> Importante: hacer esto **antes** de ejecutar el programa por primera vez.
> La contraseña del `.env` solo se usa una vez, cuando se crea el administrador.
> Si se cambia después, ver la sección "Problemas comunes".

**4. Cargar datos de prueba (recomendado)**

```
python -m pruebas.cargar_datos_prueba
```

Crea las tablas y agrega 2 departamentos, 2 empleados, 1 proyecto y 2 registros de horas.

**5. Ejecutar el sistema**

```
python main.py
```

La primera vez aparece el mensaje "Se creó el administrador inicial 'admin'" y luego pide usuario y contraseña.

## Usuarios para entrar

| Usuario     | Contraseña                                         | Qué puede hacer |
|-------------|----------------------------------------------------|-----------------|
| `admin`     | la del `.env` (por defecto `cambiar_esta_clave`)   | Gestionar empleados, departamentos, proyectos, informes y ver usuarios |
| `ana.perez` | `Clave1234`                                        | Ver su perfil, registrar horas y ver sus horas |
| `luis.soto` | `Clave1234`                                        | Igual que ana.perez |

Al escribir la contraseña **no se ve nada en pantalla** (ni asteriscos). Es normal: se oculta por seguridad.
Escribirla con el teclado (no pegar) y presionar Enter.

## Evaluación 3: APIs externas, seguridad y resiliencia

Después de iniciar sesión hay opciones nuevas (según el rol):

| Opción | Quién | Qué hace |
|--------|-------|----------|
| Consultar clima de una ciudad | admin y empleados | Temperatura, estado y humedad (Open-Meteo) |
| Consultar tipo de cambio | admin | Dólar o euro en pesos chilenos (mindicador.cl) |
| Calcular pago internacional | admin | Convierte el salario de un empleado a USD o EUR |
| Actualizar datos externos | admin | Actualiza monedas y las ciudades de `CIUDADES_SINCRONIZAR` |

- **Plan B:** si la API falla o no hay internet, se muestran los datos guardados en la base con su fecha y antigüedad (`obtenido_en`).
- **Dos ejecuciones seguidas** no duplican registros: `python main.py --sincronizar` (pide login de admin, actualiza y termina).
- **Contraseñas:** hash `bcrypt` con salt. Si ya existía `datos/ecotech.db` de la ES2, borrarla y volver a ejecutar `python -m pruebas.cargar_datos_prueba`.
- **Pruebas automáticas** (servidor falso local, no usan internet): `python -m pruebas.prueba_api_cliente`
- **Ver usuarios guardados** (sin claves en texto plano): `python -m pruebas.ver_usuarios_bd`
- Errores técnicos se registran en `logs/ecotech.log`. Auditoría de IA: `bitacora_ia.md`.

## Pruebas de seguridad

```
python -m pruebas.prueba_inyeccion
python -m pruebas.prueba_rollback
```

- `prueba_inyeccion`: intenta buscar y hacer login con `' OR '1'='1`; debe devolver 0 resultados.
- `prueba_rollback`: intenta guardar un empleado con un departamento que no existe; el usuario no debe quedar guardado.

## En Linux / Mac

Los mismos pasos, cambiando estos comandos:

```
python3 -m venv venv
source venv/bin/activate
cp .env.example .env
```

## Problemas comunes

**"Usuario o contraseña incorrectos" con admin aunque la clave esté bien**
El administrador se crea la primera vez que se ejecuta el programa, con la contraseña que tenía el `.env` en ese momento.
Si después se cambió el `.env`, hay que borrar la base de datos para que se cree de nuevo:

```
del datos\ecotech.db
python -m pruebas.cargar_datos_prueba
python main.py
```

(En Linux/Mac: `rm datos/ecotech.db`.)

**"Python was not found"** → Python no está instalado o no se marcó "Add python.exe to PATH" (ver Requisitos).

**"pip no se reconoce"** → falta instalar Python o activar el entorno virtual (paso 1).

**"Falta ECOTECH_ADMIN_PASSWORD en el archivo .env"** → no se hizo el paso 3, o la contraseña tiene menos de 8 caracteres.

**"Los datos de prueba ya estaban cargados"** → no es un error, solo avisa que ya existen.

## Estructura del proyecto

- `dominio/`: clases del modelo (Usuario, Empleado, Administrador, Departamento, Proyecto, RegistroTiempo, Informe) y excepciones. No tienen SQL.
- `repositorio/`: conexión a la base de datos y todas las consultas (CRUD parametrizado).
- `datos/schema.sql`: creación de tablas con llaves primarias y foráneas.
- `pruebas/`: datos de prueba, prueba de inyección SQL y prueba de rollback.
- `api_cliente.py`: cliente HTTP (timeout, reintentos, backoff, códigos de estado).
- `servicio_externo.py`: une API, deserializador y base de datos, con Plan B y control de acceso.
- `dominio/deserializador.py`, `dominio/datos_externos.py`, `dominio/validaciones.py`: validación y conversión de datos.
- `main.py`: login y menú por consola.
- Los informes generados se guardan en la carpeta `informes/`.
