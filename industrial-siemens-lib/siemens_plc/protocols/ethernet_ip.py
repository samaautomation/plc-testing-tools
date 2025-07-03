"""
Ethernet/IP Protocol Module
===========================

Implementación del protocolo Ethernet/IP.
Soporte para comunicación con dispositivos Allen-Bradley, VFDs y otros dispositivos CIP.
"""

import asyncio
import struct
import time
from typing import Any, Dict, List, Optional, Union
import logging

try:
    import cpppo
    from cpppo.server.enip import client
    ETHERNET_IP_AVAILABLE = True
except ImportError:
    ETHERNET_IP_AVAILABLE = False
    logging.warning("cpppo not available. Install with: pip install cpppo")

from .base import BaseProtocol, ProtocolConfig, ProtocolType, ReadRequest, WriteRequest


class EthernetIPProtocol(BaseProtocol):
    """Cliente Ethernet/IP."""
    
    def __init__(self, config: ProtocolConfig):
        if not ETHERNET_IP_AVAILABLE:
            raise ImportError("cpppo library is required for Ethernet/IP support")
        
        super().__init__(config)
        self._client = None
        self._session_id = None
    
    async def connect(self) -> bool:
        """Conectar al dispositivo Ethernet/IP."""
        try:
            async with self._lock:
                if self._client and self._session_id:
                    return True
                
                # Crear cliente Ethernet/IP
                self._client = client.connector(
                    host=self.config.host,
                    port=self.config.port,
                    timeout=self.config.timeout / 1000
                )
                
                # Establecer conexión
                await self._client.__aenter__()
                
                # Registrar sesión
                self._session_id = await self._register_session()
                
                if self._session_id:
                    self.status.is_connected = True
                    await self._start_heartbeat()
                    self.logger.info(f"Connected to Ethernet/IP device at {self.config.host}")
                    return True
                else:
                    self.logger.error(f"Failed to connect to Ethernet/IP device at {self.config.host}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Ethernet/IP connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Desconectar del dispositivo Ethernet/IP."""
        try:
            async with self._lock:
                await self._stop_heartbeat()
                
                if self._session_id:
                    await self._unregister_session()
                    self._session_id = None
                
                if self._client:
                    await self._client.__aexit__(None, None, None)
                    self._client = None
                
                self.status.is_connected = False
                self.logger.info("Disconnected from Ethernet/IP device")
                return True
                
        except Exception as e:
            self.logger.error(f"Ethernet/IP disconnect error: {e}")
            return False
    
    async def read_data(self, request: ReadRequest) -> List[Any]:
        """Leer datos Ethernet/IP."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._session_id:
                    raise Exception("Not connected to Ethernet/IP device")
                
                # Construir ruta CIP
                cip_path = self._build_cip_path(request.address)
                
                # Leer datos usando servicio Read Tag
                data = await self._read_tag(cip_path, request.count)
                
                # Convertir datos según el tipo
                converted_data = self._convert_cip_data(data, request.data_type, request.count)
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return converted_data
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"Ethernet/IP read error: {e}")
            raise
    
    async def write_data(self, request: WriteRequest) -> bool:
        """Escribir datos Ethernet/IP."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._session_id:
                    raise Exception("Not connected to Ethernet/IP device")
                
                # Construir ruta CIP
                cip_path = self._build_cip_path(request.address)
                
                # Convertir datos a formato CIP
                cip_data = self._convert_data_to_cip(request.value, request.data_type)
                
                # Escribir datos usando servicio Write Tag
                result = await self._write_tag(cip_path, cip_data)
                
                if not result:
                    raise Exception("Failed to write data to Ethernet/IP device")
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return True
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"Ethernet/IP write error: {e}")
            raise
    
    async def read_multiple(self, requests: List[ReadRequest]) -> Dict[int, List[Any]]:
        """Leer múltiples registros Ethernet/IP."""
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
        """Escribir múltiples registros Ethernet/IP."""
        results = {}
        
        for i, request in enumerate(requests):
            try:
                success = await self.write_data(request)
                results[i] = success
            except Exception as e:
                self.logger.error(f"Error writing request {i}: {e}")
                results[i] = False
        
        return results
    
    async def _register_session(self) -> Optional[int]:
        """Registrar sesión Ethernet/IP."""
        try:
            # Enviar comando Register Session
            register_cmd = b'\x65\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            response = await self._client.send(register_cmd)
            
            if response and len(response) >= 4:
                # Extraer Session Handle de la respuesta
                session_id = struct.unpack('>I', response[4:8])[0]
                return session_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Session registration error: {e}")
            return None
    
    async def _unregister_session(self) -> bool:
        """Desregistrar sesión Ethernet/IP."""
        try:
            if not self._session_id:
                return True
            
            # Enviar comando Unregister Session
            unregister_cmd = struct.pack('>BBHI', 0x66, 0x00, 0x00, self._session_id)
            await self._client.send(unregister_cmd)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Session unregistration error: {e}")
            return False
    
    def _build_cip_path(self, address: Union[int, str]) -> bytes:
        """Construir ruta CIP."""
        if isinstance(address, str):
            # Ruta simbólica (ej: "Tag1")
            path = b'\x91' + len(address).to_bytes(1, 'big') + address.encode('ascii')
        else:
            # Ruta numérica (ej: 100)
            path = b'\x20\x24' + address.to_bytes(2, 'big')
        
        return path
    
    async def _read_tag(self, cip_path: bytes, count: int) -> bytes:
        """Leer tag usando servicio Read Tag."""
        try:
            # Construir comando Read Tag
            cmd = struct.pack('>BBHI', 0x70, 0x00, 0x00, self._session_id)
            cmd += b'\x00\x00\x00\x00'  # Interface Handle
            cmd += b'\x00\x00\x00\x00'  # Timeout
            cmd += struct.pack('>H', 2)  # Item Count
            
            # Item 1: Null Address Item
            cmd += b'\x00\x00'
            
            # Item 2: Connected Address Item
            cmd += b'\xB2\x00' + struct.pack('>H', len(cip_path)) + cip_path
            
            # Enviar comando
            response = await self._client.send(cmd)
            
            if response and len(response) >= 28:
                # Extraer datos de la respuesta
                data_length = struct.unpack('>H', response[26:28])[0]
                if len(response) >= 28 + data_length:
                    return response[28:28+data_length]
            
            return b''
            
        except Exception as e:
            self.logger.error(f"Read tag error: {e}")
            return b''
    
    async def _write_tag(self, cip_path: bytes, data: bytes) -> bool:
        """Escribir tag usando servicio Write Tag."""
        try:
            # Construir comando Write Tag
            cmd = struct.pack('>BBHI', 0x70, 0x00, 0x00, self._session_id)
            cmd += b'\x00\x00\x00\x00'  # Interface Handle
            cmd += b'\x00\x00\x00\x00'  # Timeout
            cmd += struct.pack('>H', 2)  # Item Count
            
            # Item 1: Null Address Item
            cmd += b'\x00\x00'
            
            # Item 2: Connected Address Item
            cmd += b'\xB2\x00' + struct.pack('>H', len(cip_path) + len(data)) + cip_path + data
            
            # Enviar comando
            response = await self._client.send(cmd)
            
            # Verificar respuesta
            if response and len(response) >= 24:
                status = struct.unpack('>H', response[22:24])[0]
                return status == 0
            
            return False
            
        except Exception as e:
            self.logger.error(f"Write tag error: {e}")
            return False
    
    def _convert_cip_data(self, data: bytes, data_type: str, count: int) -> List[Any]:
        """Convertir datos CIP a tipos específicos."""
        if data_type == 'bool':
            return [bool(data[i]) for i in range(count)]
        elif data_type == 'uint8':
            return [data[i] for i in range(count)]
        elif data_type == 'int8':
            return [struct.unpack('b', bytes([data[i]]))[0] for i in range(count)]
        elif data_type == 'uint16':
            return [struct.unpack('>H', data[i:i+2])[0] for i in range(0, len(data), 2)]
        elif data_type == 'int16':
            return [struct.unpack('>h', data[i:i+2])[0] for i in range(0, len(data), 2)]
        elif data_type == 'uint32':
            return [struct.unpack('>I', data[i:i+4])[0] for i in range(0, len(data), 4)]
        elif data_type == 'int32':
            return [struct.unpack('>i', data[i:i+4])[0] for i in range(0, len(data), 4)]
        elif data_type == 'float32':
            return [struct.unpack('>f', data[i:i+4])[0] for i in range(0, len(data), 4)]
        elif data_type == 'float64':
            return [struct.unpack('>d', data[i:i+8])[0] for i in range(0, len(data), 8)]
        else:
            return list(data)
    
    def _convert_data_to_cip(self, value: Any, data_type: str) -> bytes:
        """Convertir datos a formato CIP."""
        if isinstance(value, (list, tuple)):
            values = value
        else:
            values = [value]
        
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