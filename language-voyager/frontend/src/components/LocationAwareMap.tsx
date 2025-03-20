import React, { useEffect, useState } from 'react';
import { LocationService } from '../services/LocationService';
import MapManager from '../services/arcgis';
import { MapPin, Navigation } from 'lucide-react';

export function LocationAwareMap() {
  const [isTracking, setIsTracking] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [locationService] = useState(() => new LocationService());

  useEffect(() => {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) {
      console.error('Map container not found');
      return;
    }

    // Initialize map
    MapManager.initialize(mapContainer);

    // Setup location update handler
    locationService.onUpdate((position) => {
      MapManager.updateLocationMarker({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy
      });
    });

    // Setup error handler
    locationService.onLocationError((error) => {
      console.error('Location error:', error);
      setIsTracking(false);
    });

    // Listen for map refresh events
    const handleMapRefresh = () => {
      MapManager.refresh();
    };
    window.addEventListener('map:refresh', handleMapRefresh);

    return () => {
      window.removeEventListener('map:refresh', handleMapRefresh);
      locationService.stopTracking();
    };
  }, [locationService]);

  const toggleTracking = async () => {
    if (isTracking) {
      locationService.stopTracking();
      setIsTracking(false);
    } else {
      try {
        await locationService.startTracking();
        setIsTracking(true);
      } catch (error) {
        console.error('Failed to start tracking:', error);
      }
    }
  };

  return (
    <>
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
              <h3 className="font-medium">Location Controls</h3>
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