import { WebSocketService } from './WebSocketService';

export interface GeolocationConfig {
    highAccuracyMode: boolean;
    timeout: number;
    maximumAge: number;
    minAccuracy: number;
    updateInterval: number;
    minimumDistance: number;
    backgroundMode: boolean;
    powerSaveMode: boolean;
}

export class LocationService {
    private ws: WebSocketService;
    private watchId: number | null = null;
    private config: GeolocationConfig;
    private lastPosition: GeolocationPosition | null = null;
    private onLocationUpdate?: (position: GeolocationPosition) => void;
    private onError?: (error: GeolocationError) => void;

    constructor() {
        this.ws = new WebSocketService('/api/v1/map/ws/location');
        this.config = {
            highAccuracyMode: true,
            timeout: 10000,
            maximumAge: 30000,
            minAccuracy: 20.0,
            updateInterval: 5.0,
            minimumDistance: 10.0,
            backgroundMode: false,
            powerSaveMode: false
        };

        // Setup WebSocket message handlers
        this.ws.onMessage((data) => this.handleWebSocketMessage(data));
    }

    public async startTracking(config: Partial<GeolocationConfig> = {}): Promise<void> {
        // Update config with any provided values
        this.config = { ...this.config, ...config };

        // Check if geolocation is available
        if (!navigator.geolocation) {
            this.handleError(new GeolocationPositionError());
            return;
        }

        try {
            // Request permission first
            const permission = await navigator.permissions.query({ name: 'geolocation' });
            if (permission.state === 'denied') {
                this.handleError(new GeolocationPositionError());
                return;
            }

            // Start watching position
            this.watchId = navigator.geolocation.watchPosition(
                (position) => this.handlePositionUpdate(position),
                (error) => this.handleError(error),
                {
                    enableHighAccuracy: this.config.highAccuracyMode,
                    timeout: this.config.timeout,
                    maximumAge: this.config.maximumAge
                }
            );

        } catch (error) {
            this.handleError(error as GeolocationPositionError);
        }
    }

    public stopTracking(): void {
        if (this.watchId !== null) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
        }
        this.ws.close();
    }

    public onUpdate(callback: (position: GeolocationPosition) => void): void {
        this.onLocationUpdate = callback;
    }

    public onLocationError(callback: (error: GeolocationError) => void): void {
        this.onError = callback;
    }

    private handlePositionUpdate(position: GeolocationPosition): void {
        // Don't send updates if accuracy is worse than minAccuracy
        if (position.coords.accuracy > this.config.minAccuracy) {
            return;
        }

        // Check if we've moved far enough for an update
        if (this.lastPosition) {
            const distance = this.calculateDistance(
                this.lastPosition.coords,
                position.coords
            );
            if (distance < this.config.minimumDistance) {
                return;
            }
        }

        this.lastPosition = position;
        
        // Send update to server
        this.ws.send({
            type: 'position_update',
            position: {
                coords: {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    altitude: position.coords.altitude,
                    altitudeAccuracy: position.coords.altitudeAccuracy,
                    heading: position.coords.heading,
                    speed: position.coords.speed
                },
                timestamp: position.timestamp
            }
        });

        // Notify subscribers
        if (this.onLocationUpdate) {
            this.onLocationUpdate(position);
        }
    }

    private handleError(error: GeolocationPositionError): void {
        this.ws.send({
            type: 'geolocation_error',
            error: {
                code: error.code,
                message: error.message
            }
        });

        if (this.onError) {
            this.onError(error);
        }
    }

    private handleWebSocketMessage(data: any): void {
        switch (data.type) {
            case 'geolocation_init':
                // Update tracking configuration
                if (data.config) {
                    this.startTracking(data.config);
                }
                break;
            case 'geolocation_error':
                // Handle server-side errors or configuration changes
                if (data.action === 'adjust_settings' && data.settings) {
                    this.startTracking(data.settings);
                }
                break;
            case 'get_position':
                // Server requested immediate position update
                if (this.lastPosition) {
                    this.handlePositionUpdate(this.lastPosition);
                }
                break;
        }
    }

    private calculateDistance(coords1: GeolocationCoordinates, coords2: GeolocationCoordinates): number {
        // Haversine formula for calculating distance between two points
        const R = 6371e3; // Earth's radius in meters
        const φ1 = coords1.latitude * Math.PI/180;
        const φ2 = coords2.latitude * Math.PI/180;
        const Δφ = (coords2.latitude - coords1.latitude) * Math.PI/180;
        const Δλ = (coords2.longitude - coords1.longitude) * Math.PI/180;

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                Math.cos(φ1) * Math.cos(φ2) *
                Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

        return R * c; // Distance in meters
    }
}