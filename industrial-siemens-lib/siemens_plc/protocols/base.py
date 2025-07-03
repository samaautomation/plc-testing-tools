"""
Base Protocol Module
===================

Clase base para todos los protocolos de comunicación industrial.
Define la interfaz común que deben implementar todos los protocolos.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime


class ProtocolType(Enum):
    """Tipos de protocolos soportados."""
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    PROFIBUS_DP = "profibus_dp"
    ETHERNET_IP = "ethernet_ip"
    OPC_UA = "opc_ua"
    S7 = "s7"
    CANOPEN = "canopen"
    DEVICENET = "devicenet"
    CC_LINK = "cc_link"


@dataclass
class ProtocolConfig:
    """Configuración base para protocolos."""
    protocol_type: ProtocolType
    host: str
    port: int = 502
    timeout: int = 5000
    retry_count: int = 3
    retry_delay: int = 1000
    debug: bool = False
    auto_reconnect: bool = True
    heartbeat_interval: int = 30000
    
    # Configuraciones específicas
    modbus_unit_id: int = 1
    profibus_slave_address: int = 1
    ethernet_ip_cip_path: str = "1,0"
    opc_ua_namespace: str = "http://opcfoundation.org/UA/"
    s7_rack: int = 0
    s7_slot: int = 1


@dataclass
class ReadRequest:
    """Solicitud de lectura de datos."""
    address: Union[int, str]
    count: int = 1
    data_type: str = "uint16"
    timeout: Optional[int] = None


@dataclass
class WriteRequest:
    """Solicitud de escritura de datos."""
    address: Union[int, str]
    value: Any
    data_type: str = "uint16"
    timeout: Optional[int] = None


@dataclass
class ProtocolStatus:
    """Estado del protocolo de comunicación."""
    is_connected: bool = False
    last_communication: Optional[datetime] = None
    error_count: int = 0
    success_count: int = 0
    response_time_avg: float = 0.0
    protocol_type: Optional[ProtocolType] = None


class BaseProtocol(ABC):
    """
    Clase base abstracta para todos los protocolos industriales.
    
    Define la interfaz común que deben implementar todos los protocolos:
    - Conexión/Desconexión
    - Lectura/Escritura de datos
    - Monitoreo de estado
    - Manejo de errores
    - Reconexión automática
    """
    
    def __init__(self, config: ProtocolConfig):
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.status = ProtocolStatus(protocol_type=config.protocol_type)
        self._connection = None
        self._reconnect_task = None
        self._heartbeat_task = None
        self._lock = asyncio.Lock()
        
        # Configurar logging
        if config.debug:
            self.logger.setLevel(logging.DEBUG)
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establecer conexión con el dispositivo.
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Cerrar conexión con el dispositivo.
        
        Returns:
            bool: True si la desconexión fue exitosa
        """
        pass
    
    @abstractmethod
    async def read_data(self, request: ReadRequest) -> List[Any]:
        """
        Leer datos del dispositivo.
        
        Args:
            request: Solicitud de lectura
            
        Returns:
            List[Any]: Datos leídos
            
        Raises:
            ProtocolError: Si hay error en la comunicación
        """
        pass
    
    @abstractmethod
    async def write_data(self, request: WriteRequest) -> bool:
        """
        Escribir datos al dispositivo.
        
        Args:
            request: Solicitud de escritura
            
        Returns:
            bool: True si la escritura fue exitosa
            
        Raises:
            ProtocolError: Si hay error en la comunicación
        """
        pass
    
    @abstractmethod
    async def read_multiple(self, requests: List[ReadRequest]) -> Dict[int, List[Any]]:
        """
        Leer múltiples registros en una sola transacción.
        
        Args:
            requests: Lista de solicitudes de lectura
            
        Returns:
            Dict[int, List[Any]]: Datos leídos indexados por posición
        """
        pass
    
    @abstractmethod
    async def write_multiple(self, requests: List[WriteRequest]) -> Dict[int, bool]:
        """
        Escribir múltiples registros en una sola transacción.
        
        Args:
            requests: Lista de solicitudes de escritura
            
        Returns:
            Dict[int, bool]: Resultados de escritura indexados por posición
        """
        pass
    
    async def ping(self) -> bool:
        """
        Verificar conectividad con el dispositivo.
        
        Returns:
            bool: True si el dispositivo responde
        """
        try:
            # Implementación básica - leer un registro de estado
            request = ReadRequest(address=0, count=1, data_type="uint16")
            await self.read_data(request)
            return True
        except Exception as e:
            self.logger.warning(f"Ping failed: {e}")
            return False
    
    async def get_status(self) -> ProtocolStatus:
        """
        Obtener estado actual del protocolo.
        
        Returns:
            ProtocolStatus: Estado del protocolo
        """
        return self.status
    
    async def reset_statistics(self) -> None:
        """Reiniciar estadísticas del protocolo."""
        self.status.error_count = 0
        self.status.success_count = 0
        self.status.response_time_avg = 0.0
    
    async def _update_statistics(self, success: bool, response_time: float) -> None:
        """Actualizar estadísticas del protocolo."""
        if success:
            self.status.success_count += 1
        else:
            self.status.error_count += 1
        
        # Actualizar tiempo de respuesta promedio
        total_requests = self.status.success_count + self.status.error_count
        if total_requests == 1:
            self.status.response_time_avg = response_time
        else:
            self.status.response_time_avg = (
                (self.status.response_time_avg * (total_requests - 1) + response_time) 
                / total_requests
            )
        
        self.status.last_communication = datetime.now()
    
    async def _start_heartbeat(self) -> None:
        """Iniciar heartbeat para mantener la conexión."""
        if not self.config.auto_reconnect:
            return
        
        async def heartbeat_loop():
            while self.status.is_connected:
                try:
                    await asyncio.sleep(self.config.heartbeat_interval / 1000)
                    if not await self.ping():
                        self.logger.warning("Heartbeat failed, attempting reconnect")
                        await self._reconnect()
                except Exception as e:
                    self.logger.error(f"Heartbeat error: {e}")
        
        self._heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async def _stop_heartbeat(self) -> None:
        """Detener heartbeat."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
    
    async def _reconnect(self) -> bool:
        """Reconectar automáticamente."""
        if not self.config.auto_reconnect:
            return False
        
        for attempt in range(self.config.retry_count):
            try:
                self.logger.info(f"Reconnection attempt {attempt + 1}/{self.config.retry_count}")
                await asyncio.sleep(self.config.retry_delay / 1000)
                
                await self.disconnect()
                if await self.connect():
                    self.logger.info("Reconnection successful")
                    return True
                    
            except Exception as e:
                self.logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
        
        self.logger.error("All reconnection attempts failed")
        return False
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect() 