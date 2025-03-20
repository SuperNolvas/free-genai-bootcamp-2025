document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        activeView: 'map',

        init() {
            // Listen for view changes
            this.$watch('activeView', (value) => {
                if (value === 'map') {
                    // Trigger map initialization/refresh
                    window.dispatchEvent(new Event('map:refresh'));
                }
            });

            // Handle offline status
            window.addEventListener('online', () => this.checkSync());
            window.addEventListener('offline', () => this.handleOffline());
        },

        async checkSync() {
            // Check if there are any pending sync items
            const pendingSync = JSON.parse(localStorage.getItem('pendingSync') || '[]');
            if (pendingSync.length > 0) {
                // TODO: Implement sync logic
                console.log('Syncing pending items:', pendingSync);
            }
        },

        handleOffline() {
            // TODO: Show offline notification
            console.log('App is offline');
        }
    }));
});