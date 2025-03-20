document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        activeView: localStorage.getItem('lastActiveView') || 'map',
        isOffline: !navigator.onLine,

        init() {
            // Only update localStorage when view changes, and only if the change was triggered by user action
            this.$watch('activeView', (value) => {
                if (value) {
                    localStorage.setItem('lastActiveView', value);
                    
                    // Use requestAnimationFrame to prevent refresh loops when updating map
                    if (value === 'map') {
                        requestAnimationFrame(() => {
                            window.dispatchEvent(new Event('map:refresh'));
                        });
                    }
                }
            });

            // Handle navigation clicks
            document.querySelectorAll('[x-on\\:click]').forEach(el => {
                if (el.getAttribute('x-on:click').includes('activeView =')) {
                    el.addEventListener('click', (e) => {
                        e.preventDefault();
                        const view = el.getAttribute('data-view');
                        if (view) {
                            this.activeView = view;
                        }
                    });
                }
            });

            // Handle online/offline status
            window.addEventListener('online', () => {
                this.isOffline = false;
                this.checkSync();
            });
            
            window.addEventListener('offline', () => {
                this.isOffline = true;
                this.handleOffline();
            });
        },

        async checkSync() {
            const pendingSync = JSON.parse(localStorage.getItem('pendingSync') || '[]');
            if (pendingSync.length > 0) {
                console.log('Syncing pending items:', pendingSync);
            }
        },

        handleOffline() {
            console.log('App is offline');
        }
    }));
});