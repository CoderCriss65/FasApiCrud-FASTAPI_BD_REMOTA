-- Tabla empleados
CREATE TABLE empleados (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  puesto VARCHAR(100) NOT NULL,
  salario DECIMAL(10, 2) NOT NULL
);

-- Tabla clientes
CREATE TABLE clientes (
  id_cliente INT AUTO_INCREMENT PRIMARY KEY,
  numero_identificacion VARCHAR(20) UNIQUE NOT NULL,
  nombre_cliente VARCHAR(100) NOT NULL,
  telefono_cliente VARCHAR(20) NOT NULL,
  email_cliente VARCHAR(50)
);

-- Tabla proveedoress
CREATE TABLE proveedores (
  id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
  numero_identificacion VARCHAR(20) UNIQUE NOT NULL,
  nombre_proveedor VARCHAR(100) NOT NULL,
  contacto_principal VARCHAR(100) NOT NULL,
  telefono_proveedor VARCHAR(20) NOT NULL
);

--TABLAS DE LA BASE DE DATOS QUE SE DEBEN CREAR EN LA DB REMOTA