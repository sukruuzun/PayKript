// PayKript Dashboard JavaScript

// Global değişkenler
let currentUser = null;
let currentSection = 'dashboard-overview';
let authToken = localStorage.getItem('paykript_token');

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM yüklendi, PayKript başlatılıyor');
    initializeDashboard();
    setupEventListeners();
});

// Dashboard başlatma
function initializeDashboard() {
    console.log('🚀 PayKript Dashboard başlatılıyor...');
    
    if (authToken) {
        console.log('🔑 Token mevcut, doğrulanıyor...');
        // Token geçerliliğini kontrol et
        validateToken()
            .then(valid => {
                console.log('✅ Token doğrulama sonucu:', valid);
                if (valid) {
                    showDashboard();
                    loadDashboardData();
                } else {
                    console.log('❌ Token geçersiz, login\'e yönlendiriliyor');
                    localStorage.removeItem('paykript_token');
                    authToken = null;
                    showLogin();
                }
            })
            .catch(error => {
                console.error('❌ Token doğrulama hatası:', error);
                // Hata durumunda da login'e yönlendir
                localStorage.removeItem('paykript_token');
                authToken = null;
                showLogin();
            });
    } else {
        console.log('🔓 Token yok, login ekranı gösteriliyor');
        showLogin();
    }
}

// Event listener'ları kur
function setupEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Profile form
    document.getElementById('profile-form').addEventListener('submit', handleProfileUpdate);
    
    // Password form
    document.getElementById('password-form').addEventListener('submit', handlePasswordChange);
    
    // Add wallet form
    document.getElementById('add-wallet-form').addEventListener('submit', handleAddWallet);
    
    // Add API key form
    document.getElementById('add-api-key-form').addEventListener('submit', handleAddApiKey);
    
    // Modal overlay tıklama
    document.getElementById('modal-overlay').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

// Login göster
function showLogin() {
    console.log('🔐 Login ekranı gösteriliyor');
    
    try {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('dashboard').classList.add('hidden');
        console.log('✅ Login ekranı başarıyla gösterildi');
    } catch (error) {
        console.error('❌ Login ekranı gösterme hatası:', error);
    }
}

// Dashboard göster
function showDashboard() {
    console.log('📊 Dashboard gösteriliyor');
    
    try {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');
        console.log('✅ Dashboard başarıyla gösterildi');
    } catch (error) {
        console.error('❌ Dashboard gösterme hatası:', error);
    }
}

// Login işlemi
async function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    console.log('🔐 Login işlemi başlatılıyor...');
    
    try {
        const response = await api.login(data);
        authToken = response.access_token;
        localStorage.setItem('paykript_token', authToken);
        
        // Kullanıcı bilgilerini al
        const userInfo = await api.getProfile();
        currentUser = userInfo;
        
        showDashboard();
        loadDashboardData();
        showToast('Başarıyla giriş yapıldı!', 'success');
        
        console.log('✅ Login başarılı!');
        
    } catch (error) {
        console.error('❌ Login hatası:', error);
        showToast(error.message || 'Giriş hatası', 'error');
    }
}

// Çıkış işlemi
function logout() {
    localStorage.removeItem('paykript_token');
    authToken = null;
    currentUser = null;
    showLogin();
    showToast('Çıkış yapıldı', 'info');
}

// Token geçerliliği kontrol et
async function validateToken() {
    if (!authToken) {
        console.log('❌ Token bulunamadı');
        return false;
    }
    
    try {
        console.log('🔄 API token doğrulaması başlatılıyor...');
        
        // 10 saniye timeout ekle
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Token doğrulama timeout')), 10000);
        });
        
        const response = await Promise.race([
            api.validateToken(),
            timeoutPromise
        ]);
        
        console.log('📡 Token doğrulama yanıtı:', response);
        return response && response.valid === true;
    } catch (error) {
        console.error('❌ Token doğrulama hatası:', error.message);
        return false;
    }
}

// Dashboard verilerini yükle
async function loadDashboardData() {
    try {
        // Kullanıcı bilgilerini göster
        if (currentUser) {
            document.getElementById('user-name').textContent = 
                currentUser.full_name || currentUser.email;
            
            // Profil formunu doldur
            document.getElementById('full-name').value = currentUser.full_name || '';
            document.getElementById('company-name').value = currentUser.company_name || '';
            document.getElementById('phone').value = currentUser.phone || '';
        }
        
        // İstatistikleri yükle
        await loadStats();
        
        // Son ödemeleri yükle
        await loadRecentPayments();
        
        // Cüzdanları yükle
        await loadWallets();
        
        // API anahtarlarını yükle
        await loadApiKeys();
        
    } catch (error) {
        showToast('Veri yükleme hatası: ' + error.message, 'error');
    }
}

// İstatistikleri yükle
async function loadStats() {
    try {
        const stats = await api.getDashboardStats();
        
        document.getElementById('total-payments').textContent = stats.total_payments;
        document.getElementById('confirmed-payments').textContent = stats.confirmed_payments;
        document.getElementById('pending-payments').textContent = stats.pending_payments;
        document.getElementById('total-amount').textContent = `${stats.total_amount} USDT`;
        document.getElementById('today-payments').textContent = stats.today_payments;
        document.getElementById('today-amount').textContent = `${stats.today_amount} USDT`;
        
    } catch (error) {
        console.error('İstatistik yükleme hatası:', error);
    }
}

// Son ödemeleri yükle
async function loadRecentPayments() {
    try {
        const payments = await api.getPayments({ limit: 5 });
        const container = document.getElementById('recent-payments');
        
        if (payments.length === 0) {
            container.innerHTML = '<p class="no-data">Henüz ödeme yok</p>';
            return;
        }
        
        container.innerHTML = payments.map(payment => `
            <div class="payment-item">
                <div class="payment-info">
                    <span class="order-id">#${payment.order_id}</span>
                    <span class="amount">${payment.amount} USDT</span>
                </div>
                <div class="payment-status">
                    <span class="status ${payment.status}">${getStatusText(payment.status)}</span>
                    <span class="date">${formatDate(payment.created_at)}</span>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Son ödemeler yükleme hatası:', error);
    }
}

// Tüm ödemeleri yükle
async function loadPayments(page = 1, status = '') {
    try {
        const params = { skip: (page - 1) * 50, limit: 50 };
        if (status) params.status_filter = status;
        
        const payments = await api.getPayments(params);
        const tbody = document.getElementById('payments-table-body');
        
        if (payments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="no-data">Ödeme bulunamadı</td></tr>';
            return;
        }
        
        tbody.innerHTML = payments.map(payment => `
            <tr>
                <td>${payment.order_id}</td>
                <td>${payment.amount} USDT</td>
                <td><span class="status ${payment.status}">${getStatusText(payment.status)}</span></td>
                <td>${formatDate(payment.created_at)}</td>
                <td>
                    <button class="btn btn-small" onclick="viewPayment(${payment.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        showToast('Ödemeler yüklenemedi: ' + error.message, 'error');
    }
}

// Cüzdanları yükle
async function loadWallets() {
    try {
        const wallets = await api.getWallets();
        const container = document.getElementById('wallets-list');
        
        if (wallets.length === 0) {
            container.innerHTML = '<div class="no-data">Henüz cüzdan eklenmemiş</div>';
            return;
        }
        
        container.innerHTML = wallets.map(wallet => `
            <div class="wallet-card ${wallet.is_active ? 'active' : ''}">
                <div class="wallet-header">
                    <h4>${wallet.wallet_name}</h4>
                    <span class="wallet-status ${wallet.is_active ? 'active' : 'inactive'}">
                        ${wallet.is_active ? 'Aktif' : 'Pasif'}
                    </span>
                </div>
                <div class="wallet-info">
                    <p><strong>Ağ:</strong> ${wallet.network.toUpperCase()}</p>
                    <p><strong>Adres Index:</strong> ${wallet.address_index}</p>
                    <p><strong>Oluşturulma:</strong> ${formatDate(wallet.created_at)}</p>
                </div>
                <div class="wallet-actions">
                    ${!wallet.is_active ? `<button class="btn btn-small btn-primary" onclick="activateWallet(${wallet.id})">Aktif Et</button>` : ''}
                    <button class="btn btn-small btn-secondary" onclick="testWalletAddress(${wallet.id})">Test Adresi</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        showToast('Cüzdanlar yüklenemedi: ' + error.message, 'error');
    }
}

// API anahtarlarını yükle
async function loadApiKeys() {
    try {
        const apiKeys = await api.getApiKeys();
        const container = document.getElementById('api-keys-list');
        
        if (apiKeys.length === 0) {
            container.innerHTML = '<div class="no-data">Henüz API anahtarı oluşturulmamış</div>';
            return;
        }
        
        container.innerHTML = apiKeys.map(key => `
            <div class="api-key-card">
                <div class="api-key-header">
                    <h4>${key.key_name}</h4>
                    <span class="api-key-status ${key.is_active ? 'active' : 'inactive'}">
                        ${key.is_active ? 'Aktif' : 'Pasif'}
                    </span>
                </div>
                <div class="api-key-info">
                    <p><strong>API Anahtarı:</strong> <code>${key.api_key}</code></p>
                    <p><strong>Son Kullanım:</strong> ${key.last_used_at ? formatDate(key.last_used_at) : 'Hiç kullanılmadı'}</p>
                    <p><strong>Oluşturulma:</strong> ${formatDate(key.created_at)}</p>
                </div>
                <div class="api-key-actions">
                    <button class="btn btn-small ${key.is_active ? 'btn-warning' : 'btn-success'}" 
                            onclick="toggleApiKey(${key.id}, ${!key.is_active})">
                        ${key.is_active ? 'Deaktif Et' : 'Aktif Et'}
                    </button>
                    <button class="btn btn-small btn-danger" onclick="deleteApiKey(${key.id})">Sil</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        showToast('API anahtarları yüklenemedi: ' + error.message, 'error');
    }
}

// Sekme gösterme
function showSection(sectionId) {
    // Aktif sekmeyi kaldır
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Yeni sekmeyi aktif et
    document.getElementById(sectionId).classList.add('active');
    event.target.closest('.menu-item').classList.add('active');
    
    // Sayfa başlığını güncelle
    const titles = {
        'dashboard-overview': 'Dashboard',
        'payments': 'Ödemeler',
        'wallets': 'Cüzdanlar',
        'api-keys': 'API Anahtarları',
        'settings': 'Ayarlar'
    };
    
    document.getElementById('page-title').textContent = titles[sectionId] || 'Dashboard';
    currentSection = sectionId;
    
    // Sekme özel yüklemeleri
    if (sectionId === 'payments') {
        loadPayments();
    }
}

// Modal gösterme
function showModal(modalId) {
    document.getElementById('modal-overlay').classList.remove('hidden');
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
    document.getElementById(modalId).style.display = 'block';
}

// Modal kapatma
function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

// Cüzdan ekleme modalı
function showAddWalletModal() {
    showModal('add-wallet-modal');
}

// API anahtarı ekleme modalı
function showAddApiKeyModal() {
    showModal('add-api-key-modal');
}

// Cüzdan ekleme işlemi
async function handleAddWallet(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        wallet_name: formData.get('wallet_name'),
        xpub_key: formData.get('xpub_key'),
        network: 'tron'
    };
    
    try {
        await api.addWallet(data);
        closeModal();
        await loadWallets();
        showToast('Cüzdan başarıyla eklendi!', 'success');
        e.target.reset();
        
    } catch (error) {
        showToast('Cüzdan ekleme hatası: ' + error.message, 'error');
    }
}

// API anahtarı ekleme işlemi
async function handleAddApiKey(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        key_name: formData.get('key_name')
    };
    
    try {
        const result = await api.addApiKey(data);
        closeModal();
        
        // Yeni API anahtarını göster
        showApiKeyModal(result);
        
        await loadApiKeys();
        e.target.reset();
        
    } catch (error) {
        showToast('API anahtarı oluşturma hatası: ' + error.message, 'error');
    }
}

// Yeni API anahtarını göster
function showApiKeyModal(apiKey) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3>Yeni API Anahtarı Oluşturuldu</h3>
            </div>
            <div class="modal-body">
                <div class="api-key-display">
                    <p><strong>Bu bilgileri güvenli bir yerde saklayın!</strong></p>
                    <div class="form-group">
                        <label>API Anahtarı:</label>
                        <div class="input-container">
                            <input type="text" value="${apiKey.api_key}" readonly>
                            <button class="copy-btn" onclick="copyToClipboard('${apiKey.api_key}')">Kopyala</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Secret Key:</label>
                        <div class="input-container">
                            <input type="text" value="${apiKey.secret_key}" readonly>
                            <button class="copy-btn" onclick="copyToClipboard('${apiKey.secret_key}')">Kopyala</button>
                        </div>
                    </div>
                </div>
                <div class="form-actions">
                    <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">Tamam</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Profil güncelleme
async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        full_name: formData.get('full_name'),
        company_name: formData.get('company_name'),
        phone: formData.get('phone')
    };
    
    try {
        await api.updateProfile(data);
        currentUser = { ...currentUser, ...data };
        showToast('Profil başarıyla güncellendi!', 'success');
        
    } catch (error) {
        showToast('Profil güncelleme hatası: ' + error.message, 'error');
    }
}

// Şifre değiştirme
async function handlePasswordChange(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const newPassword = formData.get('new_password');
    const confirmPassword = formData.get('confirm_password');
    
    if (newPassword !== confirmPassword) {
        showToast('Yeni şifreler eşleşmiyor!', 'error');
        return;
    }
    
    const data = {
        current_password: formData.get('current_password'),
        new_password: newPassword
    };
    
    try {
        await api.changePassword(data);
        showToast('Şifre başarıyla değiştirildi!', 'success');
        e.target.reset();
        
    } catch (error) {
        showToast('Şifre değiştirme hatası: ' + error.message, 'error');
    }
}

// Yardımcı fonksiyonlar
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('tr-TR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function getStatusText(status) {
    const statusTexts = {
        pending: 'Bekleyen',
        confirmed: 'Onaylandı',
        expired: 'Süresi Doldu',
        failed: 'Başarısız'
    };
    return statusTexts[status] || status;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Panoya kopyalandı!', 'success');
    }).catch(() => {
        showToast('Kopyalama başarısız!', 'error');
    });
}

// Toast bildirim gösterme
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas ${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    // Otomatik kaldırma
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

function getToastIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

// Şifre gösterme/gizleme
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleBtn = document.querySelector('.password-toggle i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleBtn.classList.remove('fa-eye');
        toggleBtn.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleBtn.classList.remove('fa-eye-slash');
        toggleBtn.classList.add('fa-eye');
    }
}

// Sidebar toggle (mobil)
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
}

// User menu toggle
function toggleUserMenu() {
    document.getElementById('user-dropdown').classList.toggle('show');
}

// Dışarı tıklanınca user menu'yu kapat
document.addEventListener('click', function(e) {
    if (!e.target.closest('.user-menu')) {
        document.getElementById('user-dropdown').classList.remove('show');
    }
});

// Ödemeleri filtreleme
function filterPayments() {
    const status = document.getElementById('payment-filter').value;
    loadPayments(1, status);
}

// Ödemeleri yenileme
function refreshPayments() {
    const status = document.getElementById('payment-filter').value;
    loadPayments(1, status);
    showToast('Ödemeler yenilendi', 'info');
}

// Cüzdan aktifleştirme
async function activateWallet(walletId) {
    try {
        await api.activateWallet(walletId);
        await loadWallets();
        showToast('Cüzdan aktifleştirildi!', 'success');
    } catch (error) {
        showToast('Cüzdan aktifleştirme hatası: ' + error.message, 'error');
    }
}

// Cüzdan test adresi
async function testWalletAddress(walletId) {
    try {
        const result = await api.getTestAddress(walletId);
        showToast(`Test adresi: ${result.test_address}`, 'info');
        copyToClipboard(result.test_address);
    } catch (error) {
        showToast('Test adresi alınamadı: ' + error.message, 'error');
    }
}

// API anahtarı durumu değiştirme
async function toggleApiKey(keyId, isActive) {
    try {
        await api.toggleApiKey(keyId, isActive);
        await loadApiKeys();
        showToast(`API anahtarı ${isActive ? 'aktifleştirildi' : 'deaktif edildi'}!`, 'success');
    } catch (error) {
        showToast('API anahtarı durumu değiştirilemedi: ' + error.message, 'error');
    }
}

// API anahtarı silme
async function deleteApiKey(keyId) {
    if (!confirm('Bu API anahtarını silmek istediğinizden emin misiniz?')) {
        return;
    }
    
    try {
        await api.deleteApiKey(keyId);
        await loadApiKeys();
        showToast('API anahtarı silindi!', 'success');
    } catch (error) {
        showToast('API anahtarı silinemedi: ' + error.message, 'error');
    }
}

// Ödeme detaylarını görüntüleme
function viewPayment(paymentId) {
    // Bu fonksiyon geliştirilecek
    showToast('Ödeme detayları özelliği yakında eklenecek!', 'info');
} 