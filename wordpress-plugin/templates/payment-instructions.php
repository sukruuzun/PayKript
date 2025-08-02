<?php
/**
 * PayKript Ödeme Talimatları Template
 */

if (!defined('ABSPATH')) {
    exit;
}

// PayKript API'den QR kodu al
$gateway = new WC_Gateway_PayKript();
$qr_response = wp_remote_get(
    rtrim($gateway->api_url, '/') . '/odemeler/qr/' . $payment_id,
    array(
        'headers' => array(
            'Authorization' => 'Bearer ' . $gateway->api_key . ':' . $gateway->secret_key
        )
    )
);

$qr_data = '';
if (!is_wp_error($qr_response) && wp_remote_retrieve_response_code($qr_response) === 200) {
    $qr_body = json_decode(wp_remote_retrieve_body($qr_response), true);
    $qr_data = $qr_body['qr_code'] ?? '';
}

$current_time = current_time('timestamp');
$expires_timestamp = strtotime($expires_at);
$time_remaining = $expires_timestamp - $current_time;
?>

<div class="paykript-payment-container">
    <div class="paykript-payment-header">
        <h3><?php _e('USDT ile Ödeme Talimatları', 'paykript'); ?></h3>
        <p><?php _e('Aşağıdaki adrese belirtilen miktarda USDT gönderin:', 'paykript'); ?></p>
    </div>

    <?php if ($payment_status['payment_status'] === 'confirmed'): ?>
        <div class="paykript-payment-success">
            <div class="success-icon">✅</div>
            <h4><?php _e('Ödeme Onaylandı!', 'paykript'); ?></h4>
            <p><?php _e('USDT ödemeniz başarıyla alındı ve siparişiniz işleme alındı.', 'paykript'); ?></p>
            <?php if (isset($payment_status['confirmed_at'])): ?>
                <p><small><?php printf(__('Onay zamanı: %s', 'paykript'), date_i18n(get_option('date_format') . ' ' . get_option('time_format'), strtotime($payment_status['confirmed_at']))); ?></small></p>
            <?php endif; ?>
        </div>

    <?php elseif ($time_remaining <= 0): ?>
        <div class="paykript-payment-expired">
            <div class="error-icon">⏰</div>
            <h4><?php _e('Ödeme Süresi Doldu', 'paykript'); ?></h4>
            <p><?php _e('Bu ödeme talalebinin süresi dolmuş. Lütfen yeni bir sipariş oluşturun.', 'paykript'); ?></p>
            <a href="<?php echo esc_url(wc_get_checkout_url()); ?>" class="button">
                <?php _e('Yeni Sipariş Ver', 'paykript'); ?>
            </a>
        </div>

    <?php else: ?>
        <div class="paykript-payment-pending">
            <div class="payment-info-grid">
                <div class="payment-qr">
                    <h4><?php _e('QR Kod ile Öde', 'paykript'); ?></h4>
                    <?php if ($qr_data): ?>
                        <div class="qr-code-container">
                            <img src="<?php echo esc_attr($qr_data); ?>" alt="<?php _e('Ödeme QR Kodu', 'paykript'); ?>" class="qr-code-image">
                        </div>
                        <p class="qr-instructions">
                            <?php _e('TronLink veya uyumlu bir cüzdan uygulamasında bu QR kodu tarayın', 'paykript'); ?>
                        </p>
                    <?php else: ?>
                        <div class="qr-placeholder">
                            <p><?php _e('QR kod yüklenemedi. Manuel ödeme yapabilirsiniz.', 'paykript'); ?></p>
                        </div>
                    <?php endif; ?>
                </div>

                <div class="payment-details">
                    <h4><?php _e('Manuel Ödeme Bilgileri', 'paykript'); ?></h4>
                    
                    <div class="payment-field">
                        <label><?php _e('Ödeme Adresi:', 'paykript'); ?></label>
                        <div class="address-container">
                            <code class="payment-address" id="payment-address"><?php echo esc_html($payment_address); ?></code>
                            <button type="button" class="copy-button" onclick="copyToClipboard('payment-address')">
                                <?php _e('Kopyala', 'paykript'); ?>
                            </button>
                        </div>
                    </div>

                    <div class="payment-field">
                        <label><?php _e('Ödeme Miktarı:', 'paykript'); ?></label>
                        <div class="amount-container">
                            <span class="payment-amount"><?php echo esc_html($amount); ?> USDT</span>
                        </div>
                    </div>

                    <div class="payment-field">
                        <label><?php _e('Ağ:', 'paykript'); ?></label>
                        <span class="network-info">TRON (TRC-20)</span>
                    </div>

                    <div class="payment-field">  
                        <label><?php _e('Kalan Süre:', 'paykript'); ?></label>
                        <div class="countdown-timer" id="countdown-timer" data-expires="<?php echo esc_attr($expires_timestamp); ?>">
                            <span id="time-remaining"><?php echo gmdate('i:s', $time_remaining); ?></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="payment-status-checker">
                <div class="status-indicator">
                    <div class="spinner"></div>
                    <span id="status-text"><?php _e('Ödeme kontrol ediliyor...', 'paykript'); ?></span>
                </div>
                
                <div class="manual-check">
                    <button type="button" id="check-payment-btn" class="button">
                        <?php _e('Ödeme Durumunu Kontrol Et', 'paykript'); ?>
                    </button>
                </div>
            </div>

            <div class="payment-instructions">
                <h4><?php _e('Ödeme Talimatları', 'paykript'); ?></h4>
                <ol>
                    <li><?php _e('TronLink, Trust Wallet veya TRON destekli herhangi bir cüzdan açın', 'paykript'); ?></li>
                    <li><?php _e('USDT (TRC-20) transferi seçin', 'paykript'); ?></li>
                    <li><?php _e('Yukarıdaki adresi alıcı olarak girin veya QR kodu tarayın', 'paykript'); ?></li>
                    <li><?php printf(__('Tam olarak %s USDT gönderin', 'paykript'), '<strong>' . esc_html($amount) . '</strong>'); ?></li>
                    <li><?php _e('İşlemi onaylayın ve bekleyin', 'paykript'); ?></li>
                </ol>
                
                <div class="important-notes">
                    <h5><?php _e('Önemli Notlar:', 'paykript'); ?></h5>
                    <ul>
                        <li><?php _e('Sadece TRON (TRC-20) ağından USDT gönderin', 'paykript'); ?></li>
                        <li><?php _e('Farklı ağlardan (ERC-20, BEP-20) gönderilen fonlar kaybolabilir', 'paykript'); ?></li>
                        <li><?php _e('Tam miktarı gönderin, eksik ödemeler işlenmez', 'paykript'); ?></li>
                        <li><?php _e('Ödeme onayı genellikle 1-2 dakika sürer', 'paykript'); ?></li>
                    </ul>
                </div>
            </div>
        </div>
    <?php endif; ?>
</div>

<script type="text/javascript">
jQuery(document).ready(function($) {
    // Ödeme durumu kontrol değişkenleri
    var paymentId = <?php echo (int) $payment_id; ?>;
    var orderId = <?php echo (int) $order_id; ?>;
    var checkInterval;
    var countdownInterval;
    
    // Otomatik ödeme kontrolü başlat
    function startPaymentCheck() {
        checkInterval = setInterval(function() {
            checkPaymentStatus();
        }, 10000); // Her 10 saniyede bir kontrol et
    }
    
    // Geri sayım başlat  
    function startCountdown() {
        var expiresAt = parseInt($('#countdown-timer').data('expires'));
        
        countdownInterval = setInterval(function() {
            var now = Math.floor(Date.now() / 1000);
            var remaining = expiresAt - now;
            
            if (remaining <= 0) {
                clearInterval(countdownInterval);
                $('#time-remaining').text('<?php _e('Süre doldu', 'paykript'); ?>');
                location.reload(); // Sayfayı yenile
                return;
            }
            
            var minutes = Math.floor(remaining / 60);
            var seconds = remaining % 60;
            $('#time-remaining').text(
                String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0')
            );
        }, 1000);
    }
    
    // Ödeme durumu kontrol et
    function checkPaymentStatus() {
        $.ajax({
            url: paykript_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'paykript_check_payment',
                order_id: orderId,
                payment_id: paymentId,
                nonce: paykript_ajax.nonce
            },
            success: function(response) {
                if (response.payment_status === 'confirmed') {
                    clearInterval(checkInterval);
                    clearInterval(countdownInterval);
                    
                    $('#status-text').text('<?php _e('Ödeme onaylandı! Yönlendiriliyorsunuz...', 'paykript'); ?>');
                    
                    setTimeout(function() {
                        location.reload();
                    }, 2000);
                }
            },
            error: function() {
                console.log('Ödeme durumu kontrol edilemedi');
            }
        });
    }
    
    // Manuel kontrol butonu
    $('#check-payment-btn').click(function() {
        $(this).prop('disabled', true).text('<?php _e('Kontrol ediliyor...', 'paykript'); ?>');
        
        checkPaymentStatus();
        
        setTimeout(function() {
            $('#check-payment-btn').prop('disabled', false).text('<?php _e('Ödeme Durumunu Kontrol Et', 'paykript'); ?>');
        }, 3000);
    });
    
    // Fonksiyonları başlat
    <?php if ($payment_status['payment_status'] === 'pending' && $time_remaining > 0): ?>
    startPaymentCheck();
    startCountdown();
    <?php endif; ?>
});

// Clipboard kopyalama fonksiyonu
function copyToClipboard(elementId) {
    var element = document.getElementById(elementId);
    var textArea = document.createElement("textarea");
    textArea.value = element.textContent;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    
    // Kopyalama onayı göster
    var button = element.nextElementSibling;
    var originalText = button.textContent;
    button.textContent = '<?php _e('Kopyalandı!', 'paykript'); ?>';
    button.style.background = '#4CAF50';
    
    setTimeout(function() {
        button.textContent = originalText;
        button.style.background = '';
    }, 2000);
}
</script> 