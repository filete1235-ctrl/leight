-- CREAR BASE DE DATOS Y TABLAS COMPLETAS PARA CONTROL DE ACCESO
CREATE DATABASE IF NOT EXISTS `control_acceso` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `control_acceso`;

-- TABLA DE ROLES
CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(50) NOT NULL UNIQUE,
    `descripcion` TEXT,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA DE PERMISOS
CREATE TABLE IF NOT EXISTS `permisos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(100) NOT NULL UNIQUE,
    `descripcion` TEXT,
    `modulo` VARCHAR(50) NOT NULL,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA INTERMEDIA ROL-PERMISOS
CREATE TABLE IF NOT EXISTS `rol_permisos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `rol_id` INT NOT NULL,
    `permiso_id` INT NOT NULL,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`rol_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permiso_id`) REFERENCES `permisos`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_rol_permiso` (`rol_id`, `permiso_id`)
);

-- TABLA DE USUARIOS
CREATE TABLE IF NOT EXISTS `usuarios` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(100) NOT NULL,
    `correo` VARCHAR(100) NOT NULL UNIQUE,
    `contrasena` VARCHAR(255) NOT NULL,
    `rol_id` INT NOT NULL,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `estado` ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    FOREIGN KEY (`rol_id`) REFERENCES `roles`(`id`)
);

-- TABLA DE VISITANTES
CREATE TABLE IF NOT EXISTS `visitantes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(100) NOT NULL,
    `identificacion` VARCHAR(50) NOT NULL UNIQUE,
    `empresa` VARCHAR(100),
    `motivo` TEXT,
    `fecha_registro` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `estado` ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo'
);

-- TABLA DE CREDENCIALES
CREATE TABLE IF NOT EXISTS `credenciales` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `visitante_id` INT NOT NULL,
    `codigo` VARCHAR(50) NOT NULL UNIQUE,
    `estado` ENUM('activa', 'inactiva') DEFAULT 'activa',
    `fecha_emision` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_expiracion` DATETIME,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`visitante_id`) REFERENCES `visitantes`(`id`)
);

-- TABLA DE ACCESOS
CREATE TABLE IF NOT EXISTS `accesos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `usuario_id` INT,
    `visitante_id` INT,
    `tipo` ENUM('entrada', 'salida') NOT NULL,
    `fecha_hora` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `autorizado` BOOLEAN DEFAULT TRUE,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`usuario_id`) REFERENCES `usuarios`(`id`),
    FOREIGN KEY (`visitante_id`) REFERENCES `visitantes`(`id`)
);

-- TABLA DE ALERTAS
CREATE TABLE IF NOT EXISTS `alertas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `descripcion` VARCHAR(255) NOT NULL,
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `nivel` ENUM('bajo', 'medio', 'alto') DEFAULT 'medio',
    `usuario_id` INT,
    `visitante_id` INT,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`usuario_id`) REFERENCES `usuarios`(`id`),
    FOREIGN KEY (`visitante_id`) REFERENCES `visitantes`(`id`)
);

-- INSERTAR ROLES BÁSICOS
INSERT IGNORE INTO `roles` (`id`, `nombre`, `descripcion`) VALUES
(1, 'administrador', 'Administrador completo del sistema con todos los permisos'),
(2, 'guardia', 'Personal de seguridad que gestiona accesos y visitantes'),
(3, 'recepcion', 'Personal de recepción con permisos limitados'),
(4, 'supervisor', 'Supervisor con permisos de visualización y reportes');

-- INSERTAR PERMISOS DEL SISTEMA
INSERT IGNORE INTO `permisos` (`nombre`, `descripcion`, `modulo`) VALUES
-- Módulo Dashboard
('ver_dashboard', 'Permite ver el dashboard principal', 'dashboard'),

-- Módulo Visitantes
('ver_visitantes', 'Permite ver la lista de visitantes', 'visitantes'),
('crear_visitantes', 'Permite crear nuevos visitantes', 'visitantes'),
('editar_visitantes', 'Permite editar visitantes existentes', 'visitantes'),
('eliminar_visitantes', 'Permite eliminar visitantes', 'visitantes'),
('cambiar_estado_visitantes', 'Permite activar/desactivar visitantes', 'visitantes'),
('generar_credenciales', 'Permite generar credenciales para visitantes', 'visitantes'),

-- Módulo Control de Acceso
('control_acceso', 'Permite registrar entradas y salidas', 'acceso'),
('ver_registro_accesos', 'Permite ver el historial de accesos', 'acceso'),

-- Módulo Usuarios
('ver_usuarios', 'Permite ver la lista de usuarios', 'usuarios'),
('crear_usuarios', 'Permite crear nuevos usuarios', 'usuarios'),
('editar_usuarios', 'Permite editar usuarios existentes', 'usuarios'),
('eliminar_usuarios', 'Permite eliminar usuarios', 'usuarios'),
('cambiar_estado_usuarios', 'Permite activar/desactivar usuarios', 'usuarios'),
('asignar_roles', 'Permite asignar roles a usuarios', 'usuarios'),

-- Módulo Alertas
('ver_alertas', 'Permite ver las alertas del sistema', 'alertas'),
('crear_alertas', 'Permite crear nuevas alertas', 'alertas'),
('editar_alertas', 'Permite editar alertas existentes', 'alertas'),
('eliminar_alertas', 'Permite eliminar alertas', 'alertas'),

-- Módulo Reportes
('ver_reportes', 'Permite ver reportes', 'reportes'),
('generar_reportes', 'Permite generar nuevos reportes', 'reportes'),
('exportar_reportes', 'Permite exportar reportes a PDF/CSV', 'reportes'),

-- Módulo Configuración
('gestionar_roles', 'Permite gestionar roles del sistema', 'configuracion'),
('gestionar_permisos', 'Permite gestionar permisos del sistema', 'configuracion'),
('configurar_sistema', 'Permite configurar parámetros del sistema', 'configuracion');

-- ASIGNAR PERMISOS AL ROL ADMINISTRADOR (TODOS LOS PERMISOS)
INSERT IGNORE INTO `rol_permisos` (`rol_id`, `permiso_id`)
SELECT 1, `id` FROM `permisos`;

-- ASIGNAR PERMISOS AL ROL GUARDIA
INSERT IGNORE INTO `rol_permisos` (`rol_id`, `permiso_id`)
SELECT 2, `id` FROM `permisos` 
WHERE `nombre` IN (
    'ver_dashboard',
    'ver_visitantes',
    'crear_visitantes',
    'editar_visitantes',
    'cambiar_estado_visitantes',
    'generar_credenciales',
    'control_acceso',
    'ver_registro_accesos',
    'ver_alertas',
    'crear_alertas'
);

-- ASIGNAR PERMISOS AL ROL RECEPCIÓN
INSERT IGNORE INTO `rol_permisos` (`rol_id`, `permiso_id`)
SELECT 3, `id` FROM `permisos` 
WHERE `nombre` IN (
    'ver_dashboard',
    'ver_visitantes',
    'crear_visitantes',
    'editar_visitantes',
    'generar_credenciales',
    'control_acceso',
    'ver_alertas',
    'crear_alertas'
);

-- ASIGNAR PERMISOS AL ROL SUPERVISOR
INSERT IGNORE INTO `rol_permisos` (`rol_id`, `permiso_id`)
SELECT 4, `id` FROM `permisos` 
WHERE `nombre` IN (
    'ver_dashboard',
    'ver_visitantes',
    'ver_registro_accesos',
    'ver_usuarios',
    'ver_alertas',
    'ver_reportes',
    'generar_reportes',
    'exportar_reportes'
);

-- CREAR USUARIO ADMINISTRADOR POR DEFECTO
INSERT IGNORE INTO `usuarios` (`nombre`, `correo`, `contrasena`, `rol_id`, `estado`) VALUES
('Administrador Principal', 'admin@controlacceso.com', SHA2('admin123', 256), 1, 'activo'),
('Guardia de Seguridad', 'guardia@controlacceso.com', SHA2('guardia123', 256), 2, 'activo'),
('Recepcionista', 'recepcion@controlacceso.com', SHA2('recepcion123', 256), 3, 'activo'),
('Supervisor', 'supervisor@controlacceso.com', SHA2('supervisor123', 256), 4, 'activo');

-- INSERTAR ALGUNOS VISITANTES DE EJEMPLO
INSERT IGNORE INTO `visitantes` (`nombre`, `identificacion`, `empresa`, `motivo`, `estado`) VALUES
('Juan Pérez', 'V-12345678', 'Empresa ABC', 'Reunión de negocios', 'activo'),
('María García', 'V-87654321', 'Compañía XYZ', 'Entrega de documentos', 'activo'),
('Carlos López', 'V-11223344', 'Corporación DEF', 'Visita técnica', 'activo'),
('Ana Martínez', 'V-44332211', 'Industrias GHI', 'Entrevista de trabajo', 'activo');

-- GENERAR CREDENCIALES PARA LOS VISITANTES
INSERT IGNORE INTO `credenciales` (`visitante_id`, `codigo`, `estado`, `fecha_expiracion`)
SELECT 
    `id`, 
    UPPER(SUBSTRING(MD5(RAND()), 1, 8)),
    'activa',
    DATE_ADD(NOW(), INTERVAL 8 HOUR)
FROM `visitantes`;

-- INSERTAR ALGUNOS ACCESOS DE EJEMPLO
INSERT IGNORE INTO `accesos` (`usuario_id`, `visitante_id`, `tipo`, `autorizado`) VALUES
(2, 1, 'entrada', 1),
(2, 2, 'entrada', 1),
(2, 1, 'salida', 1),
(2, 3, 'entrada', 1);

-- INSERTAR ALGUNAS ALERTAS DE EJEMPLO
INSERT IGNORE INTO `alertas` (`descripcion`, `nivel`, `usuario_id`) VALUES
('Intento de acceso fuera del horario permitido', 'medio', 2),
('Visitante con credencial expirada intentó ingresar', 'alto', 2),
('Acceso denegado por identificación no válida', 'alto', 2);

-- CREAR ÍNDICES PARA MEJOR RENDIMIENTO
CREATE INDEX IF NOT EXISTS `idx_usuarios_estado` ON `usuarios`(`estado`);
CREATE INDEX IF NOT EXISTS `idx_usuarios_rol` ON `usuarios`(`rol_id`);
CREATE INDEX IF NOT EXISTS `idx_visitantes_estado` ON `visitantes`(`estado`);
CREATE INDEX IF NOT EXISTS `idx_visitantes_identificacion` ON `visitantes`(`identificacion`);
CREATE INDEX IF NOT EXISTS `idx_credenciales_estado` ON `credenciales`(`estado`);
CREATE INDEX IF NOT EXISTS `idx_credenciales_codigo` ON `credenciales`(`codigo`);
CREATE INDEX IF NOT EXISTS `idx_credenciales_expiracion` ON `credenciales`(`fecha_expiracion`);
CREATE INDEX IF NOT EXISTS `idx_accesos_fecha` ON `accesos`(`fecha_hora`);
CREATE INDEX IF NOT EXISTS `idx_accesos_visitante` ON `accesos`(`visitante_id`);
CREATE INDEX IF NOT EXISTS `idx_alertas_fecha` ON `alertas`(`fecha`);
CREATE INDEX IF NOT EXISTS `idx_alertas_nivel` ON `alertas`(`nivel`);
CREATE INDEX IF NOT EXISTS `idx_rol_permisos_rol` ON `rol_permisos`(`rol_id`);
CREATE INDEX IF NOT EXISTS `idx_rol_permisos_permiso` ON `rol_permisos`(`permiso_id`);

-- CONSULTA PARA VERIFICAR LA ESTRUCTURA COMPLETA
SELECT 
    'Roles' as tabla,
    COUNT(*) as total
FROM `roles`
UNION ALL
SELECT 
    'Permisos',
    COUNT(*)
FROM `permisos`
UNION ALL
SELECT 
    'Usuarios',
    COUNT(*)
FROM `usuarios`
UNION ALL
SELECT 
    'Visitantes',
    COUNT(*)
FROM `visitantes`
UNION ALL
SELECT 
    'Credenciales',
    COUNT(*)
FROM `credenciales`
UNION ALL
SELECT 
    'Accesos',
    COUNT(*)
FROM `accesos`
UNION ALL
SELECT 
    'Alertas',
    COUNT(*)
FROM `alertas`
UNION ALL
SELECT 
    'Permisos por Rol',
    COUNT(*)
FROM `rol_permisos`;

-- CONSULTA PARA VER PERMISOS POR ROL
SELECT 
    r.`nombre` as rol,
    COUNT(rp.`permiso_id`) as total_permisos,
    GROUP_CONCAT(p.`modulo` SEPARATOR ', ') as modulos
FROM `roles` r
LEFT JOIN `rol_permisos` rp ON r.`id` = rp.`rol_id`
LEFT JOIN `permisos` p ON rp.`permiso_id` = p.`id`
GROUP BY r.`id`, r.`nombre`
ORDER BY r.`id`;