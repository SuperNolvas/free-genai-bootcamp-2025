import React, { useEffect } from 'react';
import { useLocationTracking } from '@/hooks/useLocationTracking';
import { useArcGIS } from '@/hooks/useArcGIS';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Map as MapIcon, MapPinOff, Navigation } from 'lucide-react';

export default function Map() {
  const { currentLocation, startTracking, stopTracking, isTracking } = useLocationTracking();
  const { mapRef, focusOnLocation } = useArcGIS();

  useEffect(() => {
    if (currentLocation?.coords) {
      focusOnLocation(currentLocation.coords.latitude, currentLocation.coords.longitude);
    }
  }, [currentLocation, focusOnLocation]);

  return (
    <div className="relative h-full min-h-[calc(100vh-12rem)] w-full overflow-hidden rounded-lg border bg-background">
      <div ref={mapRef} className="h-full w-full" />
      
      <div className="absolute bottom-4 right-4 space-y-4">
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" className="h-10 w-10 rounded-full bg-background shadow-lg">
              <MapIcon className="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right">
            <SheetHeader>
              <SheetTitle>Map Controls</SheetTitle>
              <SheetDescription>
                Manage your location tracking and map settings
              </SheetDescription>
            </SheetHeader>
            <div className="mt-4 space-y-4">
              <Card className="p-4">
                <h3 className="font-medium">Location Tracking</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  {isTracking 
                    ? 'Your location is being tracked'
                    : 'Location tracking is disabled'}
                </p>
                <Button
                  variant={isTracking ? "destructive" : "default"}
                  onClick={isTracking ? stopTracking : startTracking}
                  className="w-full"
                >
                  {isTracking ? (
                    <>
                      <MapPinOff className="mr-2 h-4 w-4" />
                      Stop Tracking
                    </>
                  ) : (
                    <>
                      <Navigation className="mr-2 h-4 w-4" />
                      Start Tracking
                    </>
                  )}
                </Button>
              </Card>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  );
}