document.addEventListener('alpine:init', () => {
    // Create app store for global navigation state
    Alpine.store('app', {
        activeView: localStorage.getItem('lastActiveView') || 'map',
        isOffline: !navigator.onLine,

        setView(view) {
            this.activeView = view;
            localStorage.setItem('lastActiveView', view);
            
            // Refresh map when switching to map view
            if (view === 'map') {
                requestAnimationFrame(() => {
                    window.dispatchEvent(new Event('map:refresh'));
                });
            }
        }
    });

    // App component for handling offline/sync
    Alpine.data('app', () => ({
        init() {
            // Handle online/offline status
            window.addEventListener('online', () => {
                this.$store.app.isOffline = false;
            });
            
            window.addEventListener('offline', () => {
                this.$store.app.isOffline = true;
            });
        }
    }));
});