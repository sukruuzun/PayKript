// PayKript Payment Status Check Script

jQuery(document).ready(function($) {
    // Ödeme durumu kontrol değişkenleri
    var paymentId = paykript_payment_data.payment_id;
    var orderId = paykript_payment_data.order_id;
    var paymentStatus = paykript_payment_data.payment_status;
    var timeRemaining = paykript_payment_data.time_remaining;
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
                $('#time-remaining').text(paykript_payment_data.time_expired_text);
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
            url: paykript_payment_data.ajax_url,
            type: 'POST',
            data: {
                action: 'paykript_check_payment',
                order_id: orderId,
                payment_id: paymentId,
                nonce: paykript_payment_data.nonce
            },
            success: function(response) {
                if (response.success && response.data) {
                    var data = response.data;
                    if (data.payment_status === 'confirmed') {
                        clearInterval(checkInterval);
                        clearInterval(countdownInterval);
                        
                        $('#status-text').text(paykript_payment_data.payment_confirmed_text);
                        
                        setTimeout(function() {
                            location.reload();
                        }, 2000);
                    }
                }
            },
            error: function() {
                console.log('Ödeme durumu kontrol edilemedi');
            }
        });
    }
    
    // Manuel kontrol butonu
    $('#check-payment-btn').click(function() {
        $(this).prop('disabled', true).text(paykript_payment_data.check_payment_text);
        
        checkPaymentStatus();
        
        setTimeout(function() {
            $('#check-payment-btn').prop('disabled', false).text(paykript_payment_data.check_payment_btn_text);
        }, 3000);
    });
    
    // Fonksiyonları başlat
    if (paymentStatus === 'pending' && timeRemaining > 0) {
        startPaymentCheck();
        startCountdown();
    }
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
    button.textContent = paykript_payment_data.copied_text;
    button.style.background = '#4CAF50';
    
    setTimeout(function() {
        button.textContent = originalText;
        button.style.background = '';
    }, 2000);
} 