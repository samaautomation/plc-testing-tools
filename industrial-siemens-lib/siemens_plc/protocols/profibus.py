"""
Profibus Protocol Module
========================

Implementación del protocolo Profibus-DP.
Soporte para comunicación con dispositivos Profibus industriales.
"""

import asyncio
import struct
import time
from typing import Any, Dict, List, Optional, Union
import logging

try:
    import snap7
    from snap7.util import *
    SNAP7_AVAILABLE = True
except ImportError:
    SNAP7_AVAILABLE = False
    logging.warning("snap7 not available. Install with: pip install python-snap7")

from .base import BaseProtocol, ProtocolConfig, ProtocolType, ReadRequest, WriteRequest


class ProfibusProtocol(BaseProtocol):
    """Clase base para protocolo Profibus-DP."""
    
    def __init__(self, config: ProtocolConfig):
        if not SNAP7_AVAILABLE:
            raise ImportError("snap7 library is required for Profibus support")
        
        super().__init__(config)
        self._client = None
        self._slave_address = config.profibus_slave_address
    
    async def connect(self) -> bool:
        """Conectar al dispositivo Profibus."""
        try:
            async with self._lock:
                if self._client and self._client.get_connected():
                    return True
                
                # Crear cliente Profibus
                self._client = snap7.client.Client()
                
                # Configurar parámetros de conexión
                self._client.set_connection_type(1)  # Profibus
                self._client.set_connection_params(
                    self.config.host,
                    self.config.profibus_slave_address,
                    0,  # Rack
                    0   # Slot
                )
                
                # Conectar
                result = self._client.connect_to(self.config.host, 
                                               self.config.profibus_slave_address, 
                                               0, 0)
                
                if result == 0:
                    self.status.is_connected = True
                    await self._start_heartbeat()
                    self.logger.info(f"Connected to Profibus device at {self.config.host}")
                    return True
                else:
                    self.logger.error(f"Failed to connect to Profibus device at {self.config.host}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Profibus connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Desconectar del dispositivo Profibus."""
        try:
            async with self._lock:
                await self._stop_heartbeat()
                
                if self._client:
                    self._client.disconnect()
                    self._client.destroy()
                    self._client = None
                
                self.status.is_connected = False
                self.logger.info("Disconnected from Profibus device")
                return True
                
        except Exception as e:
            self.logger.error(f"Profibus disconnect error: {e}")
            return False
    
    async def read_data(self, request: ReadRequest) -> List[Any]:
        """Leer datos Profibus."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._client.get_connected():
                    raise Exception("Not connected to Profibus device")
                
                # Determinar área de memoria según el tipo de datos
                area = self._get_area_from_data_type(request.data_type)
                
                # Leer datos
                data = self._client.db_read(int(request.address), 0, request.count * 2)
                
                if data is None:
                    raise Exception("Failed to read data from Profibus device")
                
                # Convertir datos según el tipo
                converted_data = self._convert_bytes_to_data(data, request.data_type, request.count)
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return converted_data
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"Profibus read error: {e}")
            raise
    
    async def write_data(self, request: WriteRequest) -> bool:
        """Escribir datos Profibus."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._client.get_connected():
                    raise Exception("Not connected to Profibus device")
                
                # Convertir datos a bytes
                if isinstance(request.value, (list, tuple)):
                    data_bytes = self._convert_data_to_bytes(request.value, request.data_type)
                else:
                    data_bytes = self._convert_data_to_bytes([request.value], request.data_type)
                
                # Escribir datos
                result = self._client.db_write(int(request.address), 0, data_bytes)
                
                if result != 0:
                    raise Exception(f"Failed to write data to Profibus device: {result}")
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return True
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"Profibus write error: {e}")
            raise
    
    async def read_multiple(self, requests: List[ReadRequest]) -> Dict[int, List[Any]]:
        """Leer múltiples registros Profibus."""
        results = {}
        
        for i, request in enumerate(requests):
            try:
                data = await self.read_data(request)
                results[i] = data
            except Exception as e:
                self.logger.error(f"Error reading request {i}: {e}")
                results[i] = []
        
        return results
    
    async def write_multiple(self, requests: List[WriteRequest]) -> Dict[int, bool]:
        """Escribir múltiples registros Profibus."""
        results = {}
        
        for i, request in enumerate(requests):
            try:
                success = await self.write_data(request)
                results[i] = success
            except Exception as e:
                self.logger.error(f"Error writing request {i}: {e}")
                results[i] = False
        
        return results
    
    def _get_area_from_data_type(self, data_type: str) -> int:
        """Obtener área de memoria según el tipo de datos."""
        area_map = {
            'input': snap7.types.Areas.PE,      # Process Inputs
            'output': snap7.types.Areas.PA,     # Process Outputs
            'mark': snap7.types.Areas.MK,       # Marks
            'data_block': snap7.types.Areas.DB, # Data Blocks
            'counter': snap7.types.Areas.CT,    # Counters
            'timer': snap7.types.Areas.TM       # Timers
        }
        
        return area_map.get(data_type, snap7.types.Areas.DB)
    
    def _convert_bytes_to_data(self, data_bytes: bytes, data_type: str, count: int) -> List[Any]:
        """Convertir bytes a tipos de datos específicos."""
        if data_type == 'bool':
            return [bool(data_bytes[i]) for i in range(count)]
        elif data_type == 'uint8':
            return [data_bytes[i] for i in range(count)]
        elif data_type == 'int8':
            return [struct.unpack('b', bytes([data_bytes[i]]))[0] for i in range(count)]
        elif data_type == 'uint16':
            return [struct.unpack('>H', data_bytes[i:i+2])[0] for i in range(0, len(data_bytes), 2)]
        elif data_type == 'int16':
            return [struct.unpack('>h', data_bytes[i:i+2])[0] for i in range(0, len(data_bytes), 2)]
        elif data_type == 'uint32':
            return [struct.unpack('>I', data_bytes[i:i+4])[0] for i in range(0, len(data_bytes), 4)]
        elif data_type == 'int32':
            return [struct.unpack('>i', data_bytes[i:i+4])[0] for i in range(0, len(data_bytes), 4)]
        elif data_type == 'float32':
            return [struct.unpack('>f', data_bytes[i:i+4])[0] for i in range(0, len(data_bytes), 4)]
        elif data_type == 'float64':
            return [struct.unpack('>d', data_bytes[i:i+8])[0] for i in range(0, len(data_bytes), 8)]
        else:
            return list(data_bytes)
    
    def _convert_data_to_bytes(self, values: List[Any], data_type: str) -> bytes:
        """Convertir datos a bytes."""
        if data_type == 'bool':
            return bytes([int(bool(val)) for val in values])
        elif data_type == 'uint8':
            return bytes([int(val) & 0xFF for val in values])
        elif data_type == 'int8':
            return bytes([struct.pack('b', int(val))[0] for val in values])
        elif data_type == 'uint16':
            return b''.join([struct.pack('>H', int(val)) for val in values])
        elif data_type == 'int16':
            return b''.join([struct.pack('>h', int(val)) for val in values])
        elif data_type == 'uint32':
            return b''.join([struct.pack('>I', int(val)) for val in values])
        elif data_type == 'int32':
            return b''.join([struct.pack('>i', int(val)) for val in values])
        elif data_type == 'float32':
            return b''.join([struct.pack('>f', float(val)) for val in values])
        elif data_type == 'float64':
            return b''.join([struct.pack('>d', float(val)) for val in values])
        else:
            return bytes(values)


class ProfibusDP(ProfibusProtocol):
    """Cliente Profibus-DP."""
    
    def __init__(self, host: str, slave_address: int = 1, **kwargs):
        config = ProtocolConfig(
            protocol_type=ProtocolType.PROFIBUS_DP,
            host=host,
            profibus_slave_address=slave_address,
            **kwargs
        )
        super().__init__(config) 