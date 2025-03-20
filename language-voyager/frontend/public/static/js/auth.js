document.addEventListener('alpine:init', () => {
    // Create auth store
    Alpine.store('auth', {
        isAuthReady: false,
        isAuthenticated: false,
        token: null,

        init() {
            const token = localStorage.getItem('token');
            if (token) {
                this.token = token;
                this.isAuthenticated = true;
            }
            this.isAuthReady = true;
        },

        getToken() {
            return this.token;
        }
    });

    // Initialize auth store
    Alpine.store('auth').init();
});