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
from .connection import SiemensPLCConnection
from .data_types import DataTypes, DataType
from .areas import Areas, MemoryArea

# Exceptions
from .exceptions import (
    PLCConnectionError,
    PLCCommunicationError,
    PLCDataError,
    PLCConfigurationError,
    PLCTimeoutError,
    PLCProtocolError
)

__all__ = [
    # Core
    "SiemensPLCConnection",
    "DataTypes",
    "DataType",
    "Areas",
    "MemoryArea",
    
    # Exceptions
    "PLCConnectionError",
    "PLCCommunicationError",
    "PLCDataError",
    "PLCConfigurationError",
    "PLCTimeoutError",
    "PLCProtocolError",
    
    # Version info
    "__version__",
    "__author__",
    "__email__"
]

# Convenience imports for common use cases
def create_plc(ip: str, rack: int = 0, slot: int = 1, **kwargs) -> SiemensPLCConnection:
    """
    Factory function para crear una instancia de PLC Siemens.
    
    Args:
        ip: Dirección IP del PLC
        rack: Número de rack (default: 0)
        slot: Número de slot (default: 1)
        **kwargs: Parámetros adicionales de configuración
        
    Returns:
        Instancia configurada de SiemensPLCConnection
    """
    return SiemensPLCConnection(ip=ip, rack=rack, slot=slot, **kwargs) 