"""
Modbus Protocol Module
======================

Implementación del protocolo Modbus (TCP y RTU).
Soporte para comunicación con VFDs, PLCs y dispositivos industriales.
"""

import asyncio
import struct
import time
from typing import Any, Dict, List, Optional, Union
import logging

try:
    import pymodbus
    from pymodbus.client import ModbusTcpClient, ModbusSerialClient
    from pymodbus.exceptions import ModbusException
    from pymodbus.pdu import ExceptionResponse
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("pymodbus not available. Install with: pip install pymodbus")

from .base import BaseProtocol, ProtocolConfig, ProtocolType, ReadRequest, WriteRequest


class ModbusProtocol(BaseProtocol):
    """Clase base para protocolo Modbus."""
    
    def __init__(self, config: ProtocolConfig):
        if not MODBUS_AVAILABLE:
            raise ImportError("pymodbus library is required for Modbus support")
        
        super().__init__(config)
        self._client = None
        self._transaction_id = 0
    
    async def connect(self) -> bool:
        """Conectar al dispositivo Modbus."""
        try:
            async with self._lock:
                if self._client and self._client.connected:
                    return True
                
                # Crear cliente según el tipo
                if self.config.protocol_type == ProtocolType.MODBUS_TCP:
                    self._client = ModbusTcpClient(
                        host=self.config.host,
                        port=self.config.port,
                        timeout=self.config.timeout / 1000,
                        retries=self.config.retry_count
                    )
                elif self.config.protocol_type == ProtocolType.MODBUS_RTU:
                    self._client = ModbusSerialClient(
                        method='rtu',
                        port=self.config.host,  # Para RTU, host es el puerto serial
                        baudrate=9600,
                        parity='N',
                        stopbits=1,
                        bytesize=8,
                        timeout=self.config.timeout / 1000
                    )
                
                # Conectar
                if self._client.connect():
                    self.status.is_connected = True
                    await self._start_heartbeat()
                    self.logger.info(f"Connected to Modbus device at {self.config.host}")
                    return True
                else:
                    self.logger.error(f"Failed to connect to Modbus device at {self.config.host}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Modbus connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Desconectar del dispositivo Modbus."""
        try:
            async with self._lock:
                await self._stop_heartbeat()
                
                if self._client:
                    self._client.close()
                    self._client = None
                
                self.status.is_connected = False
                self.logger.info("Disconnected from Modbus device")
                return True
                
        except Exception as e:
            self.logger.error(f"Modbus disconnect error: {e}")
            return False
    
    async def read_data(self, request: ReadRequest) -> List[Any]:
        """Leer datos Modbus."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._client.connected:
                    raise Exception("Not connected to Modbus device")
                
                # Determinar función según el tipo de datos
                if request.data_type in ['coil', 'discrete_input']:
                    # Funciones 1 y 2 - Coils y Discrete Inputs
                    if request.data_type == 'coil':
                        result = self._client.read_coils(
                            address=int(request.address),
                            count=request.count,
                            slave=self.config.modbus_unit_id
                        )
                    else:
                        result = self._client.read_discrete_inputs(
                            address=int(request.address),
                            count=request.count,
                            slave=self.config.modbus_unit_id
                        )
                    
                    if result.isError():
                        raise ModbusException(f"Read error: {result}")
                    
                    # Convertir a lista de booleanos
                    data = [bool(bit) for bit in result.bits[:request.count]]
                    
                else:
                    # Funciones 3 y 4 - Holding Registers e Input Registers
                    if request.data_type in ['holding_register', 'uint16', 'int16']:
                        result = self._client.read_holding_registers(
                            address=int(request.address),
                            count=request.count,
                            slave=self.config.modbus_unit_id
                        )
                    else:
                        result = self._client.read_input_registers(
                            address=int(request.address),
                            count=request.count,
                            slave=self.config.modbus_unit_id
                        )
                    
                    if result.isError():
                        raise ModbusException(f"Read error: {result}")
                    
                    # Convertir registros según el tipo de datos
                    data = self._convert_registers_to_data(result.registers, request.data_type)
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return data
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"Modbus read error: {e}")
            raise
    
    async def write_data(self, request: WriteRequest) -> bool:
        """Escribir datos Modbus."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._client.connected:
                    raise Exception("Not connected to Modbus device")
                
                # Determinar función según el tipo de datos
                if request.data_type == 'coil':
                    # Función 5 - Write Single Coil
                    if isinstance(request.value, (list, tuple)):
                        # Función 15 - Write Multiple Coils
                        result = self._client.write_coils(
                            address=int(request.address),
                            values=request.value,
                            slave=self.config.modbus_unit_id
                        )
                    else:
                        result = self._client.write_coil(
                            address=int(request.address),
                            value=bool(request.value),
                            slave=self.config.modbus_unit_id
                        )
                else:
                    # Función 6 y 16 - Write Single/Multiple Holding Registers
                    if isinstance(request.value, (list, tuple)):
                        # Convertir valores a registros
                        registers = self._convert_data_to_registers(request.value, request.data_type)
                        result = self._client.write_registers(
                            address=int(request.address),
                            values=registers,
                            slave=self.config.modbus_unit_id
                        )
                    else:
                        # Convertir valor único a registro
                        register = self._convert_single_value_to_register(request.value, request.data_type)
                        result = self._client.write_register(
                            address=int(request.address),
                            value=register,
                            slave=self.config.modbus_unit_id
                        )
                
                if result.isError():
                    raise ModbusException(f"Write error: {result}")
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return True
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"Modbus write error: {e}")
            raise
    
    async def read_multiple(self, requests: List[ReadRequest]) -> Dict[int, List[Any]]:
        """Leer múltiples registros Modbus."""
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
        """Escribir múltiples registros Modbus."""
        results = {}
        
        for i, request in enumerate(requests):
            try:
                success = await self.write_data(request)
                results[i] = success
            except Exception as e:
                self.logger.error(f"Error writing request {i}: {e}")
                results[i] = False
        
        return results
    
    def _convert_registers_to_data(self, registers: List[int], data_type: str) -> List[Any]:
        """Convertir registros Modbus a tipos de datos específicos."""
        if data_type == 'uint16':
            return registers
        elif data_type == 'int16':
            return [struct.unpack('>h', struct.pack('>H', reg))[0] for reg in registers]
        elif data_type == 'uint32':
            # Combinar dos registros para formar uint32
            data = []
            for i in range(0, len(registers), 2):
                if i + 1 < len(registers):
                    value = (registers[i] << 16) | registers[i + 1]
                    data.append(value)
            return data
        elif data_type == 'int32':
            # Combinar dos registros para formar int32
            data = []
            for i in range(0, len(registers), 2):
                if i + 1 < len(registers):
                    value = (registers[i] << 16) | registers[i + 1]
                    data.append(struct.unpack('>i', struct.pack('>I', value))[0])
            return data
        elif data_type == 'float32':
            # Combinar dos registros para formar float32
            data = []
            for i in range(0, len(registers), 2):
                if i + 1 < len(registers):
                    bytes_data = struct.pack('>HH', registers[i], registers[i + 1])
                    value = struct.unpack('>f', bytes_data)[0]
                    data.append(value)
            return data
        else:
            return registers
    
    def _convert_data_to_registers(self, values: List[Any], data_type: str) -> List[int]:
        """Convertir datos a registros Modbus."""
        registers = []
        
        for value in values:
            if data_type == 'uint16':
                registers.append(int(value) & 0xFFFF)
            elif data_type == 'int16':
                registers.append(struct.unpack('>H', struct.pack('>h', int(value)))[0])
            elif data_type == 'uint32':
                registers.extend([(int(value) >> 16) & 0xFFFF, int(value) & 0xFFFF])
            elif data_type == 'int32':
                bytes_data = struct.pack('>i', int(value))
                registers.extend(struct.unpack('>HH', bytes_data))
            elif data_type == 'float32':
                bytes_data = struct.pack('>f', float(value))
                registers.extend(struct.unpack('>HH', bytes_data))
            else:
                registers.append(int(value) & 0xFFFF)
        
        return registers
    
    def _convert_single_value_to_register(self, value: Any, data_type: str) -> int:
        """Convertir valor único a registro Modbus."""
        if data_type == 'uint16':
            return int(value) & 0xFFFF
        elif data_type == 'int16':
            return struct.unpack('>H', struct.pack('>h', int(value)))[0]
        else:
            return int(value) & 0xFFFF


class ModbusTCP(ModbusProtocol):
    """Cliente Modbus TCP."""
    
    def __init__(self, host: str, port: int = 502, **kwargs):
        config = ProtocolConfig(
            protocol_type=ProtocolType.MODBUS_TCP,
            host=host,
            port=port,
            **kwargs
        )
        super().__init__(config)


class ModbusRTU(ModbusProtocol):
    """Cliente Modbus RTU."""
    
    def __init__(self, port: str, baudrate: int = 9600, **kwargs):
        config = ProtocolConfig(
            protocol_type=ProtocolType.MODBUS_RTU,
            host=port,  # Para RTU, host es el puerto serial
            port=baudrate,
            **kwargs
        )
        super().__init__(config) 