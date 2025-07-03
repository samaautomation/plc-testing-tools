"""
Industrial Siemens Library - Connection
=======================================

Módulo de conexión robusta al PLC Siemens con reconexión automática.
"""

import time
import threading
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import snap7
from snap7 import Area

from .exceptions import (
    PLCConnectionError,
    PLCCommunicationError,
    PLCTimeoutError,
    PLCStateError
)


class ConnectionState(Enum):
    """Estados de conexión del PLC."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class ConnectionConfig:
    """Configuración de conexión al PLC."""
    ip: str
    rack: int = 0
    slot: int = 1
    timeout: int = 5000
    retry_attempts: int = 3
    retry_delay: int = 1000
    heartbeat_interval: int = 5000
    auto_reconnect: bool = True
    debug: bool = False


class PLCConnection:
    """Clase base para conexión al PLC."""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.client = snap7.client.Client()
        self.state = ConnectionState.DISCONNECTED
        self.last_heartbeat = 0
        self.connection_time = 0
        self.error_count = 0
        self.reconnect_count = 0
        
        # Threading
        self._lock = threading.RLock()
        self._heartbeat_thread = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self._connection_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []
        self._heartbeat_callbacks: List[Callable] = []
    
    def connect(self) -> bool:
        """Establece conexión con el PLC."""
        with self._lock:
            if self.state == ConnectionState.CONNECTED:
                return True
            
            self.state = ConnectionState.CONNECTING
            
            try:
                if self.config.debug:
                    print(f"🔌 Conectando a PLC {self.config.ip}...")
                
                self.client.connect(
                    self.config.ip,
                    self.config.rack,
                    self.config.slot
                )
                
                if self.client.get_connected():
                    self.state = ConnectionState.CONNECTED
                    self.connection_time = time.time()
                    self.error_count = 0
                    self.reconnect_count = 0
                    
                    if self.config.debug:
                        print(f"✅ Conectado exitosamente a PLC {self.config.ip}")
                    
                    # Iniciar heartbeat si está habilitado
                    if self.config.heartbeat_interval > 0:
                        self._start_heartbeat()
                    
                    # Notificar callbacks
                    self._notify_connection_callbacks(True)
                    return True
                else:
                    self.state = ConnectionState.ERROR
                    raise PLCConnectionError(
                        f"No se pudo conectar al PLC {self.config.ip}",
                        ip=self.config.ip
                    )
                    
            except Exception as e:
                self.state = ConnectionState.ERROR
                self.error_count += 1
                
                if self.config.debug:
                    print(f"❌ Error conectando al PLC: {e}")
                
                # Notificar callbacks
                self._notify_error_callbacks(e)
                
                if self.config.auto_reconnect:
                    self._schedule_reconnect()
                
                raise PLCConnectionError(
                    f"Error conectando al PLC {self.config.ip}: {str(e)}",
                    ip=self.config.ip,
                    details={"error": str(e)}
                )
    
    def disconnect(self):
        """Desconecta del PLC."""
        with self._lock:
            if self.state == ConnectionState.DISCONNECTED:
                return
            
            self._stop_heartbeat()
            self.state = ConnectionState.DISCONNECTED
            
            try:
                if self.client.get_connected():
                    self.client.disconnect()
            except Exception as e:
                if self.config.debug:
                    print(f"⚠️ Error durante desconexión: {e}")
            
            if self.config.debug:
                print(f"🔌 Desconectado del PLC {self.config.ip}")
    
    def is_connected(self) -> bool:
        """Verifica si está conectado al PLC."""
        with self._lock:
            return (self.state == ConnectionState.CONNECTED and 
                   self.client.get_connected())
    
    def get_state(self) -> ConnectionState:
        """Obtiene el estado actual de la conexión."""
        with self._lock:
            return self.state
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtiene información de la conexión."""
        with self._lock:
            return {
                "ip": self.config.ip,
                "rack": self.config.rack,
                "slot": self.config.slot,
                "state": self.state.value,
                "connected": self.is_connected(),
                "connection_time": self.connection_time,
                "uptime": time.time() - self.connection_time if self.connection_time > 0 else 0,
                "error_count": self.error_count,
                "reconnect_count": self.reconnect_count,
                "last_heartbeat": self.last_heartbeat
            }
    
    def add_connection_callback(self, callback: Callable[[bool], None]):
        """Agrega un callback para eventos de conexión."""
        self._connection_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[Exception], None]):
        """Agrega un callback para eventos de error."""
        self._error_callbacks.append(callback)
    
    def add_heartbeat_callback(self, callback: Callable[[float], None]):
        """Agrega un callback para eventos de heartbeat."""
        self._heartbeat_callbacks.append(callback)
    
    def _start_heartbeat(self):
        """Inicia el thread de heartbeat."""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self._heartbeat_thread.start()
    
    def _stop_heartbeat(self):
        """Detiene el thread de heartbeat."""
        self._stop_event.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=1.0)
    
    def _heartbeat_loop(self):
        """Loop principal del heartbeat."""
        while not self._stop_event.is_set():
            try:
                if self.is_connected():
                    # Realizar heartbeat (leer un byte de sistema)
                    self.client.read_area(Area.SYS, 0, 0, 1)
                    self.last_heartbeat = time.time()
                    
                    # Notificar callbacks
                    self._notify_heartbeat_callbacks(self.last_heartbeat)
                
                time.sleep(self.config.heartbeat_interval / 1000.0)
                
            except Exception as e:
                if self.config.debug:
                    print(f"⚠️ Error en heartbeat: {e}")
                
                # Marcar como error y reconectar si es necesario
                with self._lock:
                    self.state = ConnectionState.ERROR
                
                if self.config.auto_reconnect:
                    self._schedule_reconnect()
                
                break
    
    def _schedule_reconnect(self):
        """Programa una reconexión automática."""
        if self.reconnect_count >= self.config.retry_attempts:
            if self.config.debug:
                print(f"❌ Máximo número de intentos de reconexión alcanzado")
            return
        
        def delayed_reconnect():
            time.sleep(self.config.retry_delay / 1000.0)
            self._attempt_reconnect()
        
        threading.Thread(target=delayed_reconnect, daemon=True).start()
    
    def _attempt_reconnect(self):
        """Intenta reconectar al PLC."""
        with self._lock:
            if self.state == ConnectionState.CONNECTED:
                return
            
            self.state = ConnectionState.RECONNECTING
            self.reconnect_count += 1
        
        if self.config.debug:
            print(f"🔄 Reintentando conexión ({self.reconnect_count}/{self.config.retry_attempts})...")
        
        try:
            self.connect()
        except Exception as e:
            if self.config.debug:
                print(f"❌ Reconexión fallida: {e}")
    
    def _notify_connection_callbacks(self, connected: bool):
        """Notifica a los callbacks de conexión."""
        for callback in self._connection_callbacks:
            try:
                callback(connected)
            except Exception as e:
                if self.config.debug:
                    print(f"⚠️ Error en callback de conexión: {e}")
    
    def _notify_error_callbacks(self, error: Exception):
        """Notifica a los callbacks de error."""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                if self.config.debug:
                    print(f"⚠️ Error en callback de error: {e}")
    
    def _notify_heartbeat_callbacks(self, timestamp: float):
        """Notifica a los callbacks de heartbeat."""
        for callback in self._heartbeat_callbacks:
            try:
                callback(timestamp)
            except Exception as e:
                if self.config.debug:
                    print(f"⚠️ Error en callback de heartbeat: {e}")


class SiemensPLC:
    """Clase principal para comunicación con PLC Siemens."""
    
    def __init__(self, 
                 ip: str,
                 rack: int = 0,
                 slot: int = 1,
                 timeout: int = 5000,
                 retry_attempts: int = 3,
                 retry_delay: int = 1000,
                 heartbeat_interval: int = 5000,
                 auto_reconnect: bool = True,
                 debug: bool = False):
        
        config = ConnectionConfig(
            ip=ip,
            rack=rack,
            slot=slot,
            timeout=timeout,
            retry_attempts=retry_attempts,
            retry_delay=retry_delay,
            heartbeat_interval=heartbeat_interval,
            auto_reconnect=auto_reconnect,
            debug=debug
        )
        
        self.connection = PLCConnection(config)
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Configura los callbacks de la conexión."""
        self.connection.add_connection_callback(self._on_connection_change)
        self.connection.add_error_callback(self._on_error)
        self.connection.add_heartbeat_callback(self._on_heartbeat)
    
    def connect(self) -> bool:
        """Conecta al PLC."""
        return self.connection.connect()
    
    def disconnect(self):
        """Desconecta del PLC."""
        self.connection.disconnect()
    
    def is_connected(self) -> bool:
        """Verifica si está conectado."""
        return self.connection.is_connected()
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtiene información de la conexión."""
        return self.connection.get_connection_info()
    
    def read_area(self, area: Area, db_number: int, start: int, size: int) -> bytes:
        """Lee un área de memoria del PLC."""
        if not self.is_connected():
            raise PLCConnectionError("No hay conexión activa con el PLC")
        
        try:
            return self.connection.client.read_area(area, db_number, start, size)
        except Exception as e:
            raise PLCCommunicationError(
                f"Error leyendo área {area}",
                operation="read_area",
                details={"area": area, "db_number": db_number, "start": start, "size": size, "error": str(e)}
            )
    
    def write_area(self, area: Area, db_number: int, start: int, data: bytes) -> bool:
        """Escribe en un área de memoria del PLC."""
        if not self.is_connected():
            raise PLCConnectionError("No hay conexión activa con el PLC")
        
        try:
            return self.connection.client.write_area(area, db_number, start, data)
        except Exception as e:
            raise PLCCommunicationError(
                f"Error escribiendo área {area}",
                operation="write_area",
                details={"area": area, "db_number": db_number, "start": start, "error": str(e)}
            )
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Obtiene información del CPU del PLC."""
        if not self.is_connected():
            raise PLCConnectionError("No hay conexión activa con el PLC")
        
        try:
            return self.connection.client.get_cpu_info()
        except Exception as e:
            raise PLCCommunicationError(
                "Error obteniendo información del CPU",
                operation="get_cpu_info",
                details={"error": str(e)}
            )
    
    def get_order_code(self) -> str:
        """Obtiene el código de orden del PLC."""
        if not self.is_connected():
            raise PLCConnectionError("No hay conexión activa con el PLC")
        
        try:
            return self.connection.client.get_order_code()
        except Exception as e:
            raise PLCCommunicationError(
                "Error obteniendo código de orden",
                operation="get_order_code",
                details={"error": str(e)}
            )
    
    def _on_connection_change(self, connected: bool):
        """Callback para cambios de conexión."""
        if self.connection.config.debug:
            status = "conectado" if connected else "desconectado"
            print(f"🔄 Estado de conexión: {status}")
    
    def _on_error(self, error: Exception):
        """Callback para errores."""
        if self.connection.config.debug:
            print(f"❌ Error de conexión: {error}")
    
    def _on_heartbeat(self, timestamp: float):
        """Callback para heartbeat."""
        if self.connection.config.debug:
            print(f"💓 Heartbeat: {timestamp}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect() 