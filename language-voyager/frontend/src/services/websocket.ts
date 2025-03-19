import { getSession } from '@/utils/session';
import { store } from '@/store/store';
import { setWebSocketConnected, setCurrentLocation } from '@/store/slices/mapSlice';
import { LocationUpdate, LocationConfig } from '@/types/api';

class WebSocketService {
  private ws: WebSocket | null = null;
  private readonly apiUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: number = 1000; // Start with 1 second
  private locationConfig: LocationConfig = {
    highAccuracyMode: true,
    timeout: 10000,
    maximumAge: 30000,
    minAccuracy: 20,
    updateInterval: 5000,
    minimumDistance: 10,
    backgroundMode: false,
    powerSaveMode: false
  };

  constructor() {
    this.apiUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const session = getSession();
    if (!session?.token) {
      console.error('No authentication token found');
      return;
    }

    try {
      this.ws = new WebSocket(`${this.apiUrl}?token=${session.token}`);

      this.ws.onopen = () => {
        console.log('WebSocket connection established');
        store.dispatch(setWebSocketConnected(true));
        this.reconnectAttempts = 0;
        this.reconnectTimeout = 1000;
        
        // Send initial config on connect
        this.updateConfig(this.locationConfig);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket connection closed');
        store.dispatch(setWebSocketConnected(false));
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        store.dispatch(setWebSocketConnected(false));
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      store.dispatch(setWebSocketConnected(false));
      this.attemptReconnect();
    }
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'location_update':
        store.dispatch(setCurrentLocation(data as LocationUpdate));
        break;
      case 'achievement_unlocked':
        // Handle achievement notification
        break;
      default:
        console.log('Unhandled message type:', data.type);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    setTimeout(() => {
      console.log('Attempting to reconnect...');
      this.reconnectAttempts++;
      this.reconnectTimeout *= 2; // Exponential backoff
      this.connect();
    }, this.reconnectTimeout);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    store.dispatch(setWebSocketConnected(false));
  }

  updateConfig(config: Partial<LocationConfig>) {
    this.locationConfig = { ...this.locationConfig, ...config };
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'config_update',
        config: this.locationConfig
      }));
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  }
}

export default new WebSocketService();