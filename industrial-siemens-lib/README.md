# Industrial Siemens Library

**Biblioteca completa para comunicación industrial con PLCs Siemens y otros dispositivos industriales.**

## 🚀 Características Principales

### 📡 Protocolos Soportados
- **S7 Protocol**: Comunicación directa con PLCs Siemens (S7-300, S7-400, S7-1200, S7-1500)
- **Modbus TCP/RTU**: Comunicación con VFDs, PLCs y dispositivos Modbus
- **Profibus-DP**: Comunicación con dispositivos Profibus industriales
- **Ethernet/IP**: Comunicación con dispositivos Allen-Bradley y otros CIP
- **OPC UA**: Comunicación estándar industrial OPC Unified Architecture

### 🔄 Comunicación PLC-PLC
- Sincronización automática de datos entre múltiples PLCs
- Soporte para diferentes protocolos en la misma red
- Mapeo flexible de datos entre dispositivos
- Recuperación automática de errores

### ⚡ Control de VFDs
- Control de Variadores de Frecuencia (VFD)
- Monitoreo en tiempo real de parámetros
- Soporte para múltiples fabricantes (Siemens, Allen-Bradley, etc.)
- Control de velocidad, frecuencia y par

### 🛠️ Funcionalidades Avanzadas
- **Async/Await**: Programación asíncrona completa
- **Type Hints**: Soporte completo de tipos Python
- **Error Handling**: Manejo robusto de errores industriales
- **Logging**: Sistema de logging estructurado
- **Monitoring**: Monitoreo y diagnóstico de dispositivos
- **Database Integration**: Integración con bases de datos
- **Real-time Dashboards**: Dashboards en tiempo real

## 📦 Instalación

```bash
# Clonar repositorio
git clone https://github.com/your-repo/industrial-siemens-lib.git
cd industrial-siemens-lib

# Instalar dependencias
pip install -r requirements.txt

# Para desarrollo
pip install -r requirements-dev.txt
```

## 🎯 Uso Rápido

### Conexión Básica a PLC Siemens

```python
import asyncio
from siemens_plc.protocols import S7Protocol
from siemens_plc.protocols.base import ProtocolConfig, ProtocolType, ReadRequest

async def main():
    # Configurar conexión S7
    config = ProtocolConfig(
        protocol_type=ProtocolType.S7,
        host="192.168.1.10",
        s7_rack=0,
        s7_slot=1,
        timeout=5000
    )
    
    # Crear cliente S7
    plc = S7Protocol(config)
    
    # Conectar
    if await plc.connect():
        print("✅ Conectado al PLC")
        
        # Leer datos
        request = ReadRequest(address=100, count=1, data_type="float32")
        data = await plc.read_data(request)
        print(f"Datos leídos: {data}")
        
        # Desconectar
        await plc.disconnect()

asyncio.run(main())
```

### Comunicación Modbus con VFD

```python
import asyncio
from siemens_plc.protocols import ModbusTCP
from siemens_plc.protocols.base import ReadRequest, WriteRequest

async def main():
    # Conectar a VFD via Modbus TCP
    vfd = ModbusTCP("192.168.1.20", port=502)
    
    if await vfd.connect():
        print("✅ Conectado al VFD")
        
        # Leer frecuencia de salida
        freq_request = ReadRequest(address=2100, count=1, data_type="float32")
        frequency = await vfd.read_data(freq_request)
        print(f"Frecuencia: {frequency[0]} Hz")
        
        # Establecer frecuencia
        set_freq_request = WriteRequest(address=2000, value=30.0, data_type="float32")
        await vfd.write_data(set_freq_request)
        print("Frecuencia establecida a 30 Hz")
        
        await vfd.disconnect()

asyncio.run(main())
```

### Red PLC-PLC Completa

```python
import asyncio
from siemens_plc.communication import PLCNetwork

async def main():
    # Configurar red PLC-PLC
    network_config = {
        'plcs': [
            {
                'id': 'plc_main',
                'name': 'PLC Principal',
                'protocol': 's7',
                'host': '192.168.1.10',
                'rack': 0,
                'slot': 1,
                'is_master': True
            },
            {
                'id': 'plc_aux',
                'name': 'PLC Auxiliar', 
                'protocol': 'modbus_tcp',
                'host': '192.168.1.11',
                'port': 502,
                'is_master': False
            }
        ],
        'mappings': [
            {
                'source_plc': 'plc_main',
                'source_address': 100,
                'source_data_type': 'float32',
                'target_plc': 'plc_aux',
                'target_address': 200,
                'target_data_type': 'float32',
                'sync_mode': 'continuous'
            }
        ]
    }
    
    # Crear y iniciar red
    network = PLCNetwork("Mi_Red_Industrial")
    await network.load_config(network_config)
    await network.start_network()
    
    print("🌐 Red PLC-PLC iniciada")
    
    # Mantener ejecutando
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await network.stop_network()

asyncio.run(main())
```

### Control de VFD Completo

```python
import asyncio
from siemens_plc.communication import VFDCommunication

async def main():
    # Configurar VFD
    vfd_config = {
        'id': 'motor_principal',
        'name': 'Motor Principal',
        'protocol': 'modbus_tcp',
        'host': '192.168.1.20',
        'port': 502,
        'manufacturer': 'Siemens',
        'model': 'G120',
        'power_rating': 5.5,
        'max_frequency': 60.0
    }
    
    # Crear VFD
    vfd = await VFDCommunication.create_vfd('modbus_tcp', vfd_config)
    
    # Conectar
    if await vfd.connect():
        print("✅ Conectado al VFD")
        
        # Controlar VFD
        await vfd.set_frequency(30.0)  # 30 Hz
        await vfd.start_drive()
        
        # Monitorear
        while True:
            params = await vfd.read_parameters()
            print(f"Frecuencia: {params.output_frequency} Hz")
            print(f"Velocidad: {params.output_speed} RPM")
            print(f"Corriente: {params.output_current} A")
            print(f"Estado: {params.status.value}")
            await asyncio.sleep(2)
    
    await vfd.disconnect()

asyncio.run(main())
```

## 📋 Protocolos Detallados

### S7 Protocol (Siemens)

```python
from siemens_plc.protocols import S7Protocol

# Configuración
config = ProtocolConfig(
    protocol_type=ProtocolType.S7,
    host="192.168.1.10",
    s7_rack=0,
    s7_slot=1
)

plc = S7Protocol(config)

# Funciones disponibles
await plc.connect()
await plc.read_data(request)
await plc.write_data(request)
await plc.get_cpu_info()
await plc.get_plc_status()
```

### Modbus TCP/RTU

```python
from siemens_plc.protocols import ModbusTCP, ModbusRTU

# Modbus TCP
modbus_tcp = ModbusTCP("192.168.1.20", port=502)

# Modbus RTU
modbus_rtu = ModbusRTU("/dev/ttyUSB0", baudrate=9600)

# Tipos de datos soportados
# - bool (coils/discrete inputs)
# - uint16, int16 (holding/input registers)
# - uint32, int32, float32 (múltiples registros)
```

### Profibus-DP

```python
from siemens_plc.protocols import ProfibusDP

profibus = ProfibusDP("192.168.1.30", slave_address=1)

# Áreas de memoria
# - PE: Process Inputs
# - PA: Process Outputs  
# - MK: Marks
# - DB: Data Blocks
# - CT: Counters
# - TM: Timers
```

### Ethernet/IP

```python
from siemens_plc.protocols import EthernetIPProtocol

ethernet_ip = EthernetIPProtocol(ProtocolConfig(
    protocol_type=ProtocolType.ETHERNET_IP,
    host="192.168.1.40",
    port=44818
))

# Servicios CIP soportados
# - Read Tag
# - Write Tag
# - Get Attribute Single
# - Set Attribute Single
```

### OPC UA

```python
from siemens_plc.protocols import OPCUAProtocol

opc_ua = OPCUAProtocol(ProtocolConfig(
    protocol_type=ProtocolType.OPC_UA,
    host="192.168.1.50",
    port=4840
))

# Funciones avanzadas
await opc_ua.browse_nodes()
await opc_ua.subscribe_to_nodes(node_ids, callback)
```

## 🔧 Configuración Avanzada

### Configuración de Red PLC-PLC

```python
network_config = {
    'plcs': [
        {
            'id': 'plc_1',
            'name': 'PLC Principal',
            'protocol': 's7',
            'host': '192.168.1.10',
            'rack': 0,
            'slot': 1,
            'is_master': True,
            'sync_interval': 1000,
            'priority': 1
        }
    ],
    'mappings': [
        {
            'source_plc': 'plc_1',
            'source_address': 100,
            'source_data_type': 'float32',
            'target_plc': 'plc_2', 
            'target_address': 200,
            'target_data_type': 'float32',
            'sync_mode': 'continuous',  # continuous, on_change, periodic
            'sync_interval': 1000
        }
    ]
}
```

### Configuración de VFD

```python
vfd_config = {
    'id': 'motor_1',
    'name': 'Motor Principal',
    'protocol': 'modbus_tcp',
    'host': '192.168.1.20',
    'port': 502,
    'manufacturer': 'Siemens',
    'model': 'G120',
    'power_rating': 5.5,
    'max_frequency': 60.0,
    'max_speed': 1750.0,
    'control_mode': 'frequency',  # frequency, speed, torque
    'enabled': True
}
```

## 📊 Monitoreo y Diagnóstico

### Estado de la Red

```python
# Obtener estado completo
network_info = await network.get_network_info()

print(f"Red: {network_info['name']}")
print(f"PLCs conectados: {len(network_info['status']['plcs'])}")
print(f"Mapeos activos: {network_info['status']['mappings']}")

for plc_id, status in network_info['status']['plcs'].items():
    print(f"  {plc_id}: {status['connected']} ({status['name']})")
```

### Estadísticas de Protocolo

```python
# Obtener estadísticas
status = await protocol.get_status()

print(f"Conectado: {status.is_connected}")
print(f"Última comunicación: {status.last_communication}")
print(f"Errores: {status.error_count}")
print(f"Éxitos: {status.success_count}")
print(f"Tiempo respuesta promedio: {status.response_time_avg:.2f} ms")
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/

# Con cobertura
pytest --cov=siemens_plc tests/

# Tests específicos
pytest tests/test_s7_protocol.py
pytest tests/test_modbus_protocol.py
```

## 📚 Ejemplos

Ver la carpeta `examples/` para ejemplos completos:

- `basic_industrial_monitor.py`: Monitoreo básico industrial
- `multi_protocol_industrial_system.py`: Sistema multi-protocolo completo
- `plc_plc_communication.py`: Comunicación PLC-PLC
- `vfd_control.py`: Control de VFDs
- `opc_ua_client.py`: Cliente OPC UA

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

- 📧 Email: support@industrial-siemens-lib.com
- 📖 Documentación: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/industrial-siemens-lib/issues)
- 💬 Discord: [Industrial Automation Community](https://discord.gg/industrial-automation)

## 🙏 Agradecimientos

- **Snap7**: Biblioteca base para comunicación S7
- **PyModbus**: Implementación Modbus
- **AsyncUA**: Cliente OPC UA asíncrono
- **CPPPO**: Biblioteca Ethernet/IP

---

**¡Construyendo el futuro de la automatización industrial! 🏭⚡** 