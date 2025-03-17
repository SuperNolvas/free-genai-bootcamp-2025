import { store } from '../store/store';
import { setCurrentLocation, setWebSocketConnected } from '../store/slices/mapSlice';
import { LocationConfig, LocationUpdate } from '../types/api';

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout = 1000; // Start with 1 second

  connect() {
    const token = store.getState().auth.token;
    if (!token) {
      console.error('No authentication token available');
      return;
    }

    this.ws = new WebSocket(`ws://localhost:8000/api/v1/map/ws/location`);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      store.dispatch(setWebSocketConnected(true));
      this.reconnectAttempts = 0;
      this.reconnectTimeout = 1000;
      
      // Send authentication immediately after connection
      this.ws?.send(JSON.stringify({
        type: 'authentication',
        token
      }));
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'location_update':
            store.dispatch(setCurrentLocation(data as LocationUpdate));
            break;
          case 'geolocation_error':
            console.error('Geolocation error:', data.message);
            break;
          case 'get_position':
            this.sendCurrentPosition();
            break;
          default:
            console.log('Received message:', data);
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      store.dispatch(setWebSocketConnected(false));
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.reconnectTimeout *= 2; // Exponential backoff
      
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        this.connect();
      }, this.reconnectTimeout);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  updateConfig(config: Partial<LocationConfig>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'config_update',
        data: { config }
      }));
    }
  }

  private sendCurrentPosition() {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
              type: 'position_update',
              position: {
                coords: {
                  latitude: position.coords.latitude,
                  longitude: position.coords.longitude,
                  accuracy: position.coords.accuracy
                },
                timestamp: position.timestamp
              }
            }));
          }
        },
        (error) => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
              type: 'geolocation_error',
              error: {
                code: error.code,
                message: error.message
              }
            }));
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 30000
        }
      );
    }
  }
}

export const webSocketService = new WebSocketService();
export default webSocketService;