# Integración PLC con SAMABOT UI Light

## 🚀 Resumen

Este proyecto integra la comunicación con PLC Siemens en SAMABOT UI Light, permitiendo monitoreo y control en tiempo real de entradas/salidas digitales y analógicas.

## 📁 Estructura del Proyecto

```
plc-testing-tools/
├── industrial-siemens-lib/
│   ├── examples/
│   │   ├── plc_service.py          # Servicio principal de comunicación PLC
│   │   ├── test_direct.py          # Test directo con Snap7
│   │   └── test_working.py         # Test con librería wrapper
│   └── siemens_plc/                # Librería de comunicación
├── api/
│   └── plc_api.py                  # API Flask para la interfaz web
├── ui/
│   └── PLCMonitor.tsx              # Componente React para SAMABOT UI
└── README-INTEGRATION.md           # Este archivo
```

## 🔧 Instalación

### 1. En el Jetson Nano

```bash
# Clonar el repositorio
git clone https://github.com/samaautomation/plc-testing-tools.git
cd plc-testing-tools

# Instalar dependencias
pip3 install flask flask-cors

# Verificar que Snap7 esté instalado
python3 -c "import snap7; print('Snap7 OK')"
```

### 2. En SAMABOT UI Light

```bash
# Copiar el componente React
cp plc-testing-tools/ui/PLCMonitor.tsx src/components/ui/

# Agregar el componente a la página principal
# En src/app/page.tsx, agregar:
import PLCMonitor from '@/components/ui/PLCMonitor';
```

## 🚀 Uso

### 1. Iniciar el API del PLC

```bash
cd plc-testing-tools/api
python3 plc_api.py
```

El API estará disponible en `http://localhost:5001`

### 2. Integrar en SAMABOT UI Light

Agregar el componente `PLCMonitor` a tu página principal:

```tsx
// En src/app/page.tsx
import PLCMonitor from '@/components/ui/PLCMonitor';

export default function Home() {
  return (
    <div>
      {/* Otros componentes */}
      <PLCMonitor />
    </div>
  );
}
```

### 3. Configurar el PLC

En la interfaz web:
1. Hacer clic en "Config"
2. Ingresar IP del PLC (default: 192.168.1.5)
3. Configurar Rack y Slot (default: 0, 1)
4. Hacer clic en "Connect"

## 📡 Endpoints del API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/plc/status` | Estado completo del PLC |
| POST | `/api/plc/connect` | Conectar al PLC |
| POST | `/api/plc/disconnect` | Desconectar del PLC |
| POST | `/api/plc/output` | Escribir salida digital |
| GET | `/api/plc/inputs` | Leer entradas digitales |
| GET | `/api/plc/outputs` | Leer salidas digitales |
| GET | `/api/plc/analog` | Leer valores analógicos |
| POST | `/api/plc/config` | Actualizar configuración |
| GET | `/api/plc/health` | Health check |

## 🔌 Funcionalidades

### ✅ Comunicación Real-time
- Monitoreo continuo de entradas/salidas
- Actualización automática cada 500ms
- Reconexión automática en caso de error

### ✅ Entradas Digitales (E)
- E0.0 a E0.7 (8 entradas)
- Estado ON/OFF en tiempo real
- Indicadores visuales

### ✅ Salidas Digitales (A)
- A0.0 a A0.7 (8 salidas)
- Control ON/OFF con switches
- Escritura individual o múltiple

### ✅ Entradas Analógicas
- AIW0, AIW2, AIW4, AIW6
- Valores de 16 bits
- Actualización en tiempo real

### ✅ Información del PLC
- Tipo de módulo
- Número de serie
- Nombre del AS
- Código de orden
- Contador de errores

## 🎨 Interfaz de Usuario

### Características Visuales
- **Estado de conexión**: Indicador visual con colores
- **Uptime**: Tiempo de conexión activa
- **Switches interactivos**: Para controlar salidas
- **Badges de estado**: ON/OFF para entradas y salidas
- **Panel de configuración**: IP, Rack, Slot
- **Información de errores**: Contador y último error

### Responsive Design
- Grid adaptativo para diferentes tamaños de pantalla
- Componentes que se ajustan automáticamente
- Interfaz optimizada para móviles y tablets

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Configurar IP del PLC
export PLC_IP=192.168.1.5
export PLC_RACK=0
export PLC_SLOT=1

# Configurar puerto del API
export PLC_API_PORT=5001
```

### Personalización del Componente

```tsx
// Personalizar el componente
<PLCMonitor 
  apiUrl="http://localhost:5001/api/plc"
  refreshInterval={1000}
  showConfig={true}
  showAnalog={true}
/>
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de conexión al PLC**
   - Verificar IP, Rack y Slot
   - Comprobar conectividad de red
   - Verificar que Snap7 esté instalado

2. **API no responde**
   - Verificar que el servidor Flask esté corriendo
   - Comprobar puerto 5001
   - Revisar logs del servidor

3. **Datos no se actualizan**
   - Verificar conexión al PLC
   - Comprobar que el monitoreo esté activo
   - Revisar errores en la consola

### Logs y Debug

```bash
# Ver logs del servicio PLC
python3 plc_service.py

# Ver logs del API
python3 plc_api.py

# Test directo de conexión
python3 test_direct.py
```

## 🔄 Actualizaciones

Para actualizar el sistema:

```bash
# En el Jetson
cd plc-testing-tools
git pull origin main

# Reiniciar el API
pkill -f plc_api.py
python3 api/plc_api.py
```

## 📊 Monitoreo y Métricas

El sistema proporciona:
- **Uptime de conexión**
- **Contador de errores**
- **Último error registrado**
- **Estado de cada I/O**
- **Información del hardware**

## 🔒 Seguridad

- API protegido con validación de entrada
- Manejo de errores robusto
- Timeouts de conexión
- Reconexión automática segura

## 🚀 Próximas Mejoras

- [ ] Soporte para múltiples PLCs
- [ ] Histórico de datos
- [ ] Alertas y notificaciones
- [ ] Configuración por archivo
- [ ] Autenticación de API
- [ ] Dashboard avanzado

---

## 📞 Soporte

Para soporte técnico:
- Email: support@sama-engineering.com
- GitHub Issues: [plc-testing-tools](https://github.com/samaautomation/plc-testing-tools)

---

**Desarrollado por SAMA Engineering** 🏭⚡ 