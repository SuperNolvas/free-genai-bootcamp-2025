import React from 'react'
import { useLocationTracking } from '@/hooks/useLocationTracking'
import { LocationTracker } from '@/components/map/LocationTracker'
import { Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const Map = () => {
  const { isConnected, locationConfig, permissionStatus, updateConfig } = useLocationTracking()

  return (
    <div className="space-y-4 p-4 lg:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Map</h1>
          <p className="text-sm text-muted-foreground">
            Explore language learning opportunities around you
          </p>
        </div>

        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon">
              <Settings className="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Location Settings</SheetTitle>
              <SheetDescription>
                Configure how location tracking works
              </SheetDescription>
            </SheetHeader>
            <div className="space-y-4 py-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="highAccuracy"
                  checked={locationConfig.highAccuracyMode}
                  onChange={(e) => updateConfig({ highAccuracyMode: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <label htmlFor="highAccuracy" className="text-sm">
                  High accuracy mode
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="backgroundMode"
                  checked={locationConfig.backgroundMode}
                  onChange={(e) => updateConfig({ backgroundMode: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <label htmlFor="backgroundMode" className="text-sm">
                  Background tracking
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="powerSave"
                  checked={locationConfig.powerSaveMode}
                  onChange={(e) => updateConfig({ powerSaveMode: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <label htmlFor="powerSave" className="text-sm">
                  Power save mode
                </label>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Your Area</CardTitle>
            <CardDescription>
              Nearby language learning opportunities will appear here
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[60vh] w-full rounded-lg bg-muted">
              Map Component Coming Soon
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Location Status</CardTitle>
              <CardDescription>
                Current location tracking status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Connection:</span>
                  <span className={`text-sm ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Permission:</span>
                  <span className="text-sm">
                    {permissionStatus === 'granted' ? 'Allowed' : permissionStatus === 'denied' ? 'Blocked' : 'Not requested'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Nearby Points</CardTitle>
              <CardDescription>
                Points of interest in your vicinity
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">No points found yet</p>
            </CardContent>
          </Card>
        </div>
      </div>

      <LocationTracker />
    </div>
  )
}

export default Map