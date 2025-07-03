#!/usr/bin/env python3
"""
Multi-Protocol Industrial System Example
========================================

Ejemplo completo que demuestra el uso de todos los protocolos industriales:
- S7 (Siemens PLCs)
- Modbus TCP/RTU
- Profibus-DP
- Ethernet/IP
- OPC UA
- PLC-PLC Communication
- VFD Communication

Este ejemplo simula un sistema industrial completo con múltiples dispositivos.
"""

import asyncio
import logging
import time
from typing import Dict, Any
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar módulos de la librería
from siemens_plc.protocols import (
    S7Protocol, ModbusTCP, ModbusRTU, ProfibusDP, 
    EthernetIPProtocol, OPCUAProtocol
)
from siemens_plc.protocols.base import ProtocolConfig, ProtocolType, ReadRequest, WriteRequest
from siemens_plc.communication import PLCToPLCCommunication, PLCNetwork, VFDCommunication
from siemens_plc.exceptions import CommunicationError


class IndustrialSystemSimulator:
    """Simulador de sistema industrial completo."""
    
    def __init__(self):
        self.plcs = {}
        self.vfds = {}
        self.network = None
        self.running = False
        
        # Configuraciones de ejemplo
        self.plc_configs = {
            'plc_main': {
                'id': 'plc_main',
                'name': 'Main PLC (S7-1200)',
                'protocol': 's7',
                'host': '192.168.1.10',
                'rack': 0,
                'slot': 1,
                'is_master': True
            },
            'plc_aux': {
                'id': 'plc_aux', 
                'name': 'Auxiliary PLC (S7-300)',
                'protocol': 's7',
                'host': '192.168.1.11',
                'rack': 0,
                'slot': 1,
                'is_master': False
            },
            'plc_modbus': {
                'id': 'plc_modbus',
                'name': 'Modbus PLC',
                'protocol': 'modbus_tcp',
                'host': '192.168.1.12',
                'port': 502,
                'is_master': False
            }
        }
        
        self.vfd_configs = {
            'vfd_motor1': {
                'id': 'vfd_motor1',
                'name': 'Motor 1 VFD',
                'protocol': 'modbus_tcp',
                'host': '192.168.1.20',
                'port': 502,
                'manufacturer': 'Siemens',
                'model': 'G120',
                'power_rating': 5.5,
                'max_frequency': 60.0,
                'max_speed': 1750.0
            },
            'vfd_motor2': {
                'id': 'vfd_motor2',
                'name': 'Motor 2 VFD',
                'protocol': 'modbus_tcp',
                'host': '192.168.1.21',
                'port': 502,
                'manufacturer': 'Allen-Bradley',
                'model': 'PowerFlex 525',
                'power_rating': 3.0,
                'max_frequency': 60.0,
                'max_speed': 1750.0
            }
        }
    
    async def start_system(self):
        """Iniciar el sistema industrial."""
        logger.info("🚀 Starting Industrial System...")
        
        try:
            # Crear red PLC-PLC
            self.network = PLCNetwork("Industrial_Network")
            
            # Configurar callbacks
            self.network.communication.on_data_sync = self._on_data_sync
            self.network.communication.on_error = self._on_error
            self.network.communication.on_connection_change = self._on_connection_change
            
            # Cargar configuración
            config = {
                'plcs': list(self.plc_configs.values()),
                'mappings': [
                    {
                        'source_plc': 'plc_main',
                        'source_address': 100,
                        'source_data_type': 'float32',
                        'target_plc': 'plc_aux',
                        'target_address': 200,
                        'target_data_type': 'float32',
                        'sync_mode': 'continuous',
                        'sync_interval': 1000
                    },
                    {
                        'source_plc': 'plc_main',
                        'source_address': 101,
                        'source_data_type': 'bool',
                        'target_plc': 'plc_modbus',
                        'target_address': 1,
                        'target_data_type': 'coil',
                        'sync_mode': 'on_change',
                        'sync_interval': 500
                    }
                ]
            }
            
            await self.network.load_config(config)
            
            # Iniciar red
            await self.network.start_network()
            
            # Crear VFDs
            await self._create_vfds()
            
            self.running = True
            logger.info("✅ Industrial System started successfully")
            
            # Iniciar tareas de demostración
            asyncio.create_task(self._demonstration_loop())
            
        except Exception as e:
            logger.error(f"❌ Error starting system: {e}")
            raise
    
    async def stop_system(self):
        """Detener el sistema industrial."""
        logger.info("🛑 Stopping Industrial System...")
        
        self.running = False
        
        # Detener VFDs
        for vfd in self.vfds.values():
            try:
                await vfd.disconnect()
            except Exception as e:
                logger.error(f"Error stopping VFD {vfd.config.id}: {e}")
        
        # Detener red PLC
        if self.network:
            try:
                await self.network.stop_network()
            except Exception as e:
                logger.error(f"Error stopping network: {e}")
        
        logger.info("✅ Industrial System stopped")
    
    async def _create_vfds(self):
        """Crear y conectar VFDs."""
        logger.info("🔌 Creating VFDs...")
        
        for vfd_id, config in self.vfd_configs.items():
            try:
                # Crear VFD
                vfd = await VFDCommunication.create_vfd(
                    config['protocol'], 
                    config
                )
                
                # Configurar callbacks
                vfd.on_status_change = self._on_vfd_status_change
                vfd.on_fault = self._on_vfd_fault
                
                # Conectar
                if await vfd.connect():
                    self.vfds[vfd_id] = vfd
                    logger.info(f"✅ Connected to VFD {vfd_id}")
                else:
                    logger.warning(f"⚠️ Failed to connect to VFD {vfd_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error creating VFD {vfd_id}: {e}")
    
    async def _demonstration_loop(self):
        """Bucle de demostración del sistema."""
        logger.info("🎯 Starting demonstration loop...")
        
        step = 0
        while self.running:
            try:
                step += 1
                logger.info(f"📊 Demonstration Step {step}")
                
                # Paso 1: Leer estado de PLCs
                if step == 1:
                    await self._demonstrate_plc_reading()
                
                # Paso 2: Escribir datos a PLCs
                elif step == 2:
                    await self._demonstrate_plc_writing()
                
                # Paso 3: Controlar VFDs
                elif step == 3:
                    await self._demonstrate_vfd_control()
                
                # Paso 4: Leer parámetros de VFDs
                elif step == 4:
                    await self._demonstrate_vfd_monitoring()
                
                # Paso 5: Mostrar estado de la red
                elif step == 5:
                    await self._demonstrate_network_status()
                
                # Reiniciar ciclo
                elif step > 5:
                    step = 0
                
                # Esperar entre pasos
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in demonstration loop: {e}")
                await asyncio.sleep(5)
    
    async def _demonstrate_plc_reading(self):
        """Demostrar lectura de PLCs."""
        logger.info("📖 Demonstrating PLC Reading...")
        
        for plc_id, plc_config in self.plc_configs.items():
            try:
                # Simular lectura de diferentes tipos de datos
                read_requests = [
                    ReadRequest(address=100, count=1, data_type='float32'),
                    ReadRequest(address=101, count=1, data_type='bool'),
                    ReadRequest(address=102, count=1, data_type='uint16'),
                    ReadRequest(address=103, count=1, data_type='int32')
                ]
                
                logger.info(f"Reading from {plc_id}...")
                
                # En un sistema real, usaríamos el protocolo correspondiente
                # Aquí simulamos los datos
                simulated_data = {
                    'float32': 123.45,
                    'bool': True,
                    'uint16': 1234,
                    'int32': -5678
                }
                
                for i, request in enumerate(read_requests):
                    logger.info(f"  {request.data_type}: {simulated_data[request.data_type]}")
                
            except Exception as e:
                logger.error(f"Error reading from {plc_id}: {e}")
    
    async def _demonstrate_plc_writing(self):
        """Demostrar escritura a PLCs."""
        logger.info("✍️ Demonstrating PLC Writing...")
        
        for plc_id, plc_config in self.plc_configs.items():
            try:
                # Simular escritura de diferentes tipos de datos
                write_requests = [
                    WriteRequest(address=200, value=456.78, data_type='float32'),
                    WriteRequest(address=201, value=True, data_type='bool'),
                    WriteRequest(address=202, value=5678, data_type='uint16'),
                    WriteRequest(address=203, value=-1234, data_type='int32')
                ]
                
                logger.info(f"Writing to {plc_id}...")
                
                for request in write_requests:
                    logger.info(f"  {request.data_type}: {request.value}")
                
            except Exception as e:
                logger.error(f"Error writing to {plc_id}: {e}")
    
    async def _demonstrate_vfd_control(self):
        """Demostrar control de VFDs."""
        logger.info("⚡ Demonstrating VFD Control...")
        
        for vfd_id, vfd in self.vfds.items():
            try:
                logger.info(f"Controlling {vfd_id}...")
                
                # Simular control de VFD
                await vfd.set_frequency(30.0)  # 30 Hz
                logger.info(f"  Set frequency to 30 Hz")
                
                await vfd.set_speed(875.0)  # 875 RPM
                logger.info(f"  Set speed to 875 RPM")
                
                # Simular inicio
                await vfd.start_drive()
                logger.info(f"  Started drive")
                
            except Exception as e:
                logger.error(f"Error controlling {vfd_id}: {e}")
    
    async def _demonstrate_vfd_monitoring(self):
        """Demostrar monitoreo de VFDs."""
        logger.info("📊 Demonstrating VFD Monitoring...")
        
        for vfd_id, vfd in self.vfds.items():
            try:
                logger.info(f"Monitoring {vfd_id}...")
                
                # Leer parámetros
                params = await vfd.read_parameters()
                
                logger.info(f"  Output Frequency: {params.output_frequency} Hz")
                logger.info(f"  Output Speed: {params.output_speed} RPM")
                logger.info(f"  Output Current: {params.output_current} A")
                logger.info(f"  Output Voltage: {params.output_voltage} V")
                logger.info(f"  Status: {params.status.value}")
                
            except Exception as e:
                logger.error(f"Error monitoring {vfd_id}: {e}")
    
    async def _demonstrate_network_status(self):
        """Demostrar estado de la red."""
        logger.info("🌐 Demonstrating Network Status...")
        
        if self.network:
            try:
                network_info = await self.network.get_network_info()
                
                logger.info(f"Network: {network_info['name']}")
                logger.info(f"Running: {network_info['status']['running']}")
                logger.info(f"PLCs: {len(network_info['status']['plcs'])}")
                logger.info(f"Mappings: {network_info['status']['mappings']}")
                
                for plc_id, plc_status in network_info['status']['plcs'].items():
                    logger.info(f"  {plc_id}: {plc_status['connected']} ({plc_status['name']})")
                
            except Exception as e:
                logger.error(f"Error getting network status: {e}")
    
    async def _on_data_sync(self, mapping, value):
        """Callback cuando se sincronizan datos."""
        logger.info(f"🔄 Data synced: {mapping.source_plc} -> {mapping.target_plc}: {value}")
    
    async def _on_error(self, mapping, error):
        """Callback cuando hay error en sincronización."""
        logger.error(f"❌ Sync error: {mapping.source_plc} -> {mapping.target_plc}: {error}")
    
    async def _on_connection_change(self, plc_id, connected):
        """Callback cuando cambia la conexión de un PLC."""
        status = "connected" if connected else "disconnected"
        logger.info(f"🔌 PLC {plc_id} {status}")
    
    async def _on_vfd_status_change(self, new_status, old_status):
        """Callback cuando cambia el estado del VFD."""
        logger.info(f"⚡ VFD status changed: {old_status} -> {new_status}")
    
    async def _on_vfd_fault(self, fault_code):
        """Callback cuando hay falla en el VFD."""
        logger.error(f"🚨 VFD fault: {fault_code}")


async def main():
    """Función principal."""
    logger.info("🏭 Industrial System Multi-Protocol Demo")
    logger.info("=" * 50)
    
    # Crear simulador
    simulator = IndustrialSystemSimulator()
    
    try:
        # Iniciar sistema
        await simulator.start_system()
        
        # Mantener ejecutando
        logger.info("🔄 System running. Press Ctrl+C to stop...")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Received stop signal...")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
    finally:
        # Detener sistema
        await simulator.stop_system()
        logger.info("👋 Demo completed")


if __name__ == "__main__":
    # Ejecutar demo
    asyncio.run(main()) 