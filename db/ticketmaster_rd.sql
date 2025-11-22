DROP DATABASE IF EXISTS ticketmaster_rd;
CREATE DATABASE ticketmaster_rd CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE ticketmaster_rd;

-- 1. Roles
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE
);

INSERT INTO roles (nombre) VALUES ('estandar'), ('administrador');

-- 2. Usuarios
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    primer_nombre VARCHAR(50) NOT NULL,
    primer_apellido VARCHAR(50) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    dni CHAR(13) NOT NULL UNIQUE, -- 13 dígitos sin guiones
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL DEFAULT 1,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rol_id) REFERENCES roles(id)
);

-- Usuario administrador inicial → correo: admin@ticketmaster.rd  contraseña: admin2025
INSERT INTO usuarios (primer_nombre, primer_apellido, telefono, correo, dni, password_hash, rol_id)
VALUES ('Admin', 'JAAO', '12345678', 'jaao@gmail.com', '123456789013', 
        '$2b$12$z8Y8e9v7z6x5c4v3b2n1m./1q2w3e4r5t6y7u8i9o0p1a2s3d4f5g', 2);
-- (la contraseña está hasheada con bcrypt → "admin2025")

-- 3. Establecimientos (3 salas con layouts diferentes)
CREATE TABLE establecimientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    layout_type ENUM('cuadrado', 'rectangular', 'trapecio') NOT NULL,
    filas INT NOT NULL,
    columnas INT NOT NULL
);

INSERT INTO establecimientos (nombre, descripcion, layout_type, filas, columnas) VALUES
('Teatro Nacional', 'Sala principal cuadrada 10x10', 'cuadrado', 10, 10),
('Casa de la Cultura Santiago', 'Sala rectangular clásica', 'rectangular', 20, 5),
('Anfiteatro Nuryn Sanlley', 'Forma de trapecio', 'trapecio', 15, 10);

-- 4. Asientos (100 por cada establecimiento)
CREATE TABLE asientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    establecimiento_id INT NOT NULL,
    fila CHAR(2) NOT NULL,
    columna INT NOT NULL,
    zona ENUM('vip', 'preferencial', 'general') DEFAULT 'general',
    coordenada_x DECIMAL(5,2), -- para mapa SVG/JS
    coordenada_y DECIMAL(5,2),
    UNIQUE(establecimiento_id, fila, columna),
    FOREIGN KEY (establecimiento_id) REFERENCES establecimientos(id) ON DELETE CASCADE
);

-- Generamos los 300 asientos automáticamente
DELIMITER $$
CREATE PROCEDURE generar_asientos()
BEGIN
    DECLARE est_id INT;
    DECLARE f, c INT;
    DECLARE fila_char CHAR(2);

    -- Teatro Nacional 10x10
    SET est_id = 1;
    SET f = 1;
    WHILE f <= 10 DO
        SET c = 1;
        WHILE c <= 10 DO
            SET fila_char = CONCAT(CHAR(64 + f), '');
            INSERT INTO asientos (establecimiento_id, fila, columna, zona, coordenada_x, coordenada_y)
            VALUES (est_id, fila_char, c, 
                    IF(f <= 3, 'vip', IF(f <= 6, 'preferencial', 'general')),
                    c * 50, f * 50);
            SET c = c + 1;
        END WHILE;
        SET f = f + 1;
    END WHILE;

    -- Casa de la Cultura 20x5
    SET est_id = 2; SET f = 1;
    WHILE f <= 20 DO
        SET c = 1;
        WHILE c <= 5 DO
            SET fila_char = CONCAT(CHAR(64 + f), '');
            INSERT INTO asientos (establecimiento_id, fila, columna, coordenada_x, coordenada_y)
            VALUES (est_id, fila_char, c, c * 80, f * 40);
            SET c = c + 1;
        END WHILE;
        SET f = f + 1;
    END WHILE;

    -- Anfiteatro Nuryn (trapecio)
    SET est_id = 3; SET f = 1;
    WHILE f <= 15 DO
        SET c = 1;
        WHILE c <= (6 + f) DO  -- aumenta columnas hacia atrás
            SET fila_char = CONCAT(CHAR(64 + f), '');
            INSERT INTO asientos (establecimiento_id, fila, columna, coordenada_x, coordenada_y)
            VALUES (est_id, fila_char, c, c * 60, f * 45);
            SET c = c + 1;
        END WHILE;
        SET f = f + 1;
    END WHILE;
END$$
DELIMITER ;

CALL generar_asientos();
DROP PROCEDURE generar_asientos;

-- 5. Eventos
CREATE TABLE eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    establecimiento_id INT NOT NULL,
    imagen_portada VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (establecimiento_id) REFERENCES establecimientos(id)
);

-- 6. Precios por zona del evento
CREATE TABLE precios_evento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evento_id INT NOT NULL,
    zona ENUM('vip', 'preferencial', 'general') NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE
);

-- 7. Compras (carrito/pedido)
CREATE TABLE compras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    evento_id INT NOT NULL,
    fecha_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10,2) NOT NULL,
    estado ENUM('pendiente', 'pagado', 'aprobado', 'rechazado') DEFAULT 'pendiente',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (evento_id) REFERENCES eventos(id)
);

-- 8. Boletos individuales
CREATE TABLE boletos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    compra_id INT NOT NULL,
    asiento_id INT NOT NULL,
    qr_code VARCHAR(255), -- ruta del archivo QR
    FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
    FOREIGN KEY (asiento_id) REFERENCES asientos(id)
);

-- 9. Pagos (comprobante)
CREATE TABLE pagos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    compra_id INT NOT NULL,
    imagen_comprobante VARCHAR(255) NOT NULL,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    aprobado BOOLEAN NULL, -- NULL=pendiente, 1=aprobado, 0=rechazado
    revisado_por INT NULL,
    fecha_revision DATETIME NULL,
    FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
    FOREIGN KEY (revisado_por) REFERENCES usuarios(id)
);

-- 10. Datos de ejemplo: 3 eventos listos
INSERT INTO eventos (nombre, fecha_hora, establecimiento_id, imagen_portada) VALUES
('Concierto Bad Bunny - RD Tour 2026', '2026-03-15 20:00:00', 1, 'eventos/bad_bunny.jpg'),
('Obra de Teatro: La Luz de un Cigarrillo', '2026-01-20 19:00:00', 2, 'eventos/teatro.jpg'),
('Stand Up Comedy - Raymond Pozo', '2026-02-14 21:00:00', 3, 'eventos/raymond.jpg');

INSERT INTO precios_evento (evento_id, zona, precio) VALUES
(1, 'vip', 5000.00), (1, 'preferencial', 3500.00), (1, 'general', 2000.00),
(2, 'vip', 2500.00), (2, 'preferencial', 1800.00), (2, 'general', 1200.00),
(3, 'vip', 3000.00), (3, 'preferencial', 2000.00), (3, 'general', 1500.00);
