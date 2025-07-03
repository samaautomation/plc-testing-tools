#!/usr/bin/env python3
"""
PLC Service for SAMABOT UI Light
================================

Servicio de comunicación con PLC Siemens que puede ser integrado
con la interfaz web de SAMABOT UI Light.
"""

import time
import json
import threading
from typing import Dict, Any, Optional
import snap7
from snap7 import Area
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PLC_Service")

class PLCService:
    """Servicio de comunicación con PLC Siemens."""
    
    def __init__(self, ip: str = "192.168.1.5", rack: int = 0, slot: int = 1):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.connected = False
        self.running = False
        self.monitor_thread = None
        self.data = {
            "connection": {
                "status": "disconnected",
                "ip": ip,
                "rack": rack,
                "slot": slot,
                "uptime": 0,
                "last_update": None
            },
            "inputs": {
                "E0.0": False,
                "E0.1": False,
                "E0.2": False,
                "E0.3": False,
                "E0.4": False,
                "E0.5": False,
                "E0.6": False,
                "E0.7": False
            },
            "outputs": {
                "A0.0": False,
                "A0.1": False,
                "A0.2": False,
                "A0.3": False,
                "A0.4": False,
                "A0.5": False,
                "A0.6": False,
                "A0.7": False
            },
            "analog": {
                "AIW0": 0,
                "AIW2": 0,
                "AIW4": 0,
                "AIW6": 0
            },
            "status": {
                "cpu_info": {},
                "order_code": "",
                "error_count": 0,
                "last_error": None
            }
        }
        self.connection_time = 0
        
    def connect(self) -> bool:
        """Conecta al PLC."""
        try:
            logger.info(f"Conectando al PLC {self.ip}...")
            self.client.connect(self.ip, self.rack, self.slot)
            
            if self.client.get_connected():
                self.connected = True
                self.connection_time = time.time()
                self.data["connection"]["status"] = "connected"
                self.data["connection"]["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
                logger.info("✅ Conectado exitosamente al PLC")
                
                # Obtener información del PLC
                self._get_plc_info()
                return True
            else:
                logger.error("❌ No se pudo conectar al PLC")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando al PLC: {e}")
            self.data["status"]["last_error"] = str(e)
            self.data["status"]["error_count"] += 1
            return False
    
    def disconnect(self):
        """Desconecta del PLC."""
        try:
            self.stop_monitoring()
            if self.client.get_connected():
                self.client.disconnect()
            self.connected = False
            self.data["connection"]["status"] = "disconnected"
            logger.info("🔌 Desconectado del PLC")
        except Exception as e:
            logger.error(f"Error desconectando: {e}")
    
    def _get_plc_info(self):
        """Obtiene información del PLC."""
        try:
            # CPU Info
            cpu_info = self.client.get_cpu_info()
            self.data["status"]["cpu_info"] = {
                "module_type": str(cpu_info.get('ModuleTypeName', 'N/A')),
                "serial_number": str(cpu_info.get('SerialNumber', 'N/A')),
                "as_name": str(cpu_info.get('ASName', 'N/A')),
                "module_name": str(cpu_info.get('ModuleName', 'N/A'))
            }
            
            # Order Code
            order_code = self.client.get_order_code()
            self.data["status"]["order_code"] = str(order_code)
            
        except Exception as e:
            logger.warning(f"No se pudo obtener información del PLC: {e}")
    
    def read_inputs(self):
        """Lee todas las entradas digitales."""
        if not self.connected:
            return
        
        try:
            # Leer 1 byte de entradas digitales (E área)
            data = self.client.read_area(Area.PE, 0, 0, 1)
            
            # Actualizar cada entrada
            for i in range(8):
                bit_value = bool(data[0] & (1 << i))
                self.data["inputs"][f"E0.{i}"] = bit_value
                
        except Exception as e:
            logger.error(f"Error leyendo entradas: {e}")
            self.data["status"]["last_error"] = str(e)
            self.data["status"]["error_count"] += 1
    
    def read_outputs(self):
        """Lee todas las salidas digitales."""
        if not self.connected:
            return
        
        try:
            # Leer 1 byte de salidas digitales (A área)
            data = self.client.read_area(Area.PA, 0, 0, 1)
            
            # Actualizar cada salida
            for i in range(8):
                bit_value = bool(data[0] & (1 << i))
                self.data["outputs"][f"A0.{i}"] = bit_value
                
        except Exception as e:
            logger.error(f"Error leyendo salidas: {e}")
            self.data["status"]["last_error"] = str(e)
            self.data["status"]["error_count"] += 1
    
    def write_output(self, output: str, value: bool) -> bool:
        """Escribe una salida digital específica."""
        if not self.connected:
            return False
        
        try:
            # Parsear salida (ej: "A0.0" -> byte 0, bit 0)
            if not output.startswith("A"):
                raise ValueError("Solo se pueden escribir salidas (A)")
            
            parts = output.split(".")
            if len(parts) != 2:
                raise ValueError("Formato inválido. Use A0.0, A0.1, etc.")
            
            byte_num = int(parts[0][1:])  # 0
            bit_num = int(parts[1])       # 0-7
            
            # Leer estado actual
            current_data = self.client.read_area(Area.PA, 0, byte_num, 1)
            
            # Modificar bit específico
            new_data = bytearray(current_data)
            if value:
                new_data[0] |= (1 << bit_num)   # Set bit
            else:
                new_data[0] &= ~(1 << bit_num)  # Clear bit
            
            # Escribir
            self.client.write_area(Area.PA, 0, byte_num, bytes(new_data))
            
            # Actualizar datos locales
            self.data["outputs"][output] = value
            
            logger.info(f"✅ {output} = {'ON' if value else 'OFF'}")
            return True
            
        except Exception as e:
            logger.error(f"Error escribiendo {output}: {e}")
            self.data["status"]["last_error"] = str(e)
            self.data["status"]["error_count"] += 1
            return False
    
    def read_analog(self):
        """Lee entradas analógicas."""
        if not self.connected:
            return
        
        try:
            # Leer 4 words analógicas (AIW0, AIW2, AIW4, AIW6)
            for i in range(4):
                word_addr = i * 2
                data = self.client.read_area(Area.PE, 0, word_addr, 2)
                value = int.from_bytes(data, byteorder='big')
                self.data["analog"][f"AIW{word_addr}"] = value
                
        except Exception as e:
            logger.error(f"Error leyendo analógicas: {e}")
            self.data["status"]["last_error"] = str(e)
            self.data["status"]["error_count"] += 1
    
    def _monitor_loop(self):
        """Loop principal de monitoreo."""
        while self.running:
            if self.connected:
                try:
                    # Actualizar tiempo de conexión
                    uptime = time.time() - self.connection_time
                    self.data["connection"]["uptime"] = int(uptime)
                    self.data["connection"]["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Leer datos
                    self.read_inputs()
                    self.read_outputs()
                    self.read_analog()
                    
                except Exception as e:
                    logger.error(f"Error en loop de monitoreo: {e}")
                    self.data["status"]["last_error"] = str(e)
                    self.data["status"]["error_count"] += 1
            
            time.sleep(0.5)  # Actualizar cada 500ms
    
    def start_monitoring(self):
        """Inicia el monitoreo en background."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🔄 Monitoreo iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("⏹️ Monitoreo detenido")
    
    def get_data(self) -> Dict[str, Any]:
        """Obtiene los datos actuales del PLC."""
        return self.data.copy()
    
    def get_json(self) -> str:
        """Obtiene los datos en formato JSON."""
        return json.dumps(self.data, indent=2)
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Función para uso directo
def create_plc_service(ip: str = "192.168.1.5", rack: int = 0, slot: int = 1) -> PLCService:
    """Factory function para crear un servicio PLC."""
    return PLCService(ip, rack, slot)


if __name__ == "__main__":
    # Test del servicio
    print("🚀 TEST PLC SERVICE")
    print("===================")
    
    with PLCService() as plc:
        if plc.connected:
            print("✅ Servicio iniciado")
            
            # Iniciar monitoreo
            plc.start_monitoring()
            
            # Simular algunas operaciones
            for i in range(10):
                print(f"\n--- Iteración {i+1} ---")
                data = plc.get_data()
                print(f"Estado: {data['connection']['status']}")
                print(f"E0.0: {data['inputs']['E0.0']}")
                print(f"A0.0: {data['outputs']['A0.0']}")
                
                # Alternar A0.0
                plc.write_output("A0.0", i % 2 == 0)
                
                time.sleep(2)
            
            plc.stop_monitoring()
            print("\n✅ Test completado")
        else:
            print("❌ No se pudo conectar al PLC") 