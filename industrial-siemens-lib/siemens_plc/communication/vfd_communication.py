"""
VFD Communication Module
========================

Módulo para comunicación con Variadores de Frecuencia (VFD).
Soporte para protocolos Modbus, Profibus, Ethernet/IP y otros.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union, Callable
import logging
from dataclasses import dataclass
from enum import Enum

from ..protocols.base import BaseProtocol, ProtocolConfig, ProtocolType
from ..protocols.modbus import ModbusTCP, ModbusRTU
from ..protocols.profibus import ProfibusDP
from ..protocols.ethernet_ip import EthernetIPProtocol
from ..exceptions import CommunicationError


class VFDStatus(Enum):
    """Estados del VFD."""
    STOPPED = "stopped"
    RUNNING = "running"
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    FAULT = "fault"
    WARNING = "warning"
    READY = "ready"
    UNKNOWN = "unknown"


class VFDControlMode(Enum):
    """Modos de control del VFD."""
    FREQUENCY = "frequency"
    SPEED = "speed"
    TORQUE = "torque"
    POSITION = "position"


@dataclass
class VFDConfig:
    """Configuración del VFD."""
    id: str
    name: str
    protocol: BaseProtocol
    manufacturer: str = "Unknown"
    model: str = "Unknown"
    power_rating: float = 0.0  # kW
    max_frequency: float = 60.0  # Hz
    max_speed: float = 1750.0  # RPM
    control_mode: VFDControlMode = VFDControlMode.FREQUENCY
    enabled: bool = True


@dataclass
class VFDParameters:
    """Parámetros del VFD."""
    # Control
    frequency_setpoint: float = 0.0
    speed_setpoint: float = 0.0
    torque_setpoint: float = 0.0
    
    # Feedback
    output_frequency: float = 0.0
    output_speed: float = 0.0
    output_current: float = 0.0
    output_voltage: float = 0.0
    output_power: float = 0.0
    output_torque: float = 0.0
    
    # Status
    status: VFDStatus = VFDStatus.UNKNOWN
    running: bool = False
    fault_code: int = 0
    warning_code: int = 0
    
    # Temperature
    motor_temperature: float = 0.0
    drive_temperature: float = 0.0
    
    # Timestamps
    last_update: Optional[float] = None


class VFDCommunication:
    """
    Cliente de comunicación con VFD.
    
    Proporciona una interfaz unificada para comunicarse con VFDs
    de diferentes fabricantes usando varios protocolos.
    """
    
    def __init__(self, config: VFDConfig):
        self.config = config
        self.logger = logging.getLogger(f"VFD-{config.id}")
        self.protocol = config.protocol
        self.parameters = VFDParameters()
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Callbacks
        self.on_status_change: Optional[Callable] = None
        self.on_fault: Optional[Callable] = None
        self.on_parameter_change: Optional[Callable] = None
        
        # Mapeo de registros según fabricante
        self.register_map = self._get_register_map()
    
    async def connect(self) -> bool:
        """Conectar al VFD."""
        try:
            success = await self.protocol.connect()
            if success:
                self.logger.info(f"Connected to VFD {self.config.name}")
                await self._start_monitoring()
            return success
        except Exception as e:
            self.logger.error(f"Error connecting to VFD: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Desconectar del VFD."""
        try:
            await self._stop_monitoring()
            success = await self.protocol.disconnect()
            if success:
                self.logger.info(f"Disconnected from VFD {self.config.name}")
            return success
        except Exception as e:
            self.logger.error(f"Error disconnecting from VFD: {e}")
            return False
    
    async def start_drive(self) -> bool:
        """Iniciar el VFD."""
        try:
            # Enviar comando de inicio
            start_register = self.register_map.get('start_command', 0)
            success = await self._write_register(start_register, 1)
            
            if success:
                self.logger.info(f"Started VFD {self.config.name}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error starting VFD: {e}")
            return False
    
    async def stop_drive(self) -> bool:
        """Detener el VFD."""
        try:
            # Enviar comando de parada
            stop_register = self.register_map.get('stop_command', 0)
            success = await self._write_register(stop_register, 1)
            
            if success:
                self.logger.info(f"Stopped VFD {self.config.name}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error stopping VFD: {e}")
            return False
    
    async def set_frequency(self, frequency: float) -> bool:
        """Establecer frecuencia de salida."""
        try:
            # Validar frecuencia
            if frequency < 0 or frequency > self.config.max_frequency:
                raise ValueError(f"Frequency must be between 0 and {self.config.max_frequency} Hz")
            
            # Escribir frecuencia
            freq_register = self.register_map.get('frequency_setpoint', 0)
            success = await self._write_register(freq_register, frequency)
            
            if success:
                self.parameters.frequency_setpoint = frequency
                self.logger.debug(f"Set frequency to {frequency} Hz")
            
            return success
        except Exception as e:
            self.logger.error(f"Error setting frequency: {e}")
            return False
    
    async def set_speed(self, speed: float) -> bool:
        """Establecer velocidad de salida."""
        try:
            # Validar velocidad
            if speed < 0 or speed > self.config.max_speed:
                raise ValueError(f"Speed must be between 0 and {self.config.max_speed} RPM")
            
            # Escribir velocidad
            speed_register = self.register_map.get('speed_setpoint', 0)
            success = await self._write_register(speed_register, speed)
            
            if success:
                self.parameters.speed_setpoint = speed
                self.logger.debug(f"Set speed to {speed} RPM")
            
            return success
        except Exception as e:
            self.logger.error(f"Error setting speed: {e}")
            return False
    
    async def set_torque(self, torque: float) -> bool:
        """Establecer par de salida."""
        try:
            # Escribir par
            torque_register = self.register_map.get('torque_setpoint', 0)
            success = await self._write_register(torque_register, torque)
            
            if success:
                self.parameters.torque_setpoint = torque
                self.logger.debug(f"Set torque to {torque} Nm")
            
            return success
        except Exception as e:
            self.logger.error(f"Error setting torque: {e}")
            return False
    
    async def read_parameters(self) -> VFDParameters:
        """Leer todos los parámetros del VFD."""
        try:
            # Leer parámetros en paralelo
            tasks = [
                self._read_output_frequency(),
                self._read_output_speed(),
                self._read_output_current(),
                self._read_output_voltage(),
                self._read_output_power(),
                self._read_status(),
                self._read_temperatures()
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            self.parameters.last_update = time.time()
            return self.parameters
            
        except Exception as e:
            self.logger.error(f"Error reading parameters: {e}")
            return self.parameters
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado completo del VFD."""
        try:
            # Leer parámetros actuales
            await self.read_parameters()
            
            # Obtener estado del protocolo
            protocol_status = await self.protocol.get_status()
            
            return {
                'id': self.config.id,
                'name': self.config.name,
                'manufacturer': self.config.manufacturer,
                'model': self.config.model,
                'connected': protocol_status.is_connected,
                'parameters': self.parameters,
                'protocol_status': protocol_status
            }
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {}
    
    async def reset_fault(self) -> bool:
        """Resetear falla del VFD."""
        try:
            reset_register = self.register_map.get('fault_reset', 0)
            success = await self._write_register(reset_register, 1)
            
            if success:
                self.logger.info(f"Reset fault for VFD {self.config.name}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error resetting fault: {e}")
            return False
    
    async def _start_monitoring(self) -> None:
        """Iniciar monitoreo continuo."""
        if self.monitoring_task:
            return
        
        self.running = True
        
        async def monitoring_loop():
            while self.running:
                try:
                    # Leer parámetros
                    old_status = self.parameters.status
                    old_running = self.parameters.running
                    
                    await self.read_parameters()
                    
                    # Verificar cambios de estado
                    if self.parameters.status != old_status:
                        if self.on_status_change:
                            await self.on_status_change(self.parameters.status, old_status)
                    
                    if self.parameters.running != old_running:
                        if self.on_status_change:
                            await self.on_status_change("running", self.parameters.running)
                    
                    # Verificar fallas
                    if self.parameters.fault_code != 0:
                        if self.on_fault:
                            await self.on_fault(self.parameters.fault_code)
                    
                    # Esperar intervalo
                    await asyncio.sleep(1)  # 1 segundo
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(5)
        
        self.monitoring_task = asyncio.create_task(monitoring_loop())
        self.logger.info("Started VFD monitoring")
    
    async def _stop_monitoring(self) -> None:
        """Detener monitoreo continuo."""
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        self.logger.info("Stopped VFD monitoring")
    
    async def _read_output_frequency(self) -> None:
        """Leer frecuencia de salida."""
        try:
            freq_register = self.register_map.get('output_frequency', 0)
            if freq_register:
                value = await self._read_register(freq_register, 'float32')
                if value is not None:
                    self.parameters.output_frequency = value
        except Exception as e:
            self.logger.debug(f"Error reading output frequency: {e}")
    
    async def _read_output_speed(self) -> None:
        """Leer velocidad de salida."""
        try:
            speed_register = self.register_map.get('output_speed', 0)
            if speed_register:
                value = await self._read_register(speed_register, 'float32')
                if value is not None:
                    self.parameters.output_speed = value
        except Exception as e:
            self.logger.debug(f"Error reading output speed: {e}")
    
    async def _read_output_current(self) -> None:
        """Leer corriente de salida."""
        try:
            current_register = self.register_map.get('output_current', 0)
            if current_register:
                value = await self._read_register(current_register, 'float32')
                if value is not None:
                    self.parameters.output_current = value
        except Exception as e:
            self.logger.debug(f"Error reading output current: {e}")
    
    async def _read_output_voltage(self) -> None:
        """Leer voltaje de salida."""
        try:
            voltage_register = self.register_map.get('output_voltage', 0)
            if voltage_register:
                value = await self._read_register(voltage_register, 'float32')
                if value is not None:
                    self.parameters.output_voltage = value
        except Exception as e:
            self.logger.debug(f"Error reading output voltage: {e}")
    
    async def _read_output_power(self) -> None:
        """Leer potencia de salida."""
        try:
            power_register = self.register_map.get('output_power', 0)
            if power_register:
                value = await self._read_register(power_register, 'float32')
                if value is not None:
                    self.parameters.output_power = value
        except Exception as e:
            self.logger.debug(f"Error reading output power: {e}")
    
    async def _read_status(self) -> None:
        """Leer estado del VFD."""
        try:
            status_register = self.register_map.get('status', 0)
            if status_register:
                value = await self._read_register(status_register, 'uint16')
                if value is not None:
                    self.parameters.status = self._decode_status(value)
                    self.parameters.running = value & 0x01 != 0
        except Exception as e:
            self.logger.debug(f"Error reading status: {e}")
    
    async def _read_temperatures(self) -> None:
        """Leer temperaturas."""
        try:
            # Temperatura del motor
            motor_temp_register = self.register_map.get('motor_temperature', 0)
            if motor_temp_register:
                value = await self._read_register(motor_temp_register, 'float32')
                if value is not None:
                    self.parameters.motor_temperature = value
            
            # Temperatura del drive
            drive_temp_register = self.register_map.get('drive_temperature', 0)
            if drive_temp_register:
                value = await self._read_register(drive_temp_register, 'float32')
                if value is not None:
                    self.parameters.drive_temperature = value
        except Exception as e:
            self.logger.debug(f"Error reading temperatures: {e}")
    
    async def _read_register(self, address: int, data_type: str) -> Optional[float]:
        """Leer registro del VFD."""
        try:
            from ..protocols.base import ReadRequest
            
            request = ReadRequest(
                address=address,
                count=1,
                data_type=data_type
            )
            
            data = await self.protocol.read_data(request)
            return data[0] if data else None
            
        except Exception as e:
            self.logger.debug(f"Error reading register {address}: {e}")
            return None
    
    async def _write_register(self, address: int, value: float) -> bool:
        """Escribir registro del VFD."""
        try:
            from ..protocols.base import WriteRequest
            
            request = WriteRequest(
                address=address,
                value=value,
                data_type='float32'
            )
            
            return await self.protocol.write_data(request)
            
        except Exception as e:
            self.logger.debug(f"Error writing register {address}: {e}")
            return False
    
    def _get_register_map(self) -> Dict[str, int]:
        """Obtener mapa de registros según fabricante."""
        # Mapa genérico - puede ser sobrescrito según fabricante
        return {
            'start_command': 0x0001,
            'stop_command': 0x0002,
            'frequency_setpoint': 0x2000,
            'speed_setpoint': 0x2001,
            'torque_setpoint': 0x2002,
            'output_frequency': 0x2100,
            'output_speed': 0x2101,
            'output_current': 0x2102,
            'output_voltage': 0x2103,
            'output_power': 0x2104,
            'output_torque': 0x2105,
            'status': 0x2200,
            'fault_code': 0x2201,
            'warning_code': 0x2202,
            'motor_temperature': 0x2300,
            'drive_temperature': 0x2301,
            'fault_reset': 0x2400
        }
    
    def _decode_status(self, status_value: int) -> VFDStatus:
        """Decodificar valor de estado."""
        if status_value & 0x8000:  # Bit de falla
            return VFDStatus.FAULT
        elif status_value & 0x4000:  # Bit de advertencia
            return VFDStatus.WARNING
        elif status_value & 0x0001:  # Bit de ejecución
            return VFDStatus.RUNNING
        elif status_value & 0x0002:  # Bit de aceleración
            return VFDStatus.ACCELERATING
        elif status_value & 0x0004:  # Bit de desaceleración
            return VFDStatus.DECELERATING
        elif status_value & 0x0008:  # Bit de listo
            return VFDStatus.READY
        else:
            return VFDStatus.STOPPED


class VFDProtocol:
    """Factory para crear clientes VFD según protocolo."""
    
    @staticmethod
    async def create_vfd(protocol_type: str, config: Dict[str, Any]) -> VFDCommunication:
        """Crear cliente VFD según protocolo."""
        # Crear configuración de protocolo
        protocol_config = ProtocolConfig(
            protocol_type=ProtocolType(protocol_type),
            host=config['host'],
            port=config.get('port', 502),
            timeout=config.get('timeout', 5000),
            retry_count=config.get('retry_count', 3),
            debug=config.get('debug', False)
        )
        
        # Crear protocolo
        if protocol_type == 'modbus_tcp':
            protocol = ModbusTCP(config['host'], config.get('port', 502))
        elif protocol_type == 'modbus_rtu':
            protocol = ModbusRTU(config['host'], config.get('baudrate', 9600))
        elif protocol_type == 'profibus_dp':
            protocol = ProfibusDP(config['host'], config.get('slave_address', 1))
        elif protocol_type == 'ethernet_ip':
            protocol = EthernetIPProtocol(protocol_config)
        else:
            raise ValueError(f"Unsupported VFD protocol: {protocol_type}")
        
        # Crear configuración del VFD
        vfd_config = VFDConfig(
            id=config['id'],
            name=config.get('name', config['id']),
            protocol=protocol,
            manufacturer=config.get('manufacturer', 'Unknown'),
            model=config.get('model', 'Unknown'),
            power_rating=config.get('power_rating', 0.0),
            max_frequency=config.get('max_frequency', 60.0),
            max_speed=config.get('max_speed', 1750.0),
            control_mode=VFDControlMode(config.get('control_mode', 'frequency')),
            enabled=config.get('enabled', True)
        )
        
        return VFDCommunication(vfd_config) 