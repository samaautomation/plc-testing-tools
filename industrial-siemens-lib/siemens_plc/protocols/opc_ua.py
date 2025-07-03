"""
OPC UA Protocol Module
======================

Implementación del protocolo OPC UA.
Soporte para comunicación estándar industrial con dispositivos OPC UA.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
import logging

try:
    import asyncua
    from asyncua import Client, ua
    OPC_UA_AVAILABLE = True
except ImportError:
    OPC_UA_AVAILABLE = False
    logging.warning("asyncua not available. Install with: pip install asyncua")

from .base import BaseProtocol, ProtocolConfig, ProtocolType, ReadRequest, WriteRequest


class OPCUAProtocol(BaseProtocol):
    """Cliente OPC UA."""
    
    def __init__(self, config: ProtocolConfig):
        if not OPC_UA_AVAILABLE:
            raise ImportError("asyncua library is required for OPC UA support")
        
        super().__init__(config)
        self._client = None
        self._namespace_map = {}
    
    async def connect(self) -> bool:
        """Conectar al servidor OPC UA."""
        try:
            async with self._lock:
                if self._client and self._client.session:
                    return True
                
                # Crear cliente OPC UA
                url = f"opc.tcp://{self.config.host}:{self.config.port}"
                self._client = Client(url=url)
                
                # Configurar timeout
                self._client.session_timeout = self.config.timeout
                
                # Conectar
                await self._client.connect()
                
                # Obtener información del servidor
                await self._get_namespace_map()
                
                self.status.is_connected = True
                await self._start_heartbeat()
                self.logger.info(f"Connected to OPC UA server at {url}")
                return True
                
        except Exception as e:
            self.logger.error(f"OPC UA connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Desconectar del servidor OPC UA."""
        try:
            async with self._lock:
                await self._stop_heartbeat()
                
                if self._client:
                    await self._client.disconnect()
                    self._client = None
                
                self.status.is_connected = False
                self.logger.info("Disconnected from OPC UA server")
                return True
                
        except Exception as e:
            self.logger.error(f"OPC UA disconnect error: {e}")
            return False
    
    async def read_data(self, request: ReadRequest) -> List[Any]:
        """Leer datos OPC UA."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._client.session:
                    raise Exception("Not connected to OPC UA server")
                
                # Construir NodeId
                node_id = self._build_node_id(request.address)
                
                # Leer nodo
                node = self._client.get_node(node_id)
                value = await node.read_value()
                
                # Convertir valor según el tipo de datos
                converted_data = self._convert_opc_value(value, request.data_type)
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return [converted_data]
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"OPC UA read error: {e}")
            raise
    
    async def write_data(self, request: WriteRequest) -> bool:
        """Escribir datos OPC UA."""
        start_time = time.time()
        
        try:
            async with self._lock:
                if not self._client or not self._client.session:
                    raise Exception("Not connected to OPC UA server")
                
                # Construir NodeId
                node_id = self._build_node_id(request.address)
                
                # Convertir valor a tipo OPC UA
                opc_value = self._convert_to_opc_value(request.value, request.data_type)
                
                # Escribir nodo
                node = self._client.get_node(node_id)
                await node.write_value(opc_value)
                
                response_time = (time.time() - start_time) * 1000
                await self._update_statistics(True, response_time)
                
                return True
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_statistics(False, response_time)
            self.logger.error(f"OPC UA write error: {e}")
            raise
    
    async def read_multiple(self, requests: List[ReadRequest]) -> Dict[int, List[Any]]:
        """Leer múltiples nodos OPC UA."""
        results = {}
        
        try:
            async with self._lock:
                if not self._client or not self._client.session:
                    raise Exception("Not connected to OPC UA server")
                
                # Construir lista de NodeIds
                node_ids = [self._build_node_id(req.address) for req in requests]
                
                # Leer múltiples nodos
                nodes = [self._client.get_node(node_id) for node_id in node_ids]
                values = await asyncio.gather(*[node.read_value() for node in nodes])
                
                # Convertir valores
                for i, (value, request) in enumerate(zip(values, requests)):
                    converted_data = self._convert_opc_value(value, request.data_type)
                    results[i] = [converted_data]
                
        except Exception as e:
            self.logger.error(f"OPC UA multiple read error: {e}")
            # Fallback a lecturas individuales
            for i, request in enumerate(requests):
                try:
                    data = await self.read_data(request)
                    results[i] = data
                except Exception as e:
                    self.logger.error(f"Error reading request {i}: {e}")
                    results[i] = []
        
        return results
    
    async def write_multiple(self, requests: List[WriteRequest]) -> Dict[int, bool]:
        """Escribir múltiples nodos OPC UA."""
        results = {}
        
        try:
            async with self._lock:
                if not self._client or not self._client.session:
                    raise Exception("Not connected to OPC UA server")
                
                # Construir lista de operaciones de escritura
                write_operations = []
                for request in requests:
                    node_id = self._build_node_id(request.address)
                    opc_value = self._convert_to_opc_value(request.value, request.data_type)
                    node = self._client.get_node(node_id)
                    write_operations.append(node.write_value(opc_value))
                
                # Ejecutar escrituras en paralelo
                await asyncio.gather(*write_operations)
                
                # Todos exitosos
                for i in range(len(requests)):
                    results[i] = True
                
        except Exception as e:
            self.logger.error(f"OPC UA multiple write error: {e}")
            # Fallback a escrituras individuales
            for i, request in enumerate(requests):
                try:
                    success = await self.write_data(request)
                    results[i] = success
                except Exception as e:
                    self.logger.error(f"Error writing request {i}: {e}")
                    results[i] = False
        
        return results
    
    async def browse_nodes(self, node_id: str = "i=84") -> List[Dict[str, Any]]:
        """Explorar nodos del servidor OPC UA."""
        try:
            async with self._lock:
                if not self._client or not self._client.session:
                    raise Exception("Not connected to OPC UA server")
                
                # Construir NodeId
                browse_node_id = self._build_node_id(node_id)
                node = self._client.get_node(browse_node_id)
                
                # Explorar nodos
                children = await node.get_children()
                
                nodes_info = []
                for child in children:
                    try:
                        # Obtener información del nodo
                        node_class = await child.read_node_class()
                        browse_name = await child.read_browse_name()
                        display_name = await child.read_display_name()
                        
                        nodes_info.append({
                            'node_id': str(child.nodeid),
                            'browse_name': str(browse_name.Name),
                            'display_name': str(display_name.Text),
                            'node_class': str(node_class)
                        })
                    except Exception as e:
                        self.logger.warning(f"Error reading node info: {e}")
                
                return nodes_info
                
        except Exception as e:
            self.logger.error(f"OPC UA browse error: {e}")
            return []
    
    async def subscribe_to_nodes(self, node_ids: List[str], callback) -> str:
        """Suscribirse a cambios de nodos OPC UA."""
        try:
            async with self._lock:
                if not self._client or not self._client.session:
                    raise Exception("Not connected to OPC UA server")
                
                # Crear handler para notificaciones
                handler = SubscriptionHandler(callback)
                
                # Crear suscripción
                subscription = await self._client.create_subscription(
                    period=1000,  # 1 segundo
                    handler=handler
                )
                
                # Agregar nodos a la suscripción
                nodes = [self._client.get_node(self._build_node_id(node_id)) for node_id in node_ids]
                await subscription.subscribe_data_change(nodes)
                
                return str(subscription)
                
        except Exception as e:
            self.logger.error(f"OPC UA subscription error: {e}")
            raise
    
    async def _get_namespace_map(self) -> None:
        """Obtener mapa de namespaces del servidor."""
        try:
            # Obtener array de namespaces
            ns_array = await self._client.get_namespace_array()
            
            # Crear mapa
            for i, ns_uri in enumerate(ns_array):
                self._namespace_map[ns_uri] = i
            
        except Exception as e:
            self.logger.warning(f"Could not get namespace map: {e}")
    
    def _build_node_id(self, address: Union[int, str]) -> ua.NodeId:
        """Construir NodeId OPC UA."""
        if isinstance(address, str):
            # Formato: "ns=2;s=Tag1" o "i=84"
            if address.startswith('i='):
                # NodeId numérico
                node_id = int(address[2:])
                return ua.NodeId(node_id, 0)
            elif ';' in address:
                # NodeId con namespace
                parts = address.split(';')
                if len(parts) == 2:
                    ns_part, id_part = parts
                    if ns_part.startswith('ns='):
                        ns = int(ns_part[3:])
                        if id_part.startswith('s='):
                            # String identifier
                            identifier = id_part[2:]
                            return ua.NodeId(identifier, ns)
                        elif id_part.startswith('i='):
                            # Numeric identifier
                            identifier = int(id_part[2:])
                            return ua.NodeId(identifier, ns)
            
            # String identifier en namespace 0
            return ua.NodeId(address, 0)
        else:
            # Numeric identifier en namespace 0
            return ua.NodeId(int(address), 0)
    
    def _convert_opc_value(self, value: Any, data_type: str) -> Any:
        """Convertir valor OPC UA a tipo específico."""
        if isinstance(value, ua.DataValue):
            value = value.Value.Value
        
        if data_type == 'bool':
            return bool(value)
        elif data_type == 'uint8':
            return int(value) & 0xFF
        elif data_type == 'int8':
            return int(value) if -128 <= int(value) <= 127 else 0
        elif data_type == 'uint16':
            return int(value) & 0xFFFF
        elif data_type == 'int16':
            return int(value) if -32768 <= int(value) <= 32767 else 0
        elif data_type == 'uint32':
            return int(value) & 0xFFFFFFFF
        elif data_type == 'int32':
            return int(value)
        elif data_type == 'float32':
            return float(value)
        elif data_type == 'float64':
            return float(value)
        elif data_type == 'string':
            return str(value)
        else:
            return value
    
    def _convert_to_opc_value(self, value: Any, data_type: str) -> Any:
        """Convertir valor a tipo OPC UA."""
        if data_type == 'bool':
            return ua.Variant(value, ua.VariantType.Boolean)
        elif data_type == 'uint8':
            return ua.Variant(int(value) & 0xFF, ua.VariantType.Byte)
        elif data_type == 'int8':
            return ua.Variant(int(value), ua.VariantType.SByte)
        elif data_type == 'uint16':
            return ua.Variant(int(value) & 0xFFFF, ua.VariantType.UInt16)
        elif data_type == 'int16':
            return ua.Variant(int(value), ua.VariantType.Int16)
        elif data_type == 'uint32':
            return ua.Variant(int(value) & 0xFFFFFFFF, ua.VariantType.UInt32)
        elif data_type == 'int32':
            return ua.Variant(int(value), ua.VariantType.Int32)
        elif data_type == 'float32':
            return ua.Variant(float(value), ua.VariantType.Float)
        elif data_type == 'float64':
            return ua.Variant(float(value), ua.VariantType.Double)
        elif data_type == 'string':
            return ua.Variant(str(value), ua.VariantType.String)
        else:
            return ua.Variant(value)


class SubscriptionHandler:
    """Handler para suscripciones OPC UA."""
    
    def __init__(self, callback):
        self.callback = callback
        self.logger = logging.getLogger("OPCUA_Subscription")
    
    async def datachange_notification(self, node, val, data):
        """Notificación de cambio de datos."""
        try:
            await self.callback(str(node.nodeid), val, data)
        except Exception as e:
            self.logger.error(f"Error in datachange notification: {e}")
    
    async def event_notification(self, event):
        """Notificación de eventos."""
        try:
            await self.callback("event", event)
        except Exception as e:
            self.logger.error(f"Error in event notification: {e}") 