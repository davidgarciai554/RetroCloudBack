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
