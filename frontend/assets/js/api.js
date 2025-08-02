// PayKript API Client

class PayKriptAPI {
    constructor() {
        this.baseURL = 'http://localhost:8000/api/v1';
        this.token = localStorage.getItem('paykript_token');
    }

    // HTTP request helper
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            }
        };

        const config = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);
            
            // Token süresi dolmuşsa otomatik çıkış yap
            if (response.status === 401) {
                localStorage.removeItem('paykript_token');
                this.token = null;
                if (window.showLogin) {
                    window.showLogin();
                }
                throw new Error('Oturum süresi doldu. Lütfen tekrar giriş yapın.');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || `HTTP ${response.status}`);
            }

            return data;
            
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Sunucuya bağlanılamıyor. Lütfen internet bağlantınızı kontrol edin.');
            }
            throw error;
        }
    }

    // GET request
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, {
            method: 'GET'
        });
    }

    // POST request
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT request
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    // Authentication endpoints
    async login(credentials) {
        const response = await this.post('/auth/giris', credentials);
        this.token = response.access_token;
        return response;
    }

    async register(userData) {
        return this.post('/auth/kayit', userData);
    }

    async validateToken() {
        return this.post('/auth/token-kontrol');
    }

    // User profile endpoints
    async getProfile() {
        return this.get('/auth/profil');
    }

    async updateProfile(data) {
        return this.put('/auth/profil', data);
    }

    async changePassword(data) {
        return this.post('/auth/sifre-degistir', data);
    }

    // Dashboard statistics
    async getDashboardStats() {
        return this.get('/odemeler/istatistikler');
    }

    // Payment endpoints
    async getPayments(params = {}) {
        return this.get('/odemeler/liste', params);
    }

    async getPayment(paymentId) {
        return this.get(`/odemeler/durum/${paymentId}`);
    }

    async getPaymentByOrderId(orderId) {
        return this.get(`/odemeler/siparis/${orderId}`);
    }

    async createPayment(paymentData) {
        return this.post('/odemeler/olustur', paymentData);
    }

    async cancelPayment(paymentId) {
        return this.post(`/odemeler/iptal/${paymentId}`);
    }

    async getPaymentTransactions(paymentId) {
        return this.get(`/odemeler/islemler/${paymentId}`);
    }

    async getPaymentQR(paymentId) {
        return this.get(`/odemeler/qr/${paymentId}`);
    }

    // Wallet endpoints
    async getWallets() {
        return this.get('/yonetim/cuzdanlar');
    }

    async addWallet(walletData) {
        return this.post('/yonetim/cuzdanlar', walletData);
    }

    async activateWallet(walletId) {
        return this.put(`/yonetim/cuzdanlar/${walletId}/aktif`);
    }

    async deleteWallet(walletId) {
        return this.delete(`/yonetim/cuzdanlar/${walletId}`);
    }

    async getTestAddress(walletId) {
        return this.get(`/yonetim/cuzdanlar/${walletId}/test-adres`);
    }

    // API Keys endpoints
    async getApiKeys() {
        return this.get('/yonetim/api-anahtarlari');
    }

    async addApiKey(keyData) {
        return this.post('/yonetim/api-anahtarlari', keyData);
    }

    async toggleApiKey(keyId, isActive) {
        return this.put(`/yonetim/api-anahtarlari/${keyId}/durum`, { is_active: isActive });
    }

    async deleteApiKey(keyId) {
        return this.delete(`/yonetim/api-anahtarlari/${keyId}`);
    }

    // Helper methods for specific use cases
    async checkPaymentStatus(paymentId) {
        try {
            const payment = await this.getPayment(paymentId);
            return {
                status: 'success',
                payment_status: payment.status,
                expires_at: payment.expires_at,
                confirmed_at: payment.confirmed_at
            };
        } catch (error) {
            return {
                status: 'error',
                message: error.message
            };
        }
    }

    // Webhook test
    async testWebhook(webhookUrl) {
        return this.post('/webhook/test', { webhook_url: webhookUrl });
    }

    // File upload helper (for future use)
    async uploadFile(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                // Content-Type header'ı otomatik olarak ayarlanacak
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            }
        });
    }

    // Bulk operations
    async bulkUpdatePayments(paymentIds, updates) {
        return this.post('/odemeler/bulk-update', {
            payment_ids: paymentIds,
            updates: updates
        });
    }

    // Export data
    async exportPayments(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = `/odemeler/export?${queryString}`;
        
        const response = await fetch(`${this.baseURL}${url}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        return response.blob();
    }

    // Real-time updates (WebSocket connection - for future implementation)
    connectWebSocket() {
        if (this.ws) {
            this.ws.close();
        }

        const wsURL = this.baseURL.replace('http', 'ws') + '/ws';
        this.ws = new WebSocket(`${wsURL}?token=${this.token}`);

        this.ws.onopen = () => {
            console.log('WebSocket bağlantısı kuruldu');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket bağlantısı kapandı');
            // Otomatik yeniden bağlanma
            setTimeout(() => {
                if (this.token) {
                    this.connectWebSocket();
                }
            }, 5000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket hatası:', error);
        };
    }

    handleWebSocketMessage(data) {
        // WebSocket mesajlarını işle
        switch (data.type) {
            case 'payment_confirmed':
                if (window.onPaymentConfirmed) {
                    window.onPaymentConfirmed(data.payment);
                }
                break;
            case 'payment_expired':
                if (window.onPaymentExpired) {
                    window.onPaymentExpired(data.payment);
                }
                break;
            default:
                console.log('Bilinmeyen WebSocket mesajı:', data);
        }
    }

    disconnectWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    // Rate limiting helper
    async withRateLimit(fn, maxRetries = 3, delay = 1000) {
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await fn();
            } catch (error) {
                if (error.message.includes('429') && i < maxRetries - 1) {
                    await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
                    continue;
                }
                throw error;
            }
        }
    }

    // Health check
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseURL.replace('/api/v1', '')}/health`);
            return response.ok;
        } catch {
            return false;
        }
    }
}

// Global API instance
const api = new PayKriptAPI();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PayKriptAPI;
} 