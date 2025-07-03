'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { 
  Activity, 
  Power, 
  PowerOff, 
  Settings, 
  RefreshCw, 
  AlertCircle,
  CheckCircle,
  Clock,
  Wifi,
  WifiOff
} from 'lucide-react';

interface PLCData {
  connection: {
    status: string;
    ip: string;
    rack: number;
    slot: number;
    uptime: number;
    last_update: string | null;
  };
  inputs: {
    [key: string]: boolean;
  };
  outputs: {
    [key: string]: boolean;
  };
  analog: {
    [key: string]: number;
  };
  status: {
    cpu_info: {
      module_type: string;
      serial_number: string;
      as_name: string;
      module_name: string;
    };
    order_code: string;
    error_count: number;
    last_error: string | null;
  };
}

const PLCMonitor: React.FC = () => {
  const [plcData, setPlcData] = useState<PLCData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState({
    ip: '192.168.1.5',
    rack: 0,
    slot: 1
  });
  const [showConfig, setShowConfig] = useState(false);

  const API_BASE = 'http://localhost:5001/api/plc';

  const fetchPLCStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/status`);
      const result = await response.json();
      
      if (result.success) {
        setPlcData(result.data);
        setIsConnected(result.data.connection.status === 'connected');
        setError(null);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error conectando al API del PLC');
      console.error('Error fetching PLC status:', err);
    }
  }, []);

  const connectPLC = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();
      
      if (result.success) {
        setIsConnected(true);
        setError(null);
        fetchPLCStatus();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error conectando al PLC');
    } finally {
      setIsLoading(false);
    }
  };

  const disconnectPLC = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();
      
      if (result.success) {
        setIsConnected(false);
        setError(null);
        fetchPLCStatus();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error desconectando del PLC');
    } finally {
      setIsLoading(false);
    }
  };

  const writeOutput = async (output: string, value: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/output`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ output, value })
      });
      const result = await response.json();
      
      if (result.success) {
        fetchPLCStatus();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error escribiendo salida');
    }
  };

  const updateConfig = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const result = await response.json();
      
      if (result.success) {
        setShowConfig(false);
        fetchPLCStatus();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error actualizando configuración');
    } finally {
      setIsLoading(false);
    }
  };

  // Polling para actualizar datos
  useEffect(() => {
    fetchPLCStatus();
    
    const interval = setInterval(() => {
      if (isConnected) {
        fetchPLCStatus();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [fetchPLCStatus, isConnected]);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-green-500';
      case 'disconnected': return 'bg-red-500';
      case 'connecting': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Activity className="h-8 w-8 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold">PLC Monitor</h2>
            <p className="text-gray-600">Siemens PLC Communication</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowConfig(!showConfig)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Config
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={fetchPLCStatus}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          {isConnected ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={disconnectPLC}
              disabled={isLoading}
            >
              <PowerOff className="h-4 w-4 mr-2" />
              Disconnect
            </Button>
          ) : (
            <Button
              variant="default"
              size="sm"
              onClick={connectPLC}
              disabled={isLoading}
            >
              <Power className="h-4 w-4 mr-2" />
              Connect
            </Button>
          )}
        </div>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <Card>
          <CardHeader>
            <CardTitle>PLC Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="ip">IP Address</Label>
                <Input
                  id="ip"
                  value={config.ip}
                  onChange={(e) => setConfig({ ...config, ip: e.target.value })}
                  placeholder="192.168.1.5"
                />
              </div>
              <div>
                <Label htmlFor="rack">Rack</Label>
                <Input
                  id="rack"
                  type="number"
                  value={config.rack}
                  onChange={(e) => setConfig({ ...config, rack: parseInt(e.target.value) })}
                />
              </div>
              <div>
                <Label htmlFor="slot">Slot</Label>
                <Input
                  id="slot"
                  type="number"
                  value={config.slot}
                  onChange={(e) => setConfig({ ...config, slot: parseInt(e.target.value) })}
                />
              </div>
            </div>
            <Button onClick={updateConfig} disabled={isLoading}>
              Update Configuration
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Connection Status */}
      {plcData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {isConnected ? (
                <Wifi className="h-5 w-5 text-green-500" />
              ) : (
                <WifiOff className="h-5 w-5 text-red-500" />
              )}
              <span>Connection Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(plcData.connection.status)}`} />
                <span className="capitalize">{plcData.connection.status}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-gray-500" />
                <span>{formatUptime(plcData.connection.uptime)}</span>
              </div>
              <div>
                <span className="text-sm text-gray-500">IP:</span>
                <span className="ml-1 font-mono">{plcData.connection.ip}</span>
              </div>
              <div>
                <span className="text-sm text-gray-500">Rack/Slot:</span>
                <span className="ml-1">{plcData.connection.rack}/{plcData.connection.slot}</span>
              </div>
            </div>
            {plcData.connection.last_update && (
              <div className="mt-2 text-sm text-gray-500">
                Last update: {plcData.connection.last_update}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Digital Inputs */}
      {plcData && (
        <Card>
          <CardHeader>
            <CardTitle>Digital Inputs (E)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(plcData.inputs).map(([input, value]) => (
                <div key={input} className="flex items-center justify-between p-3 border rounded-lg">
                  <span className="font-mono">{input}</span>
                  <Badge variant={value ? "default" : "secondary"}>
                    {value ? "ON" : "OFF"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Digital Outputs */}
      {plcData && (
        <Card>
          <CardHeader>
            <CardTitle>Digital Outputs (A)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(plcData.outputs).map(([output, value]) => (
                <div key={output} className="flex items-center justify-between p-3 border rounded-lg">
                  <span className="font-mono">{output}</span>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={value}
                      onCheckedChange={(checked) => writeOutput(output, checked)}
                      disabled={!isConnected}
                    />
                    <Badge variant={value ? "default" : "secondary"}>
                      {value ? "ON" : "OFF"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analog Values */}
      {plcData && (
        <Card>
          <CardHeader>
            <CardTitle>Analog Inputs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(plcData.analog).map(([input, value]) => (
                <div key={input} className="p-3 border rounded-lg text-center">
                  <div className="font-mono text-sm text-gray-500">{input}</div>
                  <div className="text-2xl font-bold">{value}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* PLC Information */}
      {plcData && plcData.status.cpu_info.module_type !== 'N/A' && (
        <Card>
          <CardHeader>
            <CardTitle>PLC Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-500">Module Type:</span>
                <div className="font-medium">{plcData.status.cpu_info.module_type}</div>
              </div>
              <div>
                <span className="text-sm text-gray-500">Serial Number:</span>
                <div className="font-medium">{plcData.status.cpu_info.serial_number}</div>
              </div>
              <div>
                <span className="text-sm text-gray-500">AS Name:</span>
                <div className="font-medium">{plcData.status.cpu_info.as_name}</div>
              </div>
              <div>
                <span className="text-sm text-gray-500">Module Name:</span>
                <div className="font-medium">{plcData.status.cpu_info.module_name}</div>
              </div>
            </div>
            {plcData.status.error_count > 0 && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center space-x-2 text-yellow-800">
                  <AlertCircle className="h-4 w-4" />
                  <span>Error Count: {plcData.status.error_count}</span>
                </div>
                {plcData.status.last_error && (
                  <div className="mt-1 text-sm text-yellow-700">
                    Last Error: {plcData.status.last_error}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PLCMonitor; 