import React, { useEffect, useState } from 'react';
import MapManager from '../services/arcgis';
import { MapPin, Navigation } from 'lucide-react';

export default function Map() {
  const [isTracking, setIsTracking] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [watchId, setWatchId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) {
      console.error('Map container not found');
      return;
    }

    const initializeMap = async () => {
      try {
        await MapManager.initialize(mapContainer);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to initialize map:', error);
        setIsLoading(false);
      }
    };

    initializeMap();

    // Listen for map refresh events from Alpine.js
    const handleMapRefresh = () => {
      MapManager.refresh();
    };
    window.addEventListener('map:refresh', handleMapRefresh);

    return () => {
      window.removeEventListener('map:refresh', handleMapRefresh);
    };
  }, []);

  const toggleTracking = () => {
    if (isTracking && watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      setWatchId(null);
      setIsTracking(false);
    } else if ('geolocation' in navigator) {
      const id = navigator.geolocation.watchPosition(
        (position) => {
          MapManager.updateLocationMarker({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
        },
        (error) => {
          console.error('Geolocation error:', error);
          setIsTracking(false);
        }
      );
      setWatchId(id);
      setIsTracking(true);
    }
  };

  return (
    <>
      {isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-white bg-opacity-90 z-10">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-700">Loading map...</p>
        </div>
      )}
      
      <div className="absolute bottom-4 right-4">
        <button
          onClick={() => setShowControls(!showControls)}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-lg hover:bg-gray-100"
        >
          <MapPin className="h-4 w-4" />
        </button>
        {showControls && (
          <div className="absolute bottom-12 right-0 w-64 rounded-lg bg-white p-4 shadow-lg">
            <div className="mb-4">
              <h3 className="font-medium">Map Controls</h3>
              <p className="text-sm text-gray-600">
                {isTracking ? 'Your location is being tracked' : 'Location tracking is disabled'}
              </p>
            </div>
            <button
              onClick={toggleTracking}
              className={`w-full rounded-md px-4 py-2 text-sm font-medium text-white ${
                isTracking 
                  ? 'bg-red-500 hover:bg-red-600' 
                  : 'bg-blue-500 hover:bg-blue-600'
              }`}
            >
              <span className="flex items-center justify-center">
                {isTracking ? (
                  <>
                    <MapPin className="mr-2 h-4 w-4" />
                    Stop Tracking
                  </>
                ) : (
                  <>
                    <Navigation className="mr-2 h-4 w-4" />
                    Start Tracking
                  </>
                )}
              </span>
            </button>
          </div>
        )}
      </div>
    </>
  );
}