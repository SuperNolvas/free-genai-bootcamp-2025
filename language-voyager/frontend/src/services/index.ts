import apiService from './api';
import webSocketService from './websocket';
import arcgisService from './arcgis';

export const cleanup = () => {
  // Cleanup WebSocket connections
  webSocketService.disconnect();
  
  // Cleanup ArcGIS resources
  arcgisService.destroy();
};

export { apiService, webSocketService, arcgisService };