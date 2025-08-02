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
        // İlk kez dashboard açılıyorsa aktif section'ı ayarla
        if (!document.querySelector('.content-section.active')) {
            showSection('dashboard-overview');
        }
        
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

// ========================================
// TOAST NOTIFICATION SYSTEM  
// ========================================

// Enhanced toast system
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${getToastIcon(type)}"></i>
        </div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="closeToast(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });
    
    // Auto remove
    const autoRemove = setTimeout(() => {
        closeToast(toast.querySelector('.toast-close'));
    }, duration);
    
    // Store timeout for manual close
    toast.dataset.timeout = autoRemove;
    
    console.log(`📢 Toast shown: ${type} - ${message}`);
}

// Create toast container if not exists
function createToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    return container;
}

// Close toast
function closeToast(closeBtn) {
    const toast = closeBtn.closest('.toast');
    if (toast) {
        // Clear auto-remove timeout
        if (toast.dataset.timeout) {
            clearTimeout(parseInt(toast.dataset.timeout));
        }
        
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// Toast ikonları
function getToastIcon(type) {
    const icons = {
        success: 'fa-check',
        error: 'fa-exclamation',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info'
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

// ========================================
// NAVIGATION & UI MANAGEMENT
// ========================================

// Section navigation
function showSection(sectionId) {
    console.log('📍 Navigating to section:', sectionId);
    
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
        
        // Update page title
        const sectionTitles = {
            'dashboard-overview': 'Dashboard',
            'payments': 'Ödemeler',
            'wallets': 'Cüzdanlar',
            'api-keys': 'API Anahtarları',
            'settings': 'Ayarlar',
            'profile': 'Profil'
        };
        
        const pageTitle = document.getElementById('page-title');
        if (pageTitle) {
            pageTitle.textContent = sectionTitles[sectionId] || 'Dashboard';
        }
        
        // Update active menu item
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeMenuItem = document.querySelector(`[onclick="showSection('${sectionId}')"]`)?.parentElement;
        if (activeMenuItem) {
            activeMenuItem.classList.add('active');
        }
        
        // Load section data
        loadSectionData(sectionId);
        
        // Close mobile sidebar if open
        closeMobileSidebar();
        
        currentSection = sectionId;
        console.log('✅ Section activated:', sectionId);
    } else {
        console.error('❌ Section not found:', sectionId);
    }
}

// Load section-specific data
function loadSectionData(sectionId) {
    switch(sectionId) {
        case 'dashboard-overview':
            loadDashboardData();
            break;
        case 'payments': 
            loadPayments();
            break;
        case 'wallets':
            loadWallets();
            break;
        case 'api-keys':
            loadApiKeys();
            break;
        case 'settings':
        case 'profile':
            // Profile data is loaded in loadDashboardData
            break;
    }
}

// Sidebar toggle (mobil)
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay') || createSidebarOverlay();
    
    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('show');
        overlay.classList.toggle('show');
        document.body.style.overflow = sidebar.classList.contains('show') ? 'hidden' : '';
    }
}

// Create sidebar overlay for mobile
function createSidebarOverlay() {
    let overlay = document.querySelector('.sidebar-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', closeMobileSidebar);
        document.body.appendChild(overlay);
    }
    return overlay;
}

// Close mobile sidebar
function closeMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebar) sidebar.classList.remove('show');
    if (overlay) overlay.classList.remove('show');
    document.body.style.overflow = '';
}

// User menu toggle
function toggleUserMenu() {
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

// Register form toggle (for future use)
function showRegisterForm() {
    showToast('Kayıt özelliği yakında eklenecek!', 'info');
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

// ========================================
// MODAL MANAGEMENT
// ========================================

// Show modal
function showModal(modalId) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById(modalId);
    
    if (overlay && modal) {
        overlay.classList.remove('hidden');
        
        // Force reflow for animation
        overlay.offsetHeight;
        overlay.classList.add('show');
        
        // Hide all modals first
        overlay.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
        
        // Show target modal
        modal.style.display = 'block';
        
        // Prevent body scrolling
        document.body.style.overflow = 'hidden';
        
        // Focus first input
        const firstInput = modal.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        console.log('✅ Modal opened:', modalId);
    }
}

// Close modal
function closeModal() {
    const overlay = document.getElementById('modal-overlay');
    
    if (overlay) {
        overlay.classList.remove('show');
        
        setTimeout(() => {
            overlay.classList.add('hidden');
            // Hide all modals
            overlay.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
            
            // Restore body scrolling
            document.body.style.overflow = '';
            
            // Clear form data
            overlay.querySelectorAll('form').forEach(form => form.reset());
        }, 300);
        
        console.log('✅ Modal closed');
    }
}

// Modal-specific show functions
function showAddWalletModal() {
    showModal('add-wallet-modal');
}

function showAddApiKeyModal() {
    showModal('add-api-key-modal');
}

// Keyboard support for modals
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const overlay = document.getElementById('modal-overlay');
        if (overlay && !overlay.classList.contains('hidden')) {
            closeModal();
        }
    }
});

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Panoya kopyalandı!', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

// Fallback copy function
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showToast('Panoya kopyalandı!', 'success');
    } catch (err) {
        showToast('Kopyalama başarısız!', 'error');
    }
    
    document.body.removeChild(textArea);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format amount
function formatAmount(amount, currency = 'USDT') {
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount)) return '0 ' + currency;
    
    return numAmount.toLocaleString('tr-TR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 6
    }) + ' ' + currency;
}

// Truncate text
function truncateText(text, maxLength = 30) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ========================================
// DATA RENDERING FUNCTIONS
// ========================================

// Render payment list item
function renderPaymentListItem(payment) {
    return `
        <div class="payment-item" style="padding: 16px 24px; border-bottom: 1px solid var(--gray-200); display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-weight: 600; color: var(--gray-900); margin-bottom: 4px;">
                    ${formatAmount(payment.amount)}
                </div>
                <div style="font-size: 0.875rem; color: var(--gray-600);">
                    ${truncateText(payment.order_id, 20)}
                </div>
            </div>
            <div style="text-align: right;">
                <div class="status-badge status-${payment.status}" style="margin-bottom: 4px;">
                    ${getStatusText(payment.status)}
                </div>
                <div style="font-size: 0.8rem; color: var(--gray-500);">
                    ${formatDate(payment.created_at)}
                </div>
            </div>
        </div>
    `;
}

// Get status text
function getStatusText(status) {
    const statusTexts = {
        'pending': 'Bekliyor',
        'confirmed': 'Onaylandı', 
        'expired': 'Süresi Doldu',
        'cancelled': 'İptal'
    };
    return statusTexts[status] || status;
}

// Ödeme detaylarını görüntüleme
function viewPayment(paymentId) {
    // Bu fonksiyon geliştirilecek
    showToast('Ödeme detayları özelliği yakında eklenecek!', 'info');
} 