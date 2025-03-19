import { useRef, useEffect, useCallback } from 'react';
import { arcgisService } from '@/services';

export function useArcGIS() {
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (mapRef.current) {
      arcgisService.initialize(mapRef.current);
      return () => {
        arcgisService.destroy();
      };
    }
  }, []);

  const focusOnLocation = useCallback((latitude: number, longitude: number) => {
    if (mapRef.current) {
      arcgisService.updateLocation(latitude, longitude);
    }
  }, []);

  return {
    mapRef,
    focusOnLocation
  };
}