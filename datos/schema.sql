PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario  TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    rol             TEXT NOT NULL CHECK (rol IN ('ADMIN', 'EMPLEADO'))
);

CREATE TABLE IF NOT EXISTS administrador (
    id_usuario        INTEGER PRIMARY KEY,
    area_responsable  TEXT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS departamento (
    id_departamento  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre           TEXT NOT NULL UNIQUE,
    id_gerente       INTEGER,
    FOREIGN KEY (id_gerente) REFERENCES empleado(id_usuario) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS empleado (
    id_usuario             INTEGER PRIMARY KEY,
    nombre                 TEXT NOT NULL,
    direccion              TEXT NOT NULL,
    telefono               TEXT NOT NULL,
    email                  TEXT NOT NULL UNIQUE,
    fecha_inicio_contrato  TEXT NOT NULL,
    salario                REAL NOT NULL CHECK (salario > 0),
    id_departamento        INTEGER,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_departamento) REFERENCES departamento(id_departamento) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS proyecto (
    id_proyecto   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL UNIQUE,
    descripcion   TEXT,
    fecha_inicio  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS empleado_proyecto (
    id_usuario   INTEGER NOT NULL,
    id_proyecto  INTEGER NOT NULL,
    PRIMARY KEY (id_usuario, id_proyecto),
    FOREIGN KEY (id_usuario) REFERENCES empleado(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS registro_tiempo (
    id_registro        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario         INTEGER NOT NULL,
    id_proyecto        INTEGER NOT NULL,
    fecha              TEXT NOT NULL,
    horas_trabajadas   REAL NOT NULL CHECK (horas_trabajadas > 0 AND horas_trabajadas <= 24),
    descripcion_tarea  TEXT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES empleado(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto) ON DELETE CASCADE
);

-- Datos que vienen de APIs externas. Se guardan para poder usarlos si la API falla (Plan B).
-- UNIQUE + ON CONFLICT en el INSERT hace que ejecutar dos veces no duplique registros.
CREATE TABLE IF NOT EXISTS clima (
    id_clima         INTEGER PRIMARY KEY AUTOINCREMENT,
    clave_busqueda   TEXT NOT NULL UNIQUE,
    ciudad_consulta  TEXT NOT NULL,
    pais_consulta    TEXT NOT NULL,
    ciudad           TEXT NOT NULL,
    pais             TEXT NOT NULL,
    latitud          REAL NOT NULL,
    longitud         REAL NOT NULL,
    temperatura      REAL NOT NULL,
    humedad          INTEGER NOT NULL CHECK (humedad BETWEEN 0 AND 100),
    codigo_tiempo    INTEGER NOT NULL,
    fecha_api        TEXT NOT NULL,
    obtenido_en      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tipo_cambio (
    id_cambio    INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo       TEXT NOT NULL,
    nombre       TEXT NOT NULL,
    valor        REAL NOT NULL CHECK (valor > 0),
    fecha_valor  TEXT NOT NULL,
    obtenido_en  TEXT NOT NULL,
    UNIQUE (codigo, fecha_valor)
);
