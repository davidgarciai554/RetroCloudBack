-- Activa el soporte de claves foráneas
PRAGMA foreign_keys = ON;

-- 1. Tabla de roles
CREATE TABLE IF NOT EXISTS roles (
  id   INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT    NOT NULL UNIQUE
);

-- Inserta los roles básicos
INSERT INTO roles (nombre) VALUES
  ('ADMIN'),
  ('USER');

-- 2. Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre      TEXT    NOT NULL UNIQUE,
  contraseña  TEXT    NOT NULL,
  rol_id      INTEGER NOT NULL,
  FOREIGN KEY (rol_id) REFERENCES roles(id)
);

-- 3. Tabla de empresas
CREATE TABLE IF NOT EXISTS EMPRESAS (
  ID INTEGER PRIMARY KEY AUTOINCREMENT,
  NOMBRE TEXT UNIQUE
);

-- 4. Tabla de consolas
CREATE TABLE IF NOT EXISTS CONSOLAS (
  ID INTEGER PRIMARY KEY,
  NOMBRE TEXT,
  EMPRESA_ID INTEGER,
  NUM_JUEGOS_API INTEGER,
  FOREIGN KEY (EMPRESA_ID) REFERENCES EMPRESAS(ID)
);

-- 5. Tabla de juegos
CREATE TABLE IF NOT EXISTS JUEGOS (
  ID INTEGER PRIMARY KEY,
  NOMBRE TEXT,
  FECHA_LANZAMIENTO TEXT,
  DESCRIPCION TEXT,
  PUBLISHERS TEXT
);

-- 6. Tabla de relación juegos-consolas con ruta en la nube
CREATE TABLE IF NOT EXISTS JUEGOS_CONSOLAS (
  JUEGO_ID INTEGER,
  CONSOLA_ID INTEGER,
  RUTA_NUBE TEXT DEFAULT '',
  PRIMARY KEY (JUEGO_ID, CONSOLA_ID),
  FOREIGN KEY (JUEGO_ID) REFERENCES JUEGOS(ID),
  FOREIGN KEY (CONSOLA_ID) REFERENCES CONSOLAS(ID)
);
