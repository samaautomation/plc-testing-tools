#!/usr/bin/env python3
"""
Ejemplo Completo de Monitoreo Industrial
========================================

Este ejemplo demuestra el uso completo del esqueleto industrial para:
- Conexión robusta al PLC Siemens
- Monitoreo de entradas/salidas digitales y analógicas
- Manejo de errores y reconexión automática
- Logging y diagnósticos
- Comunicación en tiempo real

Autor: SAMA Engineering
"""

import time
import signal
import sys
from typing import Dict, Any
from datetime import datetime

# Importar el esqueleto industrial
from siemens_plc import (
    SiemensPLC, 
    DataTypes, 
    Areas,
    PLCConnectionError,
    PLCCommunicationError
)
from snap7 import Area


class IndustrialMonitor:
    """Monitor industrial completo para PLC Siemens."""
    
    def __init__(self, plc_ip: str = "192.168.1.5"):
        self.plc_ip = plc_ip
        self.running = False
        
        # Configurar PLC con reconexión automática
        self.plc = SiemensPLC(
            ip=plc_ip,
            rack=0,
            slot=1,
            timeout=5000,
            retry_attempts=3,
            retry_delay=1000,
            heartbeat_interval=5000,
            auto_reconnect=True,
            debug=True
        )
        
        # Configurar callbacks
        self._setup_callbacks()
        
        # Estado del sistema
        self.system_status = {
            "connected": False,
            "last_update": None,
            "error_count": 0,
            "uptime": 0
        }
        
        # Configuración de monitoreo
        self.monitoring_config = {
            "digital_inputs": ["I0.0", "I0.1", "I0.2", "I0.3"],
            "digital_outputs": ["Q0.0", "Q0.1", "Q0.2", "Q0.3"],
            "analog_inputs": ["IW96", "IW98"],
            "analog_outputs": ["QW96", "QW98"],
            "marks": ["M0.0", "M0.1", "M0.2"],
            "data_blocks": ["DB1.DBW0", "DB1.DBW2", "DB1.DBW4"]
        }
        
        # Datos en tiempo real
        self.real_time_data = {
            "digital_inputs": {},
            "digital_outputs": {},
            "analog_inputs": {},
            "analog_outputs": {},
            "marks": {},
            "data_blocks": {}
        }
        
        print("🏭 Monitor Industrial Siemens Inicializado")
        print("=" * 50)
    
    def _setup_callbacks(self):
        """Configura los callbacks del PLC."""
        self.plc.connection.add_connection_callback(self._on_connection_change)
        self.plc.connection.add_error_callback(self._on_error)
        self.plc.connection.add_heartbeat_callback(self._on_heartbeat)
    
    def start(self):
        """Inicia el monitor industrial."""
        print("🚀 Iniciando monitor industrial...")
        
        # Configurar señal de interrupción
        signal.signal(signal.SIGINT, self._signal_handler)
        
        try:
            # Conectar al PLC
            if self.plc.connect():
                print("✅ Conectado exitosamente al PLC")
                self.running = True
                self._main_loop()
            else:
                print("❌ No se pudo conectar al PLC")
                
        except Exception as e:
            print(f"❌ Error iniciando monitor: {e}")
            self.stop()
    
    def stop(self):
        """Detiene el monitor industrial."""
        print("\n🛑 Deteniendo monitor industrial...")
        self.running = False
        self.plc.disconnect()
        print("✅ Monitor detenido")
    
    def _main_loop(self):
        """Loop principal de monitoreo."""
        print("📊 Iniciando monitoreo en tiempo real...")
        print("📍 Presiona Ctrl+C para detener")
        print("-" * 50)
        
        while self.running:
            try:
                if self.plc.is_connected():
                    # Actualizar datos en tiempo real
                    self._update_real_time_data()
                    
                    # Mostrar estado del sistema
                    self._display_system_status()
                    
                    # Mostrar datos críticos
                    self._display_critical_data()
                    
                    # Actualizar estado
                    self.system_status["last_update"] = datetime.now()
                    self.system_status["uptime"] = time.time() - self.plc.connection.connection_time
                    
                else:
                    print("⚠️ PLC desconectado, esperando reconexión...")
                
                # Pausa entre actualizaciones
                time.sleep(1.0)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error en loop principal: {e}")
                self.system_status["error_count"] += 1
    
    def _update_real_time_data(self):
        """Actualiza los datos en tiempo real."""
        try:
            # Leer entradas digitales
            for address in self.monitoring_config["digital_inputs"]:
                value = self._read_digital_input(address)
                self.real_time_data["digital_inputs"][address] = value
            
            # Leer salidas digitales
            for address in self.monitoring_config["digital_outputs"]:
                value = self._read_digital_output(address)
                self.real_time_data["digital_outputs"][address] = value
            
            # Leer entradas analógicas
            for address in self.monitoring_config["analog_inputs"]:
                value = self._read_analog_input(address)
                self.real_time_data["analog_inputs"][address] = value
            
            # Leer salidas analógicas
            for address in self.monitoring_config["analog_outputs"]:
                value = self._read_analog_output(address)
                self.real_time_data["analog_outputs"][address] = value
            
            # Leer marcas
            for address in self.monitoring_config["marks"]:
                value = self._read_mark(address)
                self.real_time_data["marks"][address] = value
            
            # Leer bloques de datos
            for address in self.monitoring_config["data_blocks"]:
                value = self._read_data_block(address)
                self.real_time_data["data_blocks"][address] = value
                
        except Exception as e:
            print(f"⚠️ Error actualizando datos: {e}")
    
    def _read_digital_input(self, address: str) -> bool:
        """Lee una entrada digital."""
        try:
            # Parsear dirección (ej: "I0.0" -> byte=0, bit=0)
            parts = address.split('.')
            byte = int(parts[0][1:])
            bit = int(parts[1])
            
            # Leer byte completo
            data = self.plc.read_area(Area.PE, 0, byte, 1)
            return bool(data[0] & (1 << bit))
            
        except Exception as e:
            print(f"⚠️ Error leyendo entrada digital {address}: {e}")
            return False
    
    def _read_digital_output(self, address: str) -> bool:
        """Lee una salida digital."""
        try:
            parts = address.split('.')
            byte = int(parts[0][1:])
            bit = int(parts[1])
            
            data = self.plc.read_area(Area.PA, 0, byte, 1)
            return bool(data[0] & (1 << bit))
            
        except Exception as e:
            print(f"⚠️ Error leyendo salida digital {address}: {e}")
            return False
    
    def _read_analog_input(self, address: str) -> int:
        """Lee una entrada analógica."""
        try:
            # Parsear dirección (ej: "IW96" -> byte=96)
            byte = int(address[2:])
            
            data = self.plc.read_area(Area.PE, 0, byte, 2)
            return int.from_bytes(data, byteorder='big', signed=True)
            
        except Exception as e:
            print(f"⚠️ Error leyendo entrada analógica {address}: {e}")
            return 0
    
    def _read_analog_output(self, address: str) -> int:
        """Lee una salida analógica."""
        try:
            byte = int(address[2:])
            
            data = self.plc.read_area(Area.PA, 0, byte, 2)
            return int.from_bytes(data, byteorder='big', signed=True)
            
        except Exception as e:
            print(f"⚠️ Error leyendo salida analógica {address}: {e}")
            return 0
    
    def _read_mark(self, address: str) -> bool:
        """Lee una marca."""
        try:
            parts = address.split('.')
            byte = int(parts[0][1:])
            bit = int(parts[1])
            
            data = self.plc.read_area(Area.MK, 0, byte, 1)
            return bool(data[0] & (1 << bit))
            
        except Exception as e:
            print(f"⚠️ Error leyendo marca {address}: {e}")
            return False
    
    def _read_data_block(self, address: str) -> int:
        """Lee un bloque de datos."""
        try:
            # Parsear dirección (ej: "DB1.DBW0" -> db=1, byte=0)
            parts = address.split('.')
            db_number = int(parts[0][2:])
            byte = int(parts[1][4:])
            
            data = self.plc.read_area(Area.DB, db_number, byte, 2)
            return int.from_bytes(data, byteorder='big', signed=True)
            
        except Exception as e:
            print(f"⚠️ Error leyendo bloque de datos {address}: {e}")
            return 0
    
    def _display_system_status(self):
        """Muestra el estado del sistema."""
        info = self.plc.get_connection_info()
        
        print(f"\n📊 Estado del Sistema - {datetime.now().strftime('%H:%M:%S')}")
        print(f"🔌 PLC: {info['ip']} | Estado: {info['state']}")
        print(f"⏱️  Uptime: {info['uptime']:.1f}s | Errores: {info['error_count']}")
        print(f"💓 Último heartbeat: {info['last_heartbeat']:.1f}s atrás")
    
    def _display_critical_data(self):
        """Muestra datos críticos del sistema."""
        print("\n🎛️  Datos Críticos:")
        
        # Entradas digitales
        print("📥 Entradas Digitales:")
        for address, value in self.real_time_data["digital_inputs"].items():
            status = "🟢 ON" if value else "🔴 OFF"
            print(f"   {address}: {status}")
        
        # Salidas digitales
        print("📤 Salidas Digitales:")
        for address, value in self.real_time_data["digital_outputs"].items():
            status = "🟢 ON" if value else "🔴 OFF"
            print(f"   {address}: {status}")
        
        # Entradas analógicas
        print("📊 Entradas Analógicas:")
        for address, value in self.real_time_data["analog_inputs"].items():
            print(f"   {address}: {value}")
        
        # Salidas analógicas
        print("📈 Salidas Analógicas:")
        for address, value in self.real_time_data["analog_outputs"].items():
            print(f"   {address}: {value}")
        
        # Marcas
        print("🏷️  Marcas:")
        for address, value in self.real_time_data["marks"].items():
            status = "🟢 ON" if value else "🔴 OFF"
            print(f"   {address}: {status}")
        
        # Bloques de datos
        print("💾 Bloques de Datos:")
        for address, value in self.real_time_data["data_blocks"].items():
            print(f"   {address}: {value}")
    
    def _on_connection_change(self, connected: bool):
        """Callback para cambios de conexión."""
        self.system_status["connected"] = connected
        status = "conectado" if connected else "desconectado"
        print(f"\n🔄 Estado de conexión: {status}")
    
    def _on_error(self, error: Exception):
        """Callback para errores."""
        print(f"\n❌ Error de conexión: {error}")
        self.system_status["error_count"] += 1
    
    def _on_heartbeat(self, timestamp: float):
        """Callback para heartbeat."""
        print(f"\n💓 Heartbeat recibido: {timestamp:.1f}")
    
    def _signal_handler(self, signum, frame):
        """Manejador de señal de interrupción."""
        print(f"\n⚠️ Señal de interrupción recibida ({signum})")
        self.stop()
        sys.exit(0)


def main():
    """Función principal."""
    print("🏭 Monitor Industrial Siemens S7-1200")
    print("=" * 50)
    
    # Configurar IP del PLC
    plc_ip = "192.168.1.5"  # Cambiar según tu configuración
    
    # Crear y ejecutar monitor
    monitor = IndustrialMonitor(plc_ip)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupción del usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
    finally:
        monitor.stop()


if __name__ == "__main__":
    main() 