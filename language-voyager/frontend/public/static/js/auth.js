document.addEventListener('alpine:init', () => {
    // Create a single auth store instance
    if (window.authStore) return;
    
    window.authStore = {
        isAuthenticated: false,
        isAuthReady: false,
        token: null,
        user: null,
        currentView: 'login',
        isLoading: false
    };

    Alpine.store('auth', {
        ...window.authStore,

        async init() {
            // Prevent re-initialization
            if (this.isAuthReady || this.isLoading) return;
            
            this.isLoading = true;
            this.token = localStorage.getItem('token');
            
            try {
                if (this.token) {
                    const response = await fetch('/api/v1/auth/validate', {
                        headers: {
                            'Authorization': `Bearer ${this.token}`
                        }
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        this.user = data.user;
                        this.isAuthenticated = true;
                    } else {
                        this.clearAuthState();
                    }
                }
            } catch (error) {
                console.error('Auth validation error:', error);
                this.clearAuthState();
            } finally {
                this.isAuthReady = true;
                this.isLoading = false;
                // Update the persistent store
                Object.assign(window.authStore, {
                    isAuthenticated: this.isAuthenticated,
                    isAuthReady: this.isAuthReady,
                    token: this.token,
                    user: this.user,
                    currentView: this.currentView
                });
            }
        },

        getToken() {
            return this.token;
        },

        setToken(token) {
            this.token = token;
            if (token) {
                localStorage.setItem('token', token);
                this.isAuthenticated = true;
                Object.assign(window.authStore, {
                    isAuthenticated: true,
                    token: token
                });
            } else {
                this.clearAuthState();
            }
        },

        setView(view) {
            if (!this.isLoading) {
                this.currentView = view;
                window.authStore.currentView = view;
            }
        },

        clearAuthState() {
            this.token = null;
            this.user = null;
            this.isAuthenticated = false;
            this.currentView = 'login';
            localStorage.removeItem('token');
            Object.assign(window.authStore, {
                isAuthenticated: false,
                token: null,
                user: null,
                currentView: 'login'
            });
        }
    });

    Alpine.data('auth', () => ({
        error: null,
        form: {
            email: '',
            password: ''
        },
        registerForm: {
            email: '',
            username: '',
            password: ''
        },
        resetForm: {
            email: ''
        },
        showVerificationNotice: false,
        resetRequestSuccess: null,

        init() {
            // Single initialization call
            if (!window.authStore.isAuthReady && !window.authStore.isLoading) {
                Alpine.store('auth').init();
            }
        },

        async login() {
            this.error = null;
            Alpine.store('auth').isLoading = true;
            
            try {
                const response = await fetch('/api/v1/auth/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: new URLSearchParams({
                        username: this.form.email,
                        password: this.form.password
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    Alpine.store('auth').setToken(data.access_token);
                } else {
                    const error = await response.json();
                    this.error = error.detail || 'Login failed';
                }
            } catch (error) {
                console.error('Login error:', error);
                this.error = 'An error occurred during login';
            } finally {
                Alpine.store('auth').isLoading = false;
            }
        },

        logout() {
            Alpine.store('auth').clearAuthState();
        }
    }));
});