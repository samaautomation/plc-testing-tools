"""
Industrial Siemens Library - Exceptions
=======================================

Excepciones personalizadas para el sistema de comunicación industrial.
"""

from typing import Optional, Any, Dict


class IndustrialException(Exception):
    """Clase base para todas las excepciones de la biblioteca industrial."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a diccionario para logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class PLCConnectionError(IndustrialException):
    """Error de conexión con el PLC."""
    
    def __init__(self, message: str, ip: Optional[str] = None, port: Optional[int] = None, **kwargs):
        details = {"ip": ip, "port": port}
        details.update(kwargs)
        super().__init__(message, "PLC_CONNECTION_ERROR", details)


class PLCCommunicationError(IndustrialException):
    """Error de comunicación con el PLC."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        details = {"operation": operation}
        details.update(kwargs)
        super().__init__(message, "PLC_COMMUNICATION_ERROR", details)


class PLCDataError(IndustrialException):
    """Error relacionado con datos del PLC."""
    
    def __init__(self, message: str, data_type: Optional[str] = None, address: Optional[str] = None, **kwargs):
        details = {"data_type": data_type, "address": address}
        details.update(kwargs)
        super().__init__(message, "PLC_DATA_ERROR", details)


class PLCConfigurationError(IndustrialException):
    """Error de configuración del PLC."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = {"config_key": config_key}
        details.update(kwargs)
        super().__init__(message, "PLC_CONFIG_ERROR", details)


class PLCTimeoutError(IndustrialException):
    """Error de timeout en operaciones del PLC."""
    
    def __init__(self, message: str, timeout_ms: Optional[int] = None, operation: Optional[str] = None, **kwargs):
        details = {"timeout_ms": timeout_ms, "operation": operation}
        details.update(kwargs)
        super().__init__(message, "PLC_TIMEOUT_ERROR", details)


class PLCProtocolError(IndustrialException):
    """Error de protocolo de comunicación."""
    
    def __init__(self, message: str, protocol: Optional[str] = None, **kwargs):
        details = {"protocol": protocol}
        details.update(kwargs)
        super().__init__(message, "PLC_PROTOCOL_ERROR", details)


class PLCAddressError(IndustrialException):
    """Error de dirección de memoria del PLC."""
    
    def __init__(self, message: str, address: Optional[str] = None, area: Optional[str] = None, **kwargs):
        details = {"address": address, "area": area}
        details.update(kwargs)
        super().__init__(message, "PLC_ADDRESS_ERROR", details)


class PLCDataTypeError(IndustrialException):
    """Error de tipo de datos."""
    
    def __init__(self, message: str, expected_type: Optional[str] = None, actual_type: Optional[str] = None, **kwargs):
        details = {"expected_type": expected_type, "actual_type": actual_type}
        details.update(kwargs)
        super().__init__(message, "PLC_DATA_TYPE_ERROR", details)


class PLCValidationError(IndustrialException):
    """Error de validación de datos."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
        details = {"field": field, "value": value}
        details.update(kwargs)
        super().__init__(message, "PLC_VALIDATION_ERROR", details)


class PLCNetworkError(IndustrialException):
    """Error de red."""
    
    def __init__(self, message: str, network_type: Optional[str] = None, **kwargs):
        details = {"network_type": network_type}
        details.update(kwargs)
        super().__init__(message, "PLC_NETWORK_ERROR", details)


class PLCDeviceError(IndustrialException):
    """Error específico del dispositivo PLC."""
    
    def __init__(self, message: str, device_type: Optional[str] = None, device_id: Optional[str] = None, **kwargs):
        details = {"device_type": device_type, "device_id": device_id}
        details.update(kwargs)
        super().__init__(message, "PLC_DEVICE_ERROR", details)


class PLCStateError(IndustrialException):
    """Error de estado del PLC."""
    
    def __init__(self, message: str, current_state: Optional[str] = None, expected_state: Optional[str] = None, **kwargs):
        details = {"current_state": current_state, "expected_state": expected_state}
        details.update(kwargs)
        super().__init__(message, "PLC_STATE_ERROR", details)


class PLCSecurityError(IndustrialException):
    """Error de seguridad."""
    
    def __init__(self, message: str, security_level: Optional[str] = None, **kwargs):
        details = {"security_level": security_level}
        details.update(kwargs)
        super().__init__(message, "PLC_SECURITY_ERROR", details)


class PLCResourceError(IndustrialException):
    """Error de recursos del PLC."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, **kwargs):
        details = {"resource_type": resource_type, "resource_id": resource_id}
        details.update(kwargs)
        super().__init__(message, "PLC_RESOURCE_ERROR", details)


# Funciones de utilidad para manejo de excepciones
def handle_plc_exception(func):
    """Decorador para manejar excepciones del PLC."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndustrialException:
            raise
        except Exception as e:
            # Convertir excepciones genéricas a excepciones específicas del PLC
            raise PLCCommunicationError(f"Error inesperado: {str(e)}", operation=func.__name__)
    return wrapper


def is_connection_error(exception: Exception) -> bool:
    """Verifica si una excepción es de tipo conexión."""
    return isinstance(exception, PLCConnectionError)


def is_timeout_error(exception: Exception) -> bool:
    """Verifica si una excepción es de tipo timeout."""
    return isinstance(exception, PLCTimeoutError)


def is_data_error(exception: Exception) -> bool:
    """Verifica si una excepción es de tipo datos."""
    return isinstance(exception, (PLCDataError, PLCDataTypeError, PLCAddressError))


def get_error_summary(exception: IndustrialException) -> Dict[str, Any]:
    """Obtiene un resumen estructurado de la excepción."""
    return {
        "type": exception.__class__.__name__,
        "message": exception.message,
        "error_code": exception.error_code,
        "timestamp": getattr(exception, 'timestamp', None),
        "details": exception.details
    }


# Constantes de códigos de error
ERROR_CODES = {
    "CONNECTION_FAILED": "PLC_CONNECTION_ERROR",
    "COMMUNICATION_FAILED": "PLC_COMMUNICATION_ERROR",
    "DATA_READ_ERROR": "PLC_DATA_ERROR",
    "DATA_WRITE_ERROR": "PLC_DATA_ERROR",
    "CONFIGURATION_INVALID": "PLC_CONFIG_ERROR",
    "TIMEOUT_EXCEEDED": "PLC_TIMEOUT_ERROR",
    "PROTOCOL_ERROR": "PLC_PROTOCOL_ERROR",
    "ADDRESS_INVALID": "PLC_ADDRESS_ERROR",
    "DATA_TYPE_MISMATCH": "PLC_DATA_TYPE_ERROR",
    "VALIDATION_FAILED": "PLC_VALIDATION_ERROR",
    "NETWORK_ERROR": "PLC_NETWORK_ERROR",
    "DEVICE_ERROR": "PLC_DEVICE_ERROR",
    "STATE_ERROR": "PLC_STATE_ERROR",
    "SECURITY_ERROR": "PLC_SECURITY_ERROR",
    "RESOURCE_ERROR": "PLC_RESOURCE_ERROR"
} 