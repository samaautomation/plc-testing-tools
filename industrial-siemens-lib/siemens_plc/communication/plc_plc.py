"""
PLC-PLC Communication Module
============================

Módulo para comunicación entre múltiples PLCs.
Soporte para redes de PLCs con sincronización de datos.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union, Callable
import logging
from dataclasses import dataclass
from datetime import datetime

from ..protocols.base import BaseProtocol, ProtocolConfig, ProtocolType
from ..protocols.modbus import ModbusTCP, ModbusRTU
from ..protocols.s7 import S7Protocol
from ..protocols.profibus import ProfibusDP
from ..exceptions import CommunicationError


@dataclass
class PLCNode:
    """Configuración de un nodo PLC en la red."""
    id: str
    name: str
    protocol: BaseProtocol
    is_master: bool = False
    sync_interval: int = 1000  # ms
    priority: int = 1
    enabled: bool = True


@dataclass
class DataMapping:
    """Mapeo de datos entre PLCs."""
    source_plc: str
    source_address: Union[int, str]
    source_data_type: str
    target_plc: str
    target_address: Union[int, str]
    target_data_type: str
    sync_mode: str = "continuous"  # continuous, on_change, periodic
    sync_interval: int = 1000  # ms
    enabled: bool = True


class PLCToPLCCommunication:
    """
    Sistema de comunicación PLC-PLC.
    
    Permite la comunicación y sincronización de datos entre múltiples PLCs
    usando diferentes protocolos (S7, Modbus, Profibus, etc.).
    """
    
    def __init__(self):
        self.logger = logging.getLogger("PLC-PLC-Communication")
        self.plcs: Dict[str, PLCNode] = {}
        self.data_mappings: List[DataMapping] = []
        self.sync_tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        self._lock = asyncio.Lock()
        
        # Callbacks
        self.on_data_sync: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_connection_change: Optional[Callable] = None
    
    async def add_plc(self, plc_config: PLCNode) -> bool:
        """Agregar PLC a la red."""
        try:
            async with self._lock:
                if plc_config.id in self.plcs:
                    self.logger.warning(f"PLC {plc_config.id} already exists")
                    return False
                
                # Conectar al PLC
                if await plc_config.protocol.connect():
                    self.plcs[plc_config.id] = plc_config
                    self.logger.info(f"Added PLC {plc_config.id} ({plc_config.name})")
                    
                    # Iniciar sincronización si es master
                    if plc_config.is_master:
                        await self._start_sync_for_plc(plc_config.id)
                    
                    if self.on_connection_change:
                        await self.on_connection_change(plc_config.id, True)
                    
                    return True
                else:
                    self.logger.error(f"Failed to connect to PLC {plc_config.id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error adding PLC {plc_config.id}: {e}")
            return False
    
    async def remove_plc(self, plc_id: str) -> bool:
        """Remover PLC de la red."""
        try:
            async with self._lock:
                if plc_id not in self.plcs:
                    return False
                
                # Detener sincronización
                await self._stop_sync_for_plc(plc_id)
                
                # Desconectar PLC
                plc = self.plcs[plc_id]
                await plc.protocol.disconnect()
                
                del self.plcs[plc_id]
                self.logger.info(f"Removed PLC {plc_id}")
                
                if self.on_connection_change:
                    await self.on_connection_change(plc_id, False)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error removing PLC {plc_id}: {e}")
            return False
    
    async def add_data_mapping(self, mapping: DataMapping) -> bool:
        """Agregar mapeo de datos entre PLCs."""
        try:
            async with self._lock:
                # Verificar que ambos PLCs existan
                if mapping.source_plc not in self.plcs:
                    raise CommunicationError(f"Source PLC {mapping.source_plc} not found")
                
                if mapping.target_plc not in self.plcs:
                    raise CommunicationError(f"Target PLC {mapping.target_plc} not found")
                
                self.data_mappings.append(mapping)
                self.logger.info(f"Added data mapping: {mapping.source_plc} -> {mapping.target_plc}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error adding data mapping: {e}")
            return False
    
    async def remove_data_mapping(self, source_plc: str, target_plc: str) -> bool:
        """Remover mapeo de datos."""
        try:
            async with self._lock:
                # Encontrar y remover mapeo
                for i, mapping in enumerate(self.data_mappings):
                    if mapping.source_plc == source_plc and mapping.target_plc == target_plc:
                        del self.data_mappings[i]
                        self.logger.info(f"Removed data mapping: {source_plc} -> {target_plc}")
                        return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing data mapping: {e}")
            return False
    
    async def start_communication(self) -> bool:
        """Iniciar comunicación PLC-PLC."""
        try:
            async with self._lock:
                if self.running:
                    return True
                
                self.running = True
                
                # Iniciar sincronización para todos los PLCs master
                for plc_id, plc in self.plcs.items():
                    if plc.is_master and plc.enabled:
                        await self._start_sync_for_plc(plc_id)
                
                self.logger.info("PLC-PLC communication started")
                return True
                
        except Exception as e:
            self.logger.error(f"Error starting communication: {e}")
            return False
    
    async def stop_communication(self) -> bool:
        """Detener comunicación PLC-PLC."""
        try:
            async with self._lock:
                if not self.running:
                    return True
                
                self.running = False
                
                # Detener todas las tareas de sincronización
                for plc_id in list(self.sync_tasks.keys()):
                    await self._stop_sync_for_plc(plc_id)
                
                self.logger.info("PLC-PLC communication stopped")
                return True
                
        except Exception as e:
            self.logger.error(f"Error stopping communication: {e}")
            return False
    
    async def sync_data_once(self, mapping: DataMapping) -> bool:
        """Sincronizar datos una vez según el mapeo."""
        try:
            # Leer datos del PLC origen
            source_plc = self.plcs[mapping.source_plc]
            from ..protocols.base import ReadRequest, WriteRequest
            
            read_request = ReadRequest(
                address=mapping.source_address,
                count=1,
                data_type=mapping.source_data_type
            )
            
            source_data = await source_plc.protocol.read_data(read_request)
            
            if not source_data:
                return False
            
            # Escribir datos al PLC destino
            target_plc = self.plcs[mapping.target_plc]
            
            write_request = WriteRequest(
                address=mapping.target_address,
                value=source_data[0],
                data_type=mapping.target_data_type
            )
            
            success = await target_plc.protocol.write_data(write_request)
            
            if success and self.on_data_sync:
                await self.on_data_sync(mapping, source_data[0])
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error syncing data: {e}")
            if self.on_error:
                await self.on_error(mapping, e)
            return False
    
    async def get_network_status(self) -> Dict[str, Any]:
        """Obtener estado de la red PLC-PLC."""
        status = {
            'running': self.running,
            'plcs': {},
            'mappings': len(self.data_mappings),
            'sync_tasks': len(self.sync_tasks)
        }
        
        for plc_id, plc in self.plcs.items():
            plc_status = await plc.protocol.get_status()
            status['plcs'][plc_id] = {
                'name': plc.name,
                'is_master': plc.is_master,
                'enabled': plc.enabled,
                'connected': plc_status.is_connected,
                'last_communication': plc_status.last_communication,
                'error_count': plc_status.error_count,
                'success_count': plc_status.success_count
            }
        
        return status
    
    async def _start_sync_for_plc(self, plc_id: str) -> None:
        """Iniciar sincronización para un PLC específico."""
        if plc_id in self.sync_tasks:
            return
        
        plc = self.plcs[plc_id]
        
        async def sync_loop():
            while self.running and plc_id in self.plcs:
                try:
                    # Encontrar mapeos donde este PLC es origen
                    for mapping in self.data_mappings:
                        if (mapping.source_plc == plc_id and 
                            mapping.enabled and 
                            mapping.sync_mode == "continuous"):
                            
                            await self.sync_data_once(mapping)
                    
                    # Esperar intervalo de sincronización
                    await asyncio.sleep(plc.sync_interval / 1000)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error in sync loop for PLC {plc_id}: {e}")
                    await asyncio.sleep(1)
        
        self.sync_tasks[plc_id] = asyncio.create_task(sync_loop())
        self.logger.info(f"Started sync for PLC {plc_id}")
    
    async def _stop_sync_for_plc(self, plc_id: str) -> None:
        """Detener sincronización para un PLC específico."""
        if plc_id in self.sync_tasks:
            self.sync_tasks[plc_id].cancel()
            try:
                await self.sync_tasks[plc_id]
            except asyncio.CancelledError:
                pass
            del self.sync_tasks[plc_id]
            self.logger.info(f"Stopped sync for PLC {plc_id}")


class PLCNetwork:
    """
    Red de PLCs con gestión automática.
    
    Proporciona una interfaz de alto nivel para gestionar una red de PLCs
    con configuración automática y recuperación de errores.
    """
    
    def __init__(self, name: str = "PLC_Network"):
        self.name = name
        self.logger = logging.getLogger(f"PLC-Network-{name}")
        self.communication = PLCToPLCCommunication()
        self.config: Dict[str, Any] = {}
        self.auto_recovery = True
        self.recovery_interval = 5000  # ms
        
        # Configurar callbacks
        self.communication.on_data_sync = self._on_data_sync
        self.communication.on_error = self._on_error
        self.communication.on_connection_change = self._on_connection_change
    
    async def load_config(self, config: Dict[str, Any]) -> bool:
        """Cargar configuración de la red."""
        try:
            self.config = config
            
            # Configurar PLCs
            for plc_config in config.get('plcs', []):
                await self._create_plc_from_config(plc_config)
            
            # Configurar mapeos de datos
            for mapping_config in config.get('mappings', []):
                await self._create_mapping_from_config(mapping_config)
            
            self.logger.info(f"Loaded configuration for network {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False
    
    async def start_network(self) -> bool:
        """Iniciar la red de PLCs."""
        try:
            success = await self.communication.start_communication()
            
            if success and self.auto_recovery:
                # Iniciar tarea de recuperación automática
                asyncio.create_task(self._auto_recovery_loop())
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error starting network: {e}")
            return False
    
    async def stop_network(self) -> bool:
        """Detener la red de PLCs."""
        try:
            return await self.communication.stop_communication()
        except Exception as e:
            self.logger.error(f"Error stopping network: {e}")
            return False
    
    async def get_network_info(self) -> Dict[str, Any]:
        """Obtener información de la red."""
        status = await self.communication.get_network_status()
        
        return {
            'name': self.name,
            'config': self.config,
            'status': status,
            'auto_recovery': self.auto_recovery
        }
    
    async def _create_plc_from_config(self, plc_config: Dict[str, Any]) -> None:
        """Crear PLC desde configuración."""
        try:
            # Crear protocolo según configuración
            protocol_type = plc_config.get('protocol', 's7')
            protocol = await self._create_protocol(protocol_type, plc_config)
            
            # Crear nodo PLC
            plc_node = PLCNode(
                id=plc_config['id'],
                name=plc_config.get('name', plc_config['id']),
                protocol=protocol,
                is_master=plc_config.get('is_master', False),
                sync_interval=plc_config.get('sync_interval', 1000),
                priority=plc_config.get('priority', 1),
                enabled=plc_config.get('enabled', True)
            )
            
            await self.communication.add_plc(plc_node)
            
        except Exception as e:
            self.logger.error(f"Error creating PLC from config: {e}")
    
    async def _create_protocol(self, protocol_type: str, config: Dict[str, Any]) -> BaseProtocol:
        """Crear protocolo según tipo."""
        protocol_config = ProtocolConfig(
            protocol_type=ProtocolType(protocol_type),
            host=config['host'],
            port=config.get('port', 502),
            timeout=config.get('timeout', 5000),
            retry_count=config.get('retry_count', 3),
            debug=config.get('debug', False)
        )
        
        if protocol_type == 's7':
            return S7Protocol(protocol_config)
        elif protocol_type == 'modbus_tcp':
            return ModbusTCP(config['host'], config.get('port', 502))
        elif protocol_type == 'modbus_rtu':
            return ModbusRTU(config['host'], config.get('baudrate', 9600))
        elif protocol_type == 'profibus_dp':
            return ProfibusDP(config['host'], config.get('slave_address', 1))
        else:
            raise ValueError(f"Unsupported protocol type: {protocol_type}")
    
    async def _create_mapping_from_config(self, mapping_config: Dict[str, Any]) -> None:
        """Crear mapeo desde configuración."""
        try:
            mapping = DataMapping(
                source_plc=mapping_config['source_plc'],
                source_address=mapping_config['source_address'],
                source_data_type=mapping_config['source_data_type'],
                target_plc=mapping_config['target_plc'],
                target_address=mapping_config['target_address'],
                target_data_type=mapping_config['target_data_type'],
                sync_mode=mapping_config.get('sync_mode', 'continuous'),
                sync_interval=mapping_config.get('sync_interval', 1000),
                enabled=mapping_config.get('enabled', True)
            )
            
            await self.communication.add_data_mapping(mapping)
            
        except Exception as e:
            self.logger.error(f"Error creating mapping from config: {e}")
    
    async def _auto_recovery_loop(self) -> None:
        """Bucle de recuperación automática."""
        while self.communication.running:
            try:
                await asyncio.sleep(self.recovery_interval / 1000)
                
                # Verificar conexiones y reconectar si es necesario
                for plc_id, plc in self.communication.plcs.items():
                    status = await plc.protocol.get_status()
                    if not status.is_connected and plc.enabled:
                        self.logger.info(f"Attempting to reconnect PLC {plc_id}")
                        await plc.protocol.connect()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in auto recovery loop: {e}")
    
    async def _on_data_sync(self, mapping: DataMapping, value: Any) -> None:
        """Callback cuando se sincronizan datos."""
        self.logger.debug(f"Data synced: {mapping.source_plc} -> {mapping.target_plc}: {value}")
    
    async def _on_error(self, mapping: DataMapping, error: Exception) -> None:
        """Callback cuando hay error en sincronización."""
        self.logger.error(f"Sync error: {mapping.source_plc} -> {mapping.target_plc}: {error}")
    
    async def _on_connection_change(self, plc_id: str, connected: bool) -> None:
        """Callback cuando cambia la conexión de un PLC."""
        status = "connected" if connected else "disconnected"
        self.logger.info(f"PLC {plc_id} {status}") 