document.addEventListener('alpine:init', () => {
    Alpine.data('auth', () => ({
        isAuthenticated: false,
        authView: 'login', // login, register, resetRequest
        showVerificationNotice: false,
        resetRequestSuccess: null,
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
        error: null,

        init() {
            // Check for existing token
            const token = localStorage.getItem('token');
            if (token) {
                this.validateToken(token);
            }
            
            // Check URL for verification token
            const urlParams = new URLSearchParams(window.location.search);
            const verifyToken = urlParams.get('verify_token');
            if (verifyToken) {
                this.verifyEmail(verifyToken);
            }
        },

        async login() {
            this.error = null;
            try {
                const response = await fetch('/api/v1/auth/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        username: this.form.email,
                        password: this.form.password
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    localStorage.setItem('token', data.access_token);
                    this.isAuthenticated = true;
                    this.error = null;
                } else {
                    this.error = data.detail || 'Login failed';
                }
            } catch (err) {
                this.error = 'An error occurred during login';
                console.error('Login error:', err);
            }
        },

        async register() {
            this.error = null;
            try {
                const response = await fetch('/api/v1/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(this.registerForm)
                });
                const data = await response.json();
                if (response.ok) {
                    this.showVerificationNotice = true;
                    this.authView = 'login';
                    this.error = null;
                } else {
                    this.error = data.detail || 'Registration failed';
                }
            } catch (err) {
                this.error = 'An error occurred during registration';
                console.error('Registration error:', err);
            }
        },

        async requestPasswordReset() {
            this.error = null;
            this.resetRequestSuccess = null;
            try {
                const response = await fetch('/api/v1/auth/request-password-reset', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email: this.resetForm.email })
                });
                const data = await response.json();
                if (response.ok) {
                    this.resetRequestSuccess = 'Password reset instructions have been sent to your email';
                    setTimeout(() => {
                        this.authView = 'login';
                        this.resetRequestSuccess = null;
                    }, 3000);
                } else {
                    this.error = data.detail || 'Failed to request password reset';
                }
            } catch (err) {
                this.error = 'An error occurred while requesting password reset';
                console.error('Password reset request error:', err);
            }
        },

        async verifyEmail(token) {
            try {
                const response = await fetch(`/api/v1/auth/verify-email?token=${token}`, {
                    method: 'POST'
                });
                const data = await response.json();
                if (response.ok) {
                    this.error = null;
                    alert('Email verified successfully! You can now log in.');
                    // Remove token from URL without refreshing
                    window.history.replaceState({}, document.title, window.location.pathname);
                } else {
                    this.error = data.detail || 'Email verification failed';
                }
            } catch (err) {
                this.error = 'An error occurred during email verification';
                console.error('Email verification error:', err);
            }
        },

        async validateToken(token) {
            try {
                const response = await fetch('/api/v1/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                if (response.ok) {
                    this.isAuthenticated = true;
                } else {
                    localStorage.removeItem('token');
                    this.isAuthenticated = false;
                }
            } catch (err) {
                console.error('Token validation error:', err);
                localStorage.removeItem('token');
                this.isAuthenticated = false;
            }
        },

        logout() {
            localStorage.removeItem('token');
            this.isAuthenticated = false;
            this.form.email = '';
            this.form.password = '';
            this.authView = 'login';
        }
    }));
});