document.addEventListener('alpine:init', () => {
    // Remove the standalone map component since it's now part of mapView
    Alpine.data('map', () => ({
        loading: true,
        error: null,

        async init() {
            try {
                // Wait for ArcGIS to be loaded (it exposes the require function)
                while (typeof require === 'undefined') {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }

                // Wait for MapManager to be initialized
                while (!window.MapManager) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }

                const mapContainer = document.getElementById('map-container');
                if (!mapContainer) {
                    throw new Error('Map container not found');
                }

                await window.MapManager.initialize(mapContainer);
                this.loading = false;
                this.error = null;

                // Dispatch event to notify components that map is ready
                window.dispatchEvent(new Event('map:ready'));
            } catch (error) {
                console.error('Failed to initialize map:', error);
                this.error = error.message || 'Failed to initialize map';
                this.loading = false;
            }
        }
    }));
});