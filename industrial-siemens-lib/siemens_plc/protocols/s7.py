"""
S7 Protocol Module
==================

Implementación del protocolo S7 para comunicación directa con PLCs Siemens.
Soporte para S7-300, S7-400, S7-1200, S7-1500 y otros PLCs Siemens.
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


class S7Protocol(BaseProtocol):
    """Cliente S7 para PLCs Siemens."""
    
    def __init__(self, config: ProtocolConfig):
        if not SNAP7_AVAILABLE:
            raise ImportError("snap7 library is required for S7 support")
        
        super().__init__(config)
        self._client = None
        self._rack = config.s7_rack
        self._slot = config.s7_slot
    
    async def connect(self) -> bool:
        """Conectar al PLC Siemens."""
        try:
            async with self._lock:
                if self._client and self._client.get_connected():
                    return True
                
                # Crear cliente S7
                self._client = snap7.client.Client()
                
                # Configurar parámetros de conexión
                self._client.set_connection_type(1)  # TCP
                self._client.set_connection_params(
                    self.config.host,
                    self._rack,
                    self._slot
                )
                
                # Conectar
                result = self._client.connect_to(self.config.host, self._rack, self._slot)
                
                if result == 0:
                    self.status.is_connected = True
                    await self._start_heartbeat()
                    self.logger.info(f"Connected to S7 PLC at {self.config.host}")
                    return True
                else:
                    self.logger.error(f"Failed to connect to S7 PLC at {self.config.host}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"S7 connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Desconectar del PLC Siemens."""
        try:
            async with self._lock:
                await self._stop_heartbeat()
                
                if self._client:
                    self._client.disconnect()
                    self._client.destroy()
                    self._client = None
                
                self.status.is_connected = False
                self.logger.info("Disconnected from S7 PLC")
                return True
                
        except Exception as e:
            self.logger.error(f"S7 disconnect error: {e}")
            return False
    
    async def read_data(self, request: ReadRequest) -> List[Any]:
        """Leer datos del PLC Siemens."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._client.get_connected():
                    raise Exception("Not connected to S7 PLC")
                
                # Determinar área de memoria según el tipo de datos
                area = self._get_area_from_data_type(request.data_type)
                
                # Leer datos
                data = self._client.read_area(area, 0, int(request.address), request.count * 2)
                
                if data is None:
                    raise Exception("Failed to read data from S7 PLC")
                
                # Convertir datos según el tipo
                converted_data = self._convert_bytes_to_data(data, request.data_type, request.count)
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return converted_data
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"S7 read error: {e}")
            raise
    
    async def write_data(self, request: WriteRequest) -> bool:
        """Escribir datos al PLC Siemens."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._client.get_connected():
                    raise Exception("Not connected to S7 PLC")
                
                # Determinar área de memoria según el tipo de datos
                area = self._get_area_from_data_type(request.data_type)
                
                # Convertir datos a bytes
                if isinstance(request.value, (list, tuple)):
                    data_bytes = self._convert_data_to_bytes(request.value, request.data_type)
                else:
                    data_bytes = self._convert_data_to_bytes([request.value], request.data_type)
                
                # Escribir datos
                result = self._client.write_area(area, 0, int(request.address), data_bytes)
                
                if result != 0:
                    raise Exception(f"Failed to write data to S7 PLC: {result}")
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return True
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"S7 write error: {e}")
            raise
    
    async def read_multiple(self, requests: List[ReadRequest]) -> Dict[int, List[Any]]:
        """Leer múltiples registros S7."""
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
        """Escribir múltiples registros S7."""
        results = {}
        
        for i, request in enumerate(requests):
            try:
                success = await self.write_data(request)
                results[i] = success
            except Exception as e:
                self.logger.error(f"Error writing request {i}: {e}")
                results[i] = False
        
        return results
    
    async def get_cpu_info(self) -> Dict[str, Any]:
        """Obtener información del CPU del PLC."""
        try:
            async with self._lock:
                if not self._client or not self._client.get_connected():
                    raise Exception("Not connected to S7 PLC")
                
                # Obtener información del CPU
                cpu_info = self._client.get_cpu_info()
                
                if cpu_info:
                    return {
                        'module_type_name': cpu_info.ModuleTypeName.decode('utf-8').strip('\x00'),
                        'serial_number': cpu_info.SerialNumber.decode('utf-8').strip('\x00'),
                        'asic_version': cpu_info.ASICVersion.decode('utf-8').strip('\x00'),
                        'module_version': cpu_info.ModuleVersion.decode('utf-8').strip('\x00')
                    }
                else:
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Error getting CPU info: {e}")
            return {}
    
    async def get_order_code(self) -> str:
        """Obtener código de orden del PLC."""
        try:
            async with self._lock:
                if not self._client or not self._client.get_connected():
                    raise Exception("Not connected to S7 PLC")
                
                order_code = self._client.get_order_code()
                
                if order_code:
                    return order_code.decode('utf-8').strip('\x00')
                else:
                    return ""
                    
        except Exception as e:
            self.logger.error(f"Error getting order code: {e}")
            return ""
    
    async def get_plc_status(self) -> str:
        """Obtener estado del PLC."""
        try:
            async with self._lock:
                if not self._client or not self._client.get_connected():
                    raise Exception("Not connected to S7 PLC")
                
                status = self._client.get_plc_status()
                
                status_map = {
                    snap7.common.S7CpuStatusRun: "RUN",
                    snap7.common.S7CpuStatusStop: "STOP",
                    snap7.common.S7CpuStatusUnknown: "UNKNOWN"
                }
                
                return status_map.get(status, "UNKNOWN")
                
        except Exception as e:
            self.logger.error(f"Error getting PLC status: {e}")
            return "UNKNOWN"
    
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
            return [get_bool(data_bytes, 0, i) for i in range(count)]
        elif data_type == 'uint8':
            return [get_int(data_bytes, i) for i in range(count)]
        elif data_type == 'int8':
            return [get_sint(data_bytes, i) for i in range(count)]
        elif data_type == 'uint16':
            return [get_uint(data_bytes, i) for i in range(0, count, 2)]
        elif data_type == 'int16':
            return [get_int(data_bytes, i) for i in range(0, count, 2)]
        elif data_type == 'uint32':
            return [get_udint(data_bytes, i) for i in range(0, count, 4)]
        elif data_type == 'int32':
            return [get_dint(data_bytes, i) for i in range(0, count, 4)]
        elif data_type == 'float32':
            return [get_real(data_bytes, i) for i in range(0, count, 4)]
        elif data_type == 'float64':
            return [get_lreal(data_bytes, i) for i in range(0, count, 8)]
        elif data_type == 'string':
            return [get_string(data_bytes, i) for i in range(0, count, 84)]  # S7 string max 82 chars
        else:
            return list(data_bytes)
    
    def _convert_data_to_bytes(self, values: List[Any], data_type: str) -> bytes:
        """Convertir datos a bytes."""
        data_bytes = bytearray()
        
        for value in values:
            if data_type == 'bool':
                set_bool(data_bytes, 0, len(data_bytes), bool(value))
            elif data_type == 'uint8':
                set_int(data_bytes, len(data_bytes), int(value))
            elif data_type == 'int8':
                set_sint(data_bytes, len(data_bytes), int(value))
            elif data_type == 'uint16':
                set_uint(data_bytes, len(data_bytes), int(value))
            elif data_type == 'int16':
                set_int(data_bytes, len(data_bytes), int(value))
            elif data_type == 'uint32':
                set_udint(data_bytes, len(data_bytes), int(value))
            elif data_type == 'int32':
                set_dint(data_bytes, len(data_bytes), int(value))
            elif data_type == 'float32':
                set_real(data_bytes, len(data_bytes), float(value))
            elif data_type == 'float64':
                set_lreal(data_bytes, len(data_bytes), float(value))
            elif data_type == 'string':
                set_string(data_bytes, len(data_bytes), str(value), 82)
        
        return bytes(data_bytes) 