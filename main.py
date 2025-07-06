from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.logger import logger
from pydantic import BaseModel
import os
import logging
import sys
import uvicorn
from typing import List, Optional
from database import execute_query  # Importamos la función execute_query

# Configuración básica de logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger("fastapi")

# Modelos Pydantic
class EmpleadoBase(BaseModel):
    nombre: str
    puesto: str
    salario: float

class EmpleadoCreate(EmpleadoBase):
    pass

class Empleado(EmpleadoBase):
    id: int

    class Config:
        orm_mode = True

class ClienteBase(BaseModel):
    numero_identificacion: str
    nombre_cliente: str
    telefono_cliente: str
    email_cliente: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    id_cliente: int

    class Config:
        orm_mode = True

class ProveedorBase(BaseModel):
    numero_identificacion: str
    nombre_proveedor: str
    contacto_principal: str
    telefono_proveedor: str

class ProveedorCreate(ProveedorBase):
    pass

class Proveedor(ProveedorBase):
    id_proveedor: int

    class Config:
        orm_mode = True

# Configuración de la aplicación
app = FastAPI(
    title="API de Gestión Empresarial",
    description="API para gestionar empleados, clientes y proveedores",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"REQUEST: {request.method} {request.url}")
    
    if request.method in ["POST", "PUT"]:
        body = await request.body()
        if body:
            logger.info(f"REQUEST BODY: {body.decode()}")
    
    response = await call_next(request)
    
    logger.info(f"RESPONSE: {response.status_code}")
    return response

# Rutas para empleados
@app.get("/empleados", response_model=List[Empleado], summary="Obtener todos los empleados")
def get_empleados():
    """Obtiene la lista completa de empleados"""
    try:
        return execute_query("SELECT * FROM empleados", fetch_all=True)
    except Exception as e:
        logger.error(f"Error al obtener empleados: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/empleados/{id}", response_model=Empleado, summary="Obtener un empleado por ID")
def get_empleado(id: int):
    """Obtiene un empleado específico por su ID"""
    empleado = execute_query("SELECT * FROM empleados WHERE id = %s", (id,), fetch_one=True)
    if not empleado:
        logger.warning(f"Empleado no encontrado: ID {id}")
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return empleado

@app.post("/empleados", response_model=Empleado, status_code=status.HTTP_201_CREATED, summary="Crear un nuevo empleado")
def create_empleado(empleado: EmpleadoCreate):
    """Crea un nuevo empleado"""
    try:
        empleado_id = execute_query(
            "INSERT INTO empleados (nombre, puesto, salario) VALUES (%s, %s, %s)",
            (empleado.nombre, empleado.puesto, empleado.salario),
            lastrowid=True
        )
        logger.info(f"Empleado creado con ID: {empleado_id}")
        return {**empleado.dict(), "id": empleado_id}
    except Exception as e:
        logger.error(f"Error al crear empleado: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.put("/empleados/{id}", response_model=Empleado, summary="Actualizar un empleado")
def update_empleado(id: int, empleado: EmpleadoCreate):
    """Actualiza un empleado existente"""
    affected_rows = execute_query(
        "UPDATE empleados SET nombre=%s, puesto=%s, salario=%s WHERE id=%s",
        (empleado.nombre, empleado.puesto, empleado.salario, id)
    )
    
    if affected_rows == 0:
        logger.warning(f"Empleado no encontrado para actualizar: ID {id}")
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    logger.info(f"Empleado actualizado: ID {id}")
    return {**empleado.dict(), "id": id}

@app.delete("/empleados/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar un empleado")
def delete_empleado(id: int):
    """Elimina un empleado por su ID"""
    affected_rows = execute_query(
        "DELETE FROM empleados WHERE id = %s",
        (id,)
    )
    
    if affected_rows == 0:
        logger.warning(f"Empleado no encontrado para eliminar: ID {id}")
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    logger.info(f"Empleado eliminado: ID {id}")

# Rutas para clientes
@app.get("/clientes", response_model=List[Cliente], summary="Obtener todos los clientes")
def get_clientes():
    """Obtiene la lista completa de clientes"""
    try:
        return execute_query("SELECT * FROM clientes", fetch_all=True)
    except Exception as e:
        logger.error(f"Error al obtener clientes: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/clientes/{id}", response_model=Cliente, summary="Obtener un cliente por ID")
def get_cliente(id: int):
    """Obtiene un cliente específico por su ID"""
    cliente = execute_query("SELECT * FROM clientes WHERE id_cliente = %s", (id,), fetch_one=True)
    if not cliente:
        logger.warning(f"Cliente no encontrado: ID {id}")
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@app.post("/clientes", response_model=Cliente, status_code=status.HTTP_201_CREATED, summary="Crear un nuevo cliente")
def create_cliente(cliente: ClienteCreate):
    """Crea un nuevo cliente"""
    if not cliente.numero_identificacion or not cliente.nombre_cliente or not cliente.telefono_cliente:
        logger.warning("Validación fallida: Campos obligatorios faltantes para cliente")
        raise HTTPException(
            status_code=400,
            detail="Número de identificación, nombre y teléfono son obligatorios"
        )
    
    try:
        cliente_id = execute_query(
            "INSERT INTO clientes (numero_identificacion, nombre_cliente, telefono_cliente, email_cliente) VALUES (%s, %s, %s, %s)",
            (cliente.numero_identificacion, cliente.nombre_cliente, cliente.telefono_cliente, cliente.email_cliente),
            lastrowid=True
        )
        logger.info(f"Cliente creado con ID: {cliente_id}")
        return {**cliente.dict(), "id_cliente": cliente_id}
    except Exception as e:
        logger.error(f"Error al crear cliente: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.put("/clientes/{id}", response_model=Cliente, summary="Actualizar un cliente")
def update_cliente(id: int, cliente: ClienteCreate):
    """Actualiza un cliente existente"""
    if not cliente.numero_identificacion or not cliente.nombre_cliente or not cliente.telefono_cliente:
        logger.warning("Validación fallida: Campos obligatorios faltantes para actualizar cliente")
        raise HTTPException(
            status_code=400,
            detail="Número de identificación, nombre y teléfono son obligatorios"
        )
    
    affected_rows = execute_query(
        "UPDATE clientes SET numero_identificacion=%s, nombre_cliente=%s, telefono_cliente=%s, email_cliente=%s WHERE id_cliente=%s",
        (cliente.numero_identificacion, cliente.nombre_cliente, cliente.telefono_cliente, cliente.email_cliente, id)
    )
    
    if affected_rows == 0:
        logger.warning(f"Cliente no encontrado para actualizar: ID {id}")
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    logger.info(f"Cliente actualizado: ID {id}")
    return {**cliente.dict(), "id_cliente": id}

@app.delete("/clientes/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar un cliente")
def delete_cliente(id: int):
    """Elimina un cliente por su ID"""
    affected_rows = execute_query(
        "DELETE FROM clientes WHERE id_cliente = %s",
        (id,)
    )
    
    if affected_rows == 0:
        logger.warning(f"Cliente no encontrado para eliminar: ID {id}")
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    logger.info(f"Cliente eliminado: ID {id}")

# Rutas para proveedores
@app.get("/proveedores", response_model=List[Proveedor], summary="Obtener todos los proveedores")
def get_proveedores():
    """Obtiene la lista completa de proveedores"""
    try:
        return execute_query("SELECT * FROM proveedores", fetch_all=True)
    except Exception as e:
        logger.error(f"Error al obtener proveedores: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/proveedores/{id}", response_model=Proveedor, summary="Obtener un proveedor por ID")
def get_proveedor(id: int):
    """Obtiene un proveedor específico por su ID"""
    proveedor = execute_query("SELECT * FROM proveedores WHERE id_proveedor = %s", (id,), fetch_one=True)
    if not proveedor:
        logger.warning(f"Proveedor no encontrado: ID {id}")
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor

@app.post("/proveedores", response_model=Proveedor, status_code=status.HTTP_201_CREATED, summary="Crear un nuevo proveedor")
def create_proveedor(proveedor: ProveedorCreate):
    """Crea un nuevo proveedor"""
    if not all([proveedor.numero_identificacion, proveedor.nombre_proveedor, 
                proveedor.contacto_principal, proveedor.telefono_proveedor]):
        logger.warning("Validación fallida: Campos obligatorios faltantes para proveedor")
        raise HTTPException(
            status_code=400,
            detail="Todos los campos son obligatorios"
        )
    
    try:
        proveedor_id = execute_query(
            "INSERT INTO proveedores (numero_identificacion, nombre_proveedor, contacto_principal, telefono_proveedor) VALUES (%s, %s, %s, %s)",
            (proveedor.numero_identificacion, proveedor.nombre_proveedor, proveedor.contacto_principal, proveedor.telefono_proveedor),
            lastrowid=True
        )
        logger.info(f"Proveedor creado con ID: {proveedor_id}")
        return {**proveedor.dict(), "id_proveedor": proveedor_id}
    except Exception as e:
        logger.error(f"Error al crear proveedor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.put("/proveedores/{id}", response_model=Proveedor, summary="Actualizar un proveedor")
def update_proveedor(id: int, proveedor: ProveedorCreate):
    """Actualiza un proveedor existente"""
    if not all([proveedor.numero_identificacion, proveedor.nombre_proveedor, 
                proveedor.contacto_principal, proveedor.telefono_proveedor]):
        logger.warning("Validación fallida: Campos obligatorios faltantes para actualizar proveedor")
        raise HTTPException(
            status_code=400,
            detail="Todos los campos son obligatorios"
        )
    
    affected_rows = execute_query(
        "UPDATE proveedores SET numero_identificacion=%s, nombre_proveedor=%s, contacto_principal=%s, telefono_proveedor=%s WHERE id_proveedor=%s",
        (proveedor.numero_identificacion, proveedor.nombre_proveedor, proveedor.contacto_principal, proveedor.telefono_proveedor, id)
    )
    
    if affected_rows == 0:
        logger.warning(f"Proveedor no encontrado para actualizar: ID {id}")
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    logger.info(f"Proveedor actualizado: ID {id}")
    return {**proveedor.dict(), "id_proveedor": id}

@app.delete("/proveedores/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar un proveedor")
def delete_proveedor(id: int):
    """Elimina un proveedor por su ID"""
    affected_rows = execute_query(
        "DELETE FROM proveedores WHERE id_proveedor = %s",
        (id,)
    )
    
    if affected_rows == 0:
        logger.warning(f"Proveedor no encontrado para eliminar: ID {id}")
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    logger.info(f"Proveedor eliminado: ID {id}")

# Verificar tablas al iniciar
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando aplicación...")
    try:
        # Ejemplo: verificar una tabla
        empleados = execute_query("SHOW TABLES LIKE 'empleados'", fetch_one=True)
        if not empleados:
            logger.error("❌ Tabla 'empleados' no encontrada")
        else:
            logger.info("✅ Tablas verificadas")
    except Exception as e:
        logger.error(f"Error al verificar tablas: {e}")

# Punto de entrada principal
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")