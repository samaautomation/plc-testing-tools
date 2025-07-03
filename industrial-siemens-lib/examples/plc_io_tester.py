#!/usr/bin/env python3
"""
PLC I/O Tester para Jetson Nano - Siemens PLC
==============================================

Este script permite probar entradas y salidas de un PLC Siemens
desde un Jetson Nano con interfaz web y monitoreo en tiempo real.

Autor: SAMA Engineering
Versión: 1.0
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
from dataclasses import dataclass, asdict
import signal
import sys

# Importar nuestra librería industrial
from siemens_plc.connection import SiemensPLCConnection
from siemens_plc.exceptions import PLCConnectionError, PLCReadError, PLCWriteError
from siemens_plc.areas import MemoryArea

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('plc_io_tester.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class IOTestConfig:
    """Configuración para pruebas de I/O"""
    plc_ip: str = "192.168.1.100"
    plc_rack: int = 0
    plc_slot: int = 1
    test_interval: float = 1.0
    auto_reconnect: bool = True
    heartbeat_interval: float = 5.0

@dataclass
class IOTestResult:
    """Resultado de una prueba de I/O"""
    timestamp: str
    test_type: str
    address: str
    value: Any
    success: bool
    error_message: Optional[str] = None
    response_time: float = 0.0

class PLCIOTester:
    """Clase principal para pruebas de I/O del PLC"""
    
    def __init__(self, config: IOTestConfig):
        self.config = config
        self.connection = None
        self.is_connected = False
        self.test_results: List[IOTestResult] = []
        self.monitoring = False
        self.monitor_thread = None
        
        # Configuración de áreas de memoria para pruebas
        self.test_areas = {
            'digital_inputs': {
                'E0.0': 'Entrada Digital 0',
                'E0.1': 'Entrada Digital 1', 
                'E0.2': 'Entrada Digital 2',
                'E0.3': 'Entrada Digital 3',
                'E0.4': 'Entrada Digital 4',
                'E0.5': 'Entrada Digital 5',
                'E0.6': 'Entrada Digital 6',
                'E0.7': 'Entrada Digital 7'
            },
            'digital_outputs': {
                'A0.0': 'Salida Digital 0',
                'A0.1': 'Salida Digital 1',
                'A0.2': 'Salida Digital 2', 
                'A0.3': 'Salida Digital 3',
                'A0.4': 'Salida Digital 4',
                'A0.5': 'Salida Digital 5',
                'A0.6': 'Salida Digital 6',
                'A0.7': 'Salida Digital 7'
            },
            'analog_inputs': {
                'IW64': 'Entrada Analógica 0',
                'IW66': 'Entrada Analógica 1',
                'IW68': 'Entrada Analógica 2',
                'IW70': 'Entrada Analógica 3'
            },
            'analog_outputs': {
                'QW80': 'Salida Analógica 0',
                'QW82': 'Salida Analógica 1',
                'QW84': 'Salida Analógica 2',
                'QW86': 'Salida Analógica 3'
            },
            'marks': {
                'M0.0': 'Marca 0',
                'M0.1': 'Marca 1',
                'M0.2': 'Marca 2',
                'M0.3': 'Marca 3',
                'M0.4': 'Marca 4',
                'M0.5': 'Marca 5',
                'M0.6': 'Marca 6',
                'M0.7': 'Marca 7'
            },
            'data_blocks': {
                'DB1.DBW0': 'DB1 Word 0',
                'DB1.DBW2': 'DB1 Word 2',
                'DB1.DBW4': 'DB1 Word 4',
                'DB1.DBW6': 'DB1 Word 6'
            }
        }
        
        # Configurar signal handlers para cierre limpio
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejar señales de cierre"""
        logger.info(f"Recibida señal {signum}, cerrando conexión...")
        self.disconnect()
        sys.exit(0)
    
    def connect(self) -> bool:
        """Conectar al PLC"""
        try:
            logger.info(f"Conectando al PLC en {self.config.plc_ip}...")
            
            self.connection = SiemensPLCConnection(
                ip_address=self.config.plc_ip,
                rack=self.config.plc_rack,
                slot=self.config.plc_slot,
                auto_reconnect=self.config.auto_reconnect,
                heartbeat_interval=self.config.heartbeat_interval
            )
            
            self.connection.connect()
            self.is_connected = True
            
            logger.info("✅ Conexión establecida exitosamente")
            return True
            
        except PLCConnectionError as e:
            logger.error(f"❌ Error de conexión: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Desconectar del PLC"""
        if self.connection:
            try:
                self.connection.disconnect()
                logger.info("Conexión cerrada")
            except Exception as e:
                logger.error(f"Error al cerrar conexión: {e}")
            finally:
                self.is_connected = False
                self.connection = None
    
    def read_digital_inputs(self) -> Dict[str, Any]:
        """Leer todas las entradas digitales"""
        results = {}
        
        if not self.is_connected:
            logger.error("No hay conexión al PLC")
            return results
        
        for address, description in self.test_areas['digital_inputs'].items():
            try:
                start_time = time.time()
                value = self.connection.read_bit(address)
                response_time = time.time() - start_time
                
                results[address] = {
                    'value': bool(value),
                    'description': description,
                    'response_time': response_time,
                    'success': True
                }
                
                # Registrar resultado
                self.test_results.append(IOTestResult(
                    timestamp=datetime.now().isoformat(),
                    test_type='read_digital_input',
                    address=address,
                    value=bool(value),
                    success=True,
                    response_time=response_time
                ))
                
            except Exception as e:
                logger.error(f"Error leyendo {address}: {e}")
                results[address] = {
                    'value': None,
                    'description': description,
                    'error': str(e),
                    'success': False
                }
                
                self.test_results.append(IOTestResult(
                    timestamp=datetime.now().isoformat(),
                    test_type='read_digital_input',
                    address=address,
                    value=None,
                    success=False,
                    error_message=str(e)
                ))
        
        return results
    
    def read_analog_inputs(self) -> Dict[str, Any]:
        """Leer todas las entradas analógicas"""
        results = {}
        
        if not self.is_connected:
            logger.error("No hay conexión al PLC")
            return results
        
        for address, description in self.test_areas['analog_inputs'].items():
            try:
                start_time = time.time()
                value = self.connection.read_word(address)
                response_time = time.time() - start_time
                
                results[address] = {
                    'value': value,
                    'description': description,
                    'response_time': response_time,
                    'success': True
                }
                
                self.test_results.append(IOTestResult(
                    timestamp=datetime.now().isoformat(),
                    test_type='read_analog_input',
                    address=address,
                    value=value,
                    success=True,
                    response_time=response_time
                ))
                
            except Exception as e:
                logger.error(f"Error leyendo {address}: {e}")
                results[address] = {
                    'value': None,
                    'description': description,
                    'error': str(e),
                    'success': False
                }
                
                self.test_results.append(IOTestResult(
                    timestamp=datetime.now().isoformat(),
                    test_type='read_analog_input',
                    address=address,
                    value=None,
                    success=False,
                    error_message=str(e)
                ))
        
        return results
    
    def write_digital_output(self, address: str, value: bool) -> bool:
        """Escribir una salida digital"""
        if not self.is_connected:
            logger.error("No hay conexión al PLC")
            return False
        
        try:
            start_time = time.time()
            self.connection.write_bit(address, value)
            response_time = time.time() - start_time
            
            logger.info(f"✅ Escrito {address} = {value}")
            
            self.test_results.append(IOTestResult(
                timestamp=datetime.now().isoformat(),
                test_type='write_digital_output',
                address=address,
                value=value,
                success=True,
                response_time=response_time
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error escribiendo {address}: {e}")
            
            self.test_results.append(IOTestResult(
                timestamp=datetime.now().isoformat(),
                test_type='write_digital_output',
                address=address,
                value=value,
                success=False,
                error_message=str(e)
            ))
            
            return False
    
    def write_analog_output(self, address: str, value: int) -> bool:
        """Escribir una salida analógica"""
        if not self.is_connected:
            logger.error("No hay conexión al PLC")
            return False
        
        try:
            start_time = time.time()
            self.connection.write_word(address, value)
            response_time = time.time() - start_time
            
            logger.info(f"✅ Escrito {address} = {value}")
            
            self.test_results.append(IOTestResult(
                timestamp=datetime.now().isoformat(),
                test_type='write_analog_output',
                address=address,
                value=value,
                success=True,
                response_time=response_time
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error escribiendo {address}: {e}")
            
            self.test_results.append(IOTestResult(
                timestamp=datetime.now().isoformat(),
                test_type='write_analog_output',
                address=address,
                value=value,
                success=False,
                error_message=str(e)
            ))
            
            return False
    
    def read_marks(self) -> Dict[str, Any]:
        """Leer marcas (memoria interna)"""
        results = {}
        
        if not self.is_connected:
            logger.error("No hay conexión al PLC")
            return results
        
        for address, description in self.test_areas['marks'].items():
            try:
                start_time = time.time()
                value = self.connection.read_bit(address)
                response_time = time.time() - start_time
                
                results[address] = {
                    'value': bool(value),
                    'description': description,
                    'response_time': response_time,
                    'success': True
                }
                
            except Exception as e:
                logger.error(f"Error leyendo {address}: {e}")
                results[address] = {
                    'value': None,
                    'description': description,
                    'error': str(e),
                    'success': False
                }
        
        return results
    
    def write_mark(self, address: str, value: bool) -> bool:
        """Escribir una marca"""
        if not self.is_connected:
            logger.error("No hay conexión al PLC")
            return False
        
        try:
            self.connection.write_bit(address, value)
            logger.info(f"✅ Escrito {address} = {value}")
            return True
        except Exception as e:
            logger.error(f"❌ Error escribiendo {address}: {e}")
            return False
    
    def read_data_blocks(self) -> Dict[str, Any]:
        """Leer bloques de datos"""
        results = {}
        
        if not self.is_connected:
            logger.error("No hay conexión al PLC")
            return results
        
        for address, description in self.test_areas['data_blocks'].items():
            try:
                start_time = time.time()
                value = self.connection.read_word(address)
                response_time = time.time() - start_time
                
                results[address] = {
                    'value': value,
                    'description': description,
                    'response_time': response_time,
                    'success': True
                }
                
            except Exception as e:
                logger.error(f"Error leyendo {address}: {e}")
                results[address] = {
                    'value': None,
                    'description': description,
                    'error': str(e),
                    'success': False
                }
        
        return results
    
    def write_data_block(self, address: str, value: int) -> bool:
        """Escribir un bloque de datos"""
        if not self.is_connected:
            logger.error("No hay conexión al PLC")
            return False
        
        try:
            self.connection.write_word(address, value)
            logger.info(f"✅ Escrito {address} = {value}")
            return True
        except Exception as e:
            logger.error(f"❌ Error escribiendo {address}: {e}")
            return False
    
    def start_monitoring(self):
        """Iniciar monitoreo en tiempo real"""
        if self.monitoring:
            logger.warning("El monitoreo ya está activo")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🔄 Monitoreo iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("⏹️ Monitoreo detenido")
    
    def _monitor_loop(self):
        """Loop de monitoreo en tiempo real"""
        while self.monitoring:
            try:
                if self.is_connected:
                    # Leer entradas
                    digital_inputs = self.read_digital_inputs()
                    analog_inputs = self.read_analog_inputs()
                    marks = self.read_marks()
                    
                    # Mostrar estado
                    print("\n" + "="*60)
                    print(f"📊 MONITOREO PLC - {datetime.now().strftime('%H:%M:%S')}")
                    print("="*60)
                    
                    # Entradas digitales
                    print("\n🔌 ENTRADAS DIGITALES:")
                    for addr, data in digital_inputs.items():
                        status = "🟢 ON" if data.get('value') else "🔴 OFF"
                        print(f"  {addr}: {status} ({data.get('description', '')})")
                    
                    # Entradas analógicas
                    print("\n📊 ENTRADAS ANALÓGICAS:")
                    for addr, data in analog_inputs.items():
                        if data.get('success'):
                            print(f"  {addr}: {data.get('value')} ({data.get('description', '')})")
                        else:
                            print(f"  {addr}: ❌ ERROR")
                    
                    # Marcas
                    print("\n🏷️ MARCAS:")
                    for addr, data in marks.items():
                        status = "🟢 ON" if data.get('value') else "🔴 OFF"
                        print(f"  {addr}: {status} ({data.get('description', '')})")
                    
                    print("\n" + "="*60)
                
                time.sleep(self.config.test_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                time.sleep(self.config.test_interval)
    
    def run_quick_test(self):
        """Ejecutar prueba rápida de todas las funciones"""
        logger.info("🚀 Iniciando prueba rápida...")
        
        if not self.connect():
            logger.error("No se pudo conectar al PLC")
            return False
        
        try:
            # Leer entradas
            logger.info("📖 Leyendo entradas...")
            digital_inputs = self.read_digital_inputs()
            analog_inputs = self.read_analog_inputs()
            marks = self.read_marks()
            data_blocks = self.read_data_blocks()
            
            # Mostrar resultados
            print("\n" + "="*50)
            print("📊 RESULTADOS DE PRUEBA RÁPIDA")
            print("="*50)
            
            print(f"\n🔌 Entradas Digitales: {len([d for d in digital_inputs.values() if d.get('success')])}/{len(digital_inputs)} exitosas")
            print(f"📊 Entradas Analógicas: {len([a for a in analog_inputs.values() if a.get('success')])}/{len(analog_inputs)} exitosas")
            print(f"🏷️ Marcas: {len([m for m in marks.values() if m.get('success')])}/{len(marks)} exitosas")
            print(f"💾 Bloques de Datos: {len([db for db in data_blocks.values() if db.get('success')])}/{len(data_blocks)} exitosos")
            
            # Probar escritura
            logger.info("✍️ Probando escritura...")
            test_output = self.write_digital_output('A0.0', True)
            time.sleep(0.5)
            test_output = self.write_digital_output('A0.0', False)
            
            if test_output:
                print("✅ Escritura de salidas: EXITOSA")
            else:
                print("❌ Escritura de salidas: FALLIDA")
            
            print("\n" + "="*50)
            return True
            
        except Exception as e:
            logger.error(f"Error en prueba rápida: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del sistema"""
        return {
            'connected': self.is_connected,
            'monitoring': self.monitoring,
            'plc_ip': self.config.plc_ip,
            'test_interval': self.config.test_interval,
            'total_tests': len(self.test_results),
            'successful_tests': len([r for r in self.test_results if r.success]),
            'failed_tests': len([r for r in self.test_results if not r.success]),
            'last_test': self.test_results[-1].timestamp if self.test_results else None
        }
    
    def export_results(self, filename: str = None):
        """Exportar resultados a JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"plc_test_results_{timestamp}.json"
        
        data = {
            'config': asdict(self.config),
            'status': self.get_status(),
            'results': [asdict(result) for result in self.test_results]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Resultados exportados a {filename}")

def main():
    """Función principal"""
    print("🔧 PLC I/O Tester para Jetson Nano - Siemens PLC")
    print("=" * 50)
    
    # Configuración por defecto
    config = IOTestConfig()
    
    # Crear tester
    tester = PLCIOTester(config)
    
    try:
        # Ejecutar prueba rápida
        success = tester.run_quick_test()
        
        if success:
            print("\n🎉 ¡Prueba completada exitosamente!")
            
            # Preguntar si iniciar monitoreo
            response = input("\n¿Iniciar monitoreo en tiempo real? (s/n): ").lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                print("\n🔄 Iniciando monitoreo... (Ctrl+C para detener)")
                tester.connect()
                tester.start_monitoring()
                
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n⏹️ Deteniendo monitoreo...")
                    tester.stop_monitoring()
                    tester.disconnect()
        else:
            print("\n❌ La prueba falló. Revisa la conexión al PLC.")
    
    except KeyboardInterrupt:
        print("\n👋 Cerrando aplicación...")
    except Exception as e:
        logger.error(f"Error en aplicación principal: {e}")
    finally:
        tester.disconnect()
        print("✅ Aplicación cerrada")

if __name__ == "__main__":
    main() 