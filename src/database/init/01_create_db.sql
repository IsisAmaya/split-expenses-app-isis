-- Script de inicialización de la base de datos.
-- Se ejecuta automáticamente la primera vez que se crea el contenedor.

-- La DB "splitwise" ya se crea via POSTGRES_DB env var.
-- Aquí van extensiones o configuraciones adicionales si se necesitan.

-- Habilitar extensión UUID si se necesita generar UUIDs desde SQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
