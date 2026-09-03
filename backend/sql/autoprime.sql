-- =============================================================================
--  AutoPrime - Base de datos relacional
--  Tercer avance - Proyecto React | SENA - Ficha 3406211
--  Jose Matias Agudelo Bolivar
--
--  Ejecutar:  mysql -u root < backend/sql/autoprime.sql
-- =============================================================================

DROP DATABASE IF EXISTS autoprime;
CREATE DATABASE autoprime
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE autoprime;

-- -----------------------------------------------------------------------------
-- roles
-- -----------------------------------------------------------------------------
CREATE TABLE roles (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(30)  NOT NULL UNIQUE,
  descripcion VARCHAR(150) NOT NULL
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- permisos (que puede hacer cada rol)
-- -----------------------------------------------------------------------------
CREATE TABLE permisos (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(60)  NOT NULL UNIQUE,
  descripcion VARCHAR(150) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE rol_permiso (
  rol_id     INT NOT NULL,
  permiso_id INT NOT NULL,
  PRIMARY KEY (rol_id, permiso_id),
  CONSTRAINT fk_rp_rol     FOREIGN KEY (rol_id)     REFERENCES roles(id)    ON DELETE CASCADE,
  CONSTRAINT fk_rp_permiso FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- usuarios
--   Los campos reflejan el formulario de registro del segundo avance.
--   La contrasena se guarda SIEMPRE como hash bcrypt, nunca en texto plano.
-- -----------------------------------------------------------------------------
CREATE TABLE usuarios (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  nombre           VARCHAR(40)  NOT NULL,
  apellido         VARCHAR(40)  NOT NULL,
  tipo_documento   ENUM('CC','TI','CE','PA','NIT') NOT NULL,
  numero_documento VARCHAR(15)  NOT NULL,
  direccion        VARCHAR(80)  NOT NULL,
  telefono         VARCHAR(10)  NOT NULL,
  correo           VARCHAR(60)  NOT NULL UNIQUE,
  password_hash    VARCHAR(255) NOT NULL,
  rol_id           INT          NOT NULL,
  estado           ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  creado_en        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_usuario_rol FOREIGN KEY (rol_id) REFERENCES roles(id),
  CONSTRAINT uq_documento UNIQUE (tipo_documento, numero_documento)
) ENGINE=InnoDB;

CREATE INDEX idx_usuarios_correo ON usuarios(correo);
CREATE INDEX idx_usuarios_estado ON usuarios(estado);

-- -----------------------------------------------------------------------------
-- productos (los vehiculos del catalogo)
-- -----------------------------------------------------------------------------
CREATE TABLE productos (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  slug         VARCHAR(60)  NOT NULL UNIQUE,
  marca        VARCHAR(40)  NOT NULL,
  modelo       VARCHAR(60)  NOT NULL,
  familia      ENUM('gama','edicion','coleccion') NOT NULL DEFAULT 'gama',
  base         VARCHAR(60)  NOT NULL,
  lema         VARCHAR(120) NOT NULL,
  descripcion  TEXT         NOT NULL,
  imagen       VARCHAR(120) NOT NULL,
  anio         SMALLINT     NOT NULL,
  kilometraje  INT          NOT NULL DEFAULT 0,
  precio       BIGINT       NULL,
  unidades     SMALLINT     NULL,
  motor        VARCHAR(60)  NOT NULL,
  potencia     VARCHAR(20)  NOT NULL,
  aceleracion  VARCHAR(20)  NOT NULL,
  velocidad    VARCHAR(20)  NOT NULL,
  transmision  VARCHAR(40)  NOT NULL,
  traccion     VARCHAR(20)  NOT NULL,
  estado       ENUM('disponible','vendido','inactivo') NOT NULL DEFAULT 'disponible',
  creado_en    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE INDEX idx_productos_familia ON productos(familia);
CREATE INDEX idx_productos_estado  ON productos(estado);

-- -----------------------------------------------------------------------------
-- servicios (lo que se puede agendar)
-- -----------------------------------------------------------------------------
CREATE TABLE servicios (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  nombre       VARCHAR(60)  NOT NULL,
  descripcion  VARCHAR(200) NOT NULL,
  duracion_min SMALLINT     NOT NULL DEFAULT 60,
  precio       BIGINT       NOT NULL DEFAULT 0,
  estado       ENUM('activo','inactivo') NOT NULL DEFAULT 'activo'
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- citas (agendamiento: el cliente elige fecha y hora)
--   uq_cupo evita que dos clientes tomen la misma franja para el mismo vehiculo.
-- -----------------------------------------------------------------------------
CREATE TABLE citas (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id  INT          NOT NULL,
  producto_id INT          NULL,
  servicio_id INT          NOT NULL,
  fecha       DATE         NOT NULL,
  hora        TIME         NOT NULL,
  estado      ENUM('pendiente','confirmada','cancelada','completada')
                NOT NULL DEFAULT 'pendiente',
  notas       VARCHAR(300) NULL,
  creado_en   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cita_usuario  FOREIGN KEY (usuario_id)  REFERENCES usuarios(id)  ON DELETE CASCADE,
  CONSTRAINT fk_cita_producto FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE SET NULL,
  CONSTRAINT fk_cita_servicio FOREIGN KEY (servicio_id) REFERENCES servicios(id),
  CONSTRAINT uq_cupo UNIQUE (fecha, hora, producto_id)
) ENGINE=InnoDB;

CREATE INDEX idx_citas_usuario ON citas(usuario_id);
CREATE INDEX idx_citas_fecha   ON citas(fecha);

-- =============================================================================
--  DATOS INICIALES
-- =============================================================================

INSERT INTO roles (nombre, descripcion) VALUES
  ('administrador', 'Gestiona usuarios, productos, servicios y citas'),
  ('empleado',      'Gestiona el catalogo y atiende las citas agendadas'),
  ('cliente',       'Consulta el catalogo y agenda sus propias citas');

INSERT INTO permisos (nombre, descripcion) VALUES
  ('usuarios.ver',      'Consultar el listado de usuarios'),
  ('usuarios.crear',    'Registrar usuarios'),
  ('usuarios.editar',   'Actualizar datos de usuarios'),
  ('usuarios.estado',   'Activar o inactivar usuarios'),
  ('usuarios.eliminar', 'Eliminar usuarios'),
  ('productos.ver',     'Consultar el catalogo'),
  ('productos.crear',   'Agregar vehiculos'),
  ('productos.editar',  'Actualizar vehiculos'),
  ('productos.eliminar','Eliminar vehiculos'),
  ('servicios.gestion', 'Administrar servicios'),
  ('citas.ver.todas',   'Ver todas las citas'),
  ('citas.ver.propias', 'Ver unicamente sus citas'),
  ('citas.crear',       'Agendar una cita'),
  ('citas.estado',      'Cambiar el estado de una cita');

-- administrador: todos los permisos
INSERT INTO rol_permiso (rol_id, permiso_id)
  SELECT 1, id FROM permisos;

-- empleado: catalogo, servicios y citas (no gestiona usuarios)
INSERT INTO rol_permiso (rol_id, permiso_id)
  SELECT 2, id FROM permisos
  WHERE nombre IN ('usuarios.ver','productos.ver','productos.crear','productos.editar',
                   'servicios.gestion','citas.ver.todas','citas.estado');

-- cliente: solo consulta el catalogo y maneja sus propias citas
INSERT INTO rol_permiso (rol_id, permiso_id)
  SELECT 3, id FROM permisos
  WHERE nombre IN ('productos.ver','citas.ver.propias','citas.crear');

INSERT INTO servicios (nombre, descripcion, duracion_min, precio) VALUES
  ('Prueba de manejo',          'Recorrido guiado de 45 minutos con un asesor.', 45, 0),
  ('Cotizacion formal',         'Estudio de credito y cotizacion por escrito.', 30, 0),
  ('Peritaje de 120 puntos',    'Revision tecnica completa del vehiculo.', 120, 350000),
  ('Mantenimiento programado',  'Servicio en el taller certificado.', 180, 0),
  ('Avaluo de retoma',          'Valoracion de tu vehiculo actual como parte de pago.', 60, 0);

-- Catalogo: las 10 preparaciones MANSORY.
-- Los precios son estimaciones de mercado con fines academicos; MANSORY no
-- publica tarifas. Las piezas unicas quedan en NULL ("Precio bajo consulta").
INSERT INTO productos
  (slug, marca, modelo, familia, base, lema, descripcion, imagen, anio, kilometraje,
   precio, unidades, motor, potencia, aceleracion, velocidad, transmision, traccion)
VALUES
('pugnator-tricolore','MANSORY','Pugnator Tricolore','edicion','Ferrari Purosangue',
 'El SUV que no pide permiso',
 'Carroceria completa en carbono visible sobre el primer cuatro puertas de Maranello. La bandera italiana recorre el costado en un tricolor pintado a mano que no se repetira.',
 'mansory-pugnator-perfil.webp',2024,0,NULL,1,
 '6.5 L V12 atmosferico','755 hp','3,1 s','312 km/h','Doble embrague 8 vel.','Integral'),

('phantom-viii','MANSORY','Phantom VIII','gama','Rolls-Royce Phantom',
 'Silencio, con otra voz',
 'La berlina mas solemne de Goodwood reinterpretada con paragolpes de carbono, llantas forjadas de 24 pulgadas e interior a medida. El lujo intacto; la presencia, nueva.',
 'mansory-phantom-lateral.webp',2024,0,3200000000,NULL,
 '6.75 L V12 biturbo','602 hp','5,4 s','250 km/h','Automatica 8 vel.','Trasera'),

('sf90-soft-kit','MANSORY','SF90 Soft Kit','edicion','Ferrari SF90 Stradale',
 'Mil cien caballos en blanco',
 'El hibrido enchufable mas potente de Ferrari con kit aerodinamico de carbono y electronica revisada. Tres motores electricos acompanan al V8 biturbo hasta los 1.100 hp.',
 'mansory-sf90-perfil.webp',2024,0,3600000000,NULL,
 '4.0 L V8 biturbo + 3 electricos','1.100 hp','2,4 s','355 km/h','Doble embrague 8 vel.','Integral'),

('vivere','MANSORY','Vivere','coleccion','Bugatti Chiron',
 'Mil cuatrocientos setenta y nueve',
 'Reinterpretacion integral del Chiron: frontal redisenado, difusor de carbono y escape central. El W16 de cuatro turbos conserva su cifra integra bajo una piel nueva.',
 'mansory-vivere-perfil.webp',2023,0,16000000000,10,
 '8.0 L W16 cuatro turbos','1.479 hp','2,4 s','420 km/h','Doble embrague 7 vel.','Integral'),

('art-piece-al3c','MANSORY','Art Piece AL3C','coleccion','Mercedes-AMG G 63',
 'Un lienzo de dos toneladas',
 'Colaboracion con el artista pop Alec Monopoly: cada panel del todoterreno esta intervenido a mano. Ancho de vias ampliado, carbono a la vista y 820 hp bajo el capo.',
 'mansory-al3c-perfil.webp',2024,0,NULL,1,
 '4.0 L V8 biturbo','820 hp','3,9 s','240 km/h','Automatica 9 vel.','Integral'),

('carbonado-evo','MANSORY','Carbonado EVO','coleccion','Lamborghini Aventador SVJ',
 'Carbono de extremo a extremo',
 'Kit de carroceria completo sobre el ultimo V12 atmosferico de Sant Agata. Aleron trasero de gran cuerda, capo ventilado y faldones nuevos, todos en fibra vista.',
 'mansory-carbonado-34-frontal.webp',2023,0,4800000000,1,
 '6.5 L V12 atmosferico','770 hp','2,9 s','350 km/h','Automatizada 7 vel.','Integral'),

('elongation-evo','MANSORY','Elongation EVO','gama','Tesla Cybertruck',
 'Acero inoxidable, nuevas aristas',
 'El exoesqueleto de acero del Cybertruck ampliado con paneles de carbono, llantas forjadas y suspension revisada. La silueta angular se alarga sin perder su geometria.',
 'mansory-elongation-perfil.webp',2025,0,1200000000,NULL,
 'Tres motores electricos','845 hp','2,7 s','209 km/h','Reductora directa','Integral'),

('monza-sp2','MANSORY','Monza SP2','coleccion','Ferrari Monza SP2',
 'Sin techo, sin parabrisas, sin excusas',
 'Un barchetta moderno de la serie Icona al que MANSORY anade carbono estructural y un escape especifico. Sin techo ni parabrisas: solo el V12 a la espalda.',
 'mansory-monza-perfil.webp',2022,0,10000000000,499,
 '6.5 L V12 atmosferico','830 hp','2,9 s','300 km/h','Doble embrague 7 vel.','Trasera'),

('bentley-gt','MANSORY','Bentley GT','gama','Bentley Continental GT',
 'Crewe, con mas filo',
 'El gran turismo de Crewe con programa aerodinamico de carbono y llantas forjadas especificas. El V8 hibrido entrega 782 hp sin renunciar al aislamiento de un Bentley.',
 'mansory-bentley-perfil.webp',2025,0,1800000000,NULL,
 '4.0 L V8 biturbo hibrido','782 hp','3,2 s','335 km/h','Doble embrague 8 vel.','Integral'),

('p9lm-evo-900','MANSORY','P9LM EVO 900','edicion','Porsche 911 Turbo S Cabriolet',
 'Novecientos, a cielo abierto',
 'El 911 Turbo S descapotable llevado a 900 hp, con capo integral de carbono y asientos deportivos ligeros. Siete unidades en el mundo para la version Cabrio.',
 'mansory-p9lm-perfil.webp',2024,0,2000000000,7,
 '3.8 L boxer 6 biturbo','900 hp','2,5 s','340 km/h','Doble embrague 8 vel.','Integral');

-- =============================================================================
--  Los usuarios de prueba (admin / empleado / cliente) se crean con hash bcrypt
--  desde el script:  npm run seed
--  No se insertan aqui porque la contrasena NUNCA debe ir en texto plano.
-- =============================================================================
