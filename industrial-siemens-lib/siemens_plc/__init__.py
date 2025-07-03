"""
Industrial Siemens Library
==========================

Biblioteca completa para comunicación industrial con PLCs Siemens.
Diseñada para aplicaciones IoT industriales y automatización avanzada.

Autor: SAMA Engineering
Versión: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "SAMA Engineering"
__email__ = "support@sama-engineering.com"

# Core classes
from .connection import SiemensPLC, PLCConnection
from .data_types import DataTypes, DataType
from .areas import Areas, MemoryArea

# Protocol handlers
from .protocols.snap7 import Snap7Protocol
from .protocols.modbus import ModbusProtocol
from .protocols.profibus import ProfibusProtocol

# Data handlers
from .data_handlers.digital_io import DigitalIOHandler
from .data_handlers.analog_io import AnalogIOHandler
from .data_handlers.timers import TimerHandler
from .data_handlers.counters import CounterHandler
from .data_handlers.data_blocks import DataBlockHandler
from .data_handlers.marks import MarkHandler

# Communication
from .communication.plc_to_plc import PLCToPLCCommunication
from .communication.master_slave import MasterSlaveCommunication
from .communication.network import NetworkConfiguration

# Monitoring
from .monitoring.logger import IndustrialLogger
from .monitoring.diagnostics import PLCDiagnostics
from .monitoring.alerts import AlertSystem

# Utilities
from .utils.conversions import DataConverter
from .utils.validators import DataValidator
from .utils.helpers import IndustrialHelpers

# Exceptions
from .exceptions import (
    PLCConnectionError,
    PLCCommunicationError,
    PLCDataError,
    PLCConfigurationError,
    PLCTimeoutError,
    PLCProtocolError
)

# Configuration
from .config import PLCConfig, IndustrialConfig

__all__ = [
    # Core
    "SiemensPLC",
    "PLCConnection",
    "DataTypes",
    "DataType",
    "Areas",
    "MemoryArea",
    
    # Protocols
    "Snap7Protocol",
    "ModbusProtocol",
    "ProfibusProtocol",
    
    # Data Handlers
    "DigitalIOHandler",
    "AnalogIOHandler",
    "TimerHandler",
    "CounterHandler",
    "DataBlockHandler",
    "MarkHandler",
    
    # Communication
    "PLCToPLCCommunication",
    "MasterSlaveCommunication",
    "NetworkConfiguration",
    
    # Monitoring
    "IndustrialLogger",
    "PLCDiagnostics",
    "AlertSystem",
    
    # Utilities
    "DataConverter",
    "DataValidator",
    "IndustrialHelpers",
    
    # Exceptions
    "PLCConnectionError",
    "PLCCommunicationError",
    "PLCDataError",
    "PLCConfigurationError",
    "PLCTimeoutError",
    "PLCProtocolError",
    
    # Configuration
    "PLCConfig",
    "IndustrialConfig",
    
    # Version info
    "__version__",
    "__author__",
    "__email__"
]

# Convenience imports for common use cases
def create_plc(ip: str, rack: int = 0, slot: int = 1, **kwargs) -> SiemensPLC:
    """
    Factory function para crear una instancia de PLC Siemens.
    
    Args:
        ip: Dirección IP del PLC
        rack: Número de rack (default: 0)
        slot: Número de slot (default: 1)
        **kwargs: Parámetros adicionales de configuración
        
    Returns:
        Instancia configurada de SiemensPLC
    """
    return SiemensPLC(ip=ip, rack=rack, slot=slot, **kwargs)

def create_industrial_monitor(plc: SiemensPLC) -> PLCDiagnostics:
    """
    Factory function para crear un monitor industrial.
    
    Args:
        plc: Instancia del PLC
        
    Returns:
        Instancia de PLCDiagnostics configurada
    """
    return PLCDiagnostics(plc)

# Quick setup function
def setup_industrial_system(config_file: str = None) -> tuple[SiemensPLC, PLCDiagnostics, IndustrialLogger]:
    """
    Configuración rápida de un sistema industrial completo.
    
    Args:
        config_file: Archivo de configuración YAML (opcional)
        
    Returns:
        Tupla con (PLC, Diagnostics, Logger)
    """
    if config_file:
        config = IndustrialConfig.from_file(config_file)
        plc = SiemensPLC.from_config(config)
    else:
        plc = SiemensPLC()
    
    diagnostics = PLCDiagnostics(plc)
    logger = IndustrialLogger()
    
    return plc, diagnostics, logger 