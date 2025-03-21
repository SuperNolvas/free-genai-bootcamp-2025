// Wait for ArcGIS API to load
require(['esri/Map', 'esri/views/MapView', 'esri/Graphic', 'esri/geometry/Point', 'esri/symbols/SimpleMarkerSymbol', 'esri/symbols/SimpleFillSymbol'], 
(Map, MapView, Graphic, Point, SimpleMarkerSymbol, SimpleFillSymbol) => {
    
    class ArcGISMapService {
        constructor() {
            // Basic initialization
            this.map = null;
            this.view = null;
            this.locationMarker = null;
            this.poiMarkers = new Map();
            this.regionPolygons = new Map();
            this.locationListeners = [];
            this.chatReady = false;
            this.initialLocation = null;

            // Use a plain object for cache instead of Map - simpler and more reliable
            this.locationCache = {};
            
            // Disable rate limiting
            this.lastFetchTime = 0;
            this.FETCH_COOLDOWN = 0; // No cooldown between requests
            this.consecutiveFailures = 0;
            this.MAX_BACKOFF = 0; // No backoff on failures
            
            // Cache settings
            this.MAX_CACHE_ENTRIES = 100;
            this.CACHE_EXPIRATION = 12 * 60 * 60 * 1000;

            // Bind methods to ensure proper 'this' context
            this.getLocationDetails = this.getLocationDetails.bind(this);
            this.updateLocationMarker = this.updateLocationMarker.bind(this);
            this.notifyLocationChange = this.notifyLocationChange.bind(this);
            this.getLocationName = this.getLocationName.bind(this);

            // Tokyo coordinates configuration
            this.TOKYO_CENTER = {
                latitude: 35.6762,
                longitude: 139.6503
            };
            this.TOKYO_BOUNDS = {
                north: 35.8187,
                south: 35.5311,
                east: 139.9224,
                west: 139.5804
            };
        }

        async initialize(container) {
            // Create the map
            this.map = new Map({
                basemap: 'streets-vector'
            });

            // Create the view
            this.view = new MapView({
                container,
                map: this.map,
                center: [this.TOKYO_CENTER.longitude, this.TOKYO_CENTER.latitude],
                zoom: 12,
                constraints: {
                    geometry: {
                        type: "extent",
                        xmin: this.TOKYO_BOUNDS.west,
                        ymin: this.TOKYO_BOUNDS.south,
                        xmax: this.TOKYO_BOUNDS.east,
                        ymax: this.TOKYO_BOUNDS.north,
                        spatialReference: { wkid: 4326 }
                    }
                }
            });

            await this.view.when();

            // Initialize location marker with a random position
            const initialLat = this.TOKYO_BOUNDS.south + 
                (Math.random() * (this.TOKYO_BOUNDS.north - this.TOKYO_BOUNDS.south));
            const initialLon = this.TOKYO_BOUNDS.west + 
                (Math.random() * (this.TOKYO_BOUNDS.east - this.TOKYO_BOUNDS.west));

            const point = new Point({
                longitude: initialLon,
                latitude: initialLat,
                spatialReference: { wkid: 4326 }
            });

            const locationSymbol = new SimpleMarkerSymbol({
                color: '#2196f3',
                outline: {
                    color: '#ffffff',
                    width: 2
                },
                size: 12
            });

            this.locationMarker = new Graphic({
                geometry: point,
                symbol: locationSymbol
            });
            
            this.view.graphics.add(this.locationMarker);

            // Add Tokyo region boundary
            await this.addRegionPolygon({
                id: "tokyo",
                name: "Tokyo",
                center_lat: this.TOKYO_CENTER.latitude,
                center_lon: this.TOKYO_CENTER.longitude,
                bounds: this.TOKYO_BOUNDS
            });

            // Set view to show the initial location and get details
            this.updateLocation(initialLat, initialLon);
            const initialDetails = await this.getLocationDetails(initialLat, initialLon);
            
            // Notify of initial location with details
            await this.notifyLocationChange({
                latitude: initialLat,
                longitude: initialLon,
                accuracy: 10,
                ...initialDetails
            });

            return this.view;
        }

        async setRandomLocation() {
            const latitude = this.TOKYO_BOUNDS.south + 
                (Math.random() * (this.TOKYO_BOUNDS.north - this.TOKYO_BOUNDS.south));
            const longitude = this.TOKYO_BOUNDS.west + 
                (Math.random() * (this.TOKYO_BOUNDS.east - this.TOKYO_BOUNDS.west));

            // Get location details first
            const details = await this.getLocationDetails(latitude, longitude);
            
            // Update marker and trigger full location update with details
            await this.updateLocationMarker({
                latitude,
                longitude,
                accuracy: 10,
                ...details
            });

            return { latitude, longitude };
        }

        updateLocation(latitude, longitude) {
            if (this.view) {
                this.view.goTo({
                    center: [longitude, latitude],
                    zoom: 15
                });
            }
        }

        async updateLocationMarker(location) {
            if (!this.view || !location.latitude || !location.longitude) return;

            const point = new Point({
                longitude: location.longitude,
                latitude: location.latitude,
                spatialReference: { wkid: 4326 }
            });

            if (this.locationMarker) {
                this.locationMarker.geometry = point;
            }

            this.updateLocation(location.latitude, location.longitude);

            // Look for nearby cached location first to avoid API call
            const nearbyDetails = this.findNearestCachedLocation(location.latitude, location.longitude, 0.001);
            if (nearbyDetails) {
                console.log('Using nearby cached location details instead of API call');
                return await this.notifyLocationChange({
                    ...location,
                    ...nearbyDetails
                });
            }
            
            // Only fetch new details if really needed
            const details = await this.getLocationDetails(location.latitude, location.longitude);
            
            await this.notifyLocationChange({
                ...location,
                ...details
            });

            // Update LLM context with current location details
            const currentLocationDetails = await this.getLocationDetails(location.latitude, location.longitude);
            await this.updateLLMContext(currentLocationDetails);
        }

        async updateLLMContext(locationDetails) {
            try {
                const response = await fetch('/api/v1/conversation/context', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ current_location: locationDetails })
                });
                if (!response.ok) {
                    throw new Error(`Failed to update LLM context: ${response.statusText}`);
                }
            } catch (error) {
                console.error('Failed to update LLM context:', error);
            }
        }

        onLocationChange(listener) {
            this.locationListeners.push(listener);
            return () => {
                this.locationListeners = this.locationListeners.filter(l => l !== listener);
            };
        }

        async notifyLocationChange(location) {
            // Create location context with proper name handling
            const locationDetail = {
                ...location,
                // Use local_name (Japanese) if available, fallback to name
                name: location.local_name || location.name || this.getLocationName({ 
                    latitude: location.latitude, 
                    longitude: location.longitude 
                }),
                local_name: location.local_name || '',
                type: location.type || this.determinePOIType(location),
                region: 'Tokyo'
            };

            console.log('Full location detail being sent:', locationDetail);

            // Dispatch custom event for the chat interface
            window.dispatchEvent(new CustomEvent('location:updated', {
                detail: locationDetail
            }));

            // Notify existing listeners
            this.locationListeners.forEach(listener => listener(locationDetail));
        }

        determinePOIType(location) {
            if (!this.view) return 'area';
            
            if (this.view.zoom >= 19) {
                return 'building';
            } else if (this.view.zoom >= 17) {
                return 'street';
            } else if (this.view.zoom >= 13) {
                return 'neighborhood';
            } else {
                return 'area';
            }
        }

        getLocationName(location) {
            try {
                // Format coordinates nicely
                const lat = Math.abs(location.latitude).toFixed(4) + '°' + (location.latitude >= 0 ? 'N' : 'S');
                const lon = Math.abs(location.longitude).toFixed(4) + '°' + (location.longitude >= 0 ? 'E' : 'W');
                
                // First check POI markers if we have any
                if (this.poiMarkers.size > 0) {
                    for (const [_, marker] of this.poiMarkers) {
                        if (!marker?.geometry) continue;
                        
                        if (this.isNearby(location, {
                            latitude: marker.geometry.latitude,
                            longitude: marker.geometry.longitude
                        })) {
                            return marker.attributes?.name || `${lat}, ${lon}`;
                        }
                    }
                }
                
                // If no POI is found, return formatted coordinates
                return `${lat}, ${lon}`;
            } catch (error) {
                console.warn('Error checking POI markers:', error);
                return `${location.latitude.toFixed(4)}°N, ${location.longitude.toFixed(4)}°E`;
            }
        }

        isNearby(loc1, loc2, threshold = 0.001) { // roughly 100 meters
            if (!loc1 || !loc2) return false;
            return Math.abs(loc1.latitude - loc2.latitude) < threshold &&
                   Math.abs(loc1.longitude - loc2.longitude) < threshold;
        }

        async getLocationDetails(latitude, longitude) {
            if (!latitude || !longitude) {
                console.warn('Invalid coordinates provided to getLocationDetails');
                return this.getDefaultLocationDetails(latitude, longitude);
            }

            try {
                const cacheKey = `${latitude},${longitude}`;
                
                // Check cache first - Using simple object property check
                if (this.locationCache[cacheKey] && this.locationCache[cacheKey].timestamp) {
                    // Check if cache entry is still valid
                    const now = Date.now();
                    if (now - this.locationCache[cacheKey].timestamp < this.CACHE_EXPIRATION) {
                        console.log('Cache hit for location:', cacheKey);
                        return this.locationCache[cacheKey];
                    }
                }

                // Check for nearby locations in cache - to minimize API calls
                const nearbyLocation = this.findNearestCachedLocation(latitude, longitude, 0.005); // ~500m (increased radius)
                if (nearbyLocation) {
                    console.log('Using nearby cached location details');
                    return nearbyLocation;
                }

                // Implement rate limiting with exponential backoff
                const now = Date.now();
                const timeSinceLastFetch = now - this.lastFetchTime;
                
                // Calculate backoff time based on consecutive failures
                const backoffTime = this.consecutiveFailures > 0 
                    ? Math.min(this.FETCH_COOLDOWN * Math.pow(2, this.consecutiveFailures), this.MAX_BACKOFF)
                    : this.FETCH_COOLDOWN;
                
                if (timeSinceLastFetch < backoffTime) {
                    console.log(`Rate limiting - waiting ${backoffTime - timeSinceLastFetch}ms before next request`);
                    await new Promise(resolve => setTimeout(resolve, backoffTime - timeSinceLastFetch));
                }

                console.log('Fetching location details for:', latitude, longitude);
                const response = await fetch(`/api/v1/map/location/details?lat=${latitude}&lon=${longitude}`);
                this.lastFetchTime = Date.now();

                if (!response.ok) {
                    // Handle rate limiting specifically
                    if (response.status === 429) {
                        this.consecutiveFailures++;
                        const retryAfter = response.headers.get('Retry-After') || 60;
                        const backoffSeconds = Math.min(
                            Math.pow(2, this.consecutiveFailures) * 5,
                            this.MAX_BACKOFF/1000
                        );
                        console.warn(`Rate limited (429). Using backoff strategy. Retry after: ${retryAfter}s, Calculated backoff: ${backoffSeconds}s`);
                        
                        // Store simplified details in cache to prevent repeated failures
                        const fallbackDetails = this.getDefaultLocationDetails(latitude, longitude);
                        fallbackDetails.timestamp = now;
                        this.locationCache[cacheKey] = fallbackDetails;
                        return fallbackDetails;
                    }
                    throw new Error(`Failed to fetch location details: ${response.status} ${response.statusText}`);
                }

                // Reset failure counter on success
                this.consecutiveFailures = 0;
                
                const data = await response.json();
                console.log('Raw location details response:', data);
                
                // Create location details object
                const details = {
                    name: data.local_name || data.name || this.getLocationName({ latitude, longitude }),
                    local_name: data.local_name || '',
                    description: data.description || '',
                    type: data.type || this.determinePOIType({ latitude, longitude }),
                    region_specific_customs: data.customs || {},
                    timestamp: now
                };

                // Manage cache size - remove oldest entries if needed
                const cacheKeys = Object.keys(this.locationCache);
                if (cacheKeys.length >= this.MAX_CACHE_ENTRIES) {
                    let oldestKey = cacheKeys[0];
                    let oldestTime = Infinity;
                    
                    for (const key of cacheKeys) {
                        const entry = this.locationCache[key];
                        if (entry.timestamp && entry.timestamp < oldestTime) {
                            oldestTime = entry.timestamp;
                            oldestKey = key;
                        }
                    }
                    
                    delete this.locationCache[oldestKey];
                }

                // Cache the successful response using plain object
                this.locationCache[cacheKey] = details;
                console.log('Cached location details:', details);
                
                return details;

            } catch (error) {
                console.warn('Error fetching location details:', error);
                this.consecutiveFailures++;
                
                // Use more aggressive backoff on error
                const backoffTime = Math.min(this.FETCH_COOLDOWN * Math.pow(2, this.consecutiveFailures), this.MAX_BACKOFF);
                console.warn(`API request failed. Using backoff: ${backoffTime/1000}s before next attempt`);
                
                return this.getDefaultLocationDetails(latitude, longitude);
            }
        }

        getDefaultLocationDetails(latitude, longitude) {
            // Try to find nearest cached location first with a wider radius during failures
            const radius = this.consecutiveFailures > 0 ? 0.02 * this.consecutiveFailures : 0.01; // Grow radius with failures
            const nearest = this.findNearestCachedLocation(latitude, longitude, Math.min(radius, 0.05));
            if (nearest) {
                console.log('Found nearest cached location:', nearest);
                return nearest;
            }
            
            // Fallback to coordinate-based location
            return {
                name: this.getLocationName({ latitude, longitude }),
                local_name: '',
                description: '',
                type: this.determinePOIType({ latitude, longitude }),
                region_specific_customs: {},
                timestamp: Date.now()
            };
        }

        findNearestCachedLocation(latitude, longitude, maxDistance = 0.01) { // roughly 1km
            let nearest = null;
            let minDistance = maxDistance;
            // Iterate through cache - adapted for plain object instead of Map
            for (const key in this.locationCache) {
                const [cachedLat, cachedLon] = key.split(',').map(Number);
                const distance = Math.sqrt(
                    Math.pow(latitude - cachedLat, 2) + 
                    Math.pow(longitude - cachedLon, 2)
                );
                if (distance < minDistance) {
                    minDistance = distance;
                    nearest = this.locationCache[key];
                }
            }
            return nearest;
        }

        async addRegionPolygon(region) {
            if (!this.view) return;

            const polygonGeometry = {
                type: "polygon",
                rings: [
                    [
                        [region.bounds?.west || region.center_lon - 0.1, region.bounds?.south || region.center_lat - 0.1],
                        [region.bounds?.east || region.center_lon + 0.1, region.bounds?.south || region.center_lat - 0.1],
                        [region.bounds?.east || region.center_lon + 0.1, region.bounds?.north || region.center_lat + 0.1],
                        [region.bounds?.west || region.center_lon - 0.1, region.bounds?.north || region.center_lat + 0.1],
                        [region.bounds?.west || region.center_lon - 0.1, region.bounds?.south || region.center_lat - 0.1]
                    ]
                ],
                spatialReference: { wkid: 4326 }
            };

            const symbol = new SimpleFillSymbol({
                color: [51, 51, 204, 0.2],
                outline: {
                    color: [51, 51, 204],
                    width: 1
                }
            });

            const graphic = new Graphic({
                geometry: polygonGeometry,
                symbol,
                attributes: {
                    id: region.id,
                    name: region.name
                }
            });

            this.regionPolygons.set(region.id, graphic);
            this.view.graphics.add(graphic);
        }

        clearAll() {
            if (this.view) {
                this.view.graphics.removeAll();
                this.poiMarkers.clear();
                this.regionPolygons.clear();
                
                if (this.locationMarker) {
                    this.view.graphics.add(this.locationMarker);
                }
            }
        }

        refresh() {
            if (this.view) {
                this.view.goTo({
                    center: [this.TOKYO_CENTER.longitude, this.TOKYO_CENTER.latitude],
                    zoom: 12
                });
            }
        }
    }

    // Initialize and expose MapManager globally
    window.MapManager = new ArcGISMapService();
});