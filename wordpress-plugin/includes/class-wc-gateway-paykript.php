<?php

if (!defined('ABSPATH')) {
    exit;
}

/**
 * PayKript WooCommerce Ödeme Geçidi
 */
class WC_Gateway_PayKript extends WC_Payment_Gateway {

    public function __construct() {
        $this->id = 'paykript';
        $this->icon = plugin_dir_url(dirname(__FILE__)) . 'assets/images/usdt-icon.png';
        $this->method_title = __('PayKript (USDT)', 'paykript');
        $this->method_description = __('TRON ağında USDT ile güvenli kripto ödeme alma. Non-custodial ve düşük komisyonlu.', 'paykript');
        
        $this->supports = array(
            'products'
        );
        
        // Ayarları yükle
        $this->init_form_fields();
        $this->init_settings();
        
        // Özellikleri ayarla
        $this->title = $this->get_option('title');
        $this->description = $this->get_option('description');
        $this->enabled = $this->get_option('enabled');
        $this->api_url = $this->get_option('api_url');
        $this->api_key = $this->get_option('api_key');
        $this->secret_key = $this->get_option('secret_key');
        $this->webhook_secret = $this->get_option('webhook_secret');
        $this->payment_timeout = $this->get_option('payment_timeout', '15');
        
        // Hooks
        add_action('woocommerce_update_options_payment_gateways_' . $this->id, array($this, 'process_admin_options'));
        add_action('wp_enqueue_scripts', array($this, 'payment_scripts'));
        add_action('woocommerce_thankyou_' . $this->id, array($this, 'thankyou_page'));
    }
    
    /**
     * Form alanlarını başlat
     */
    public function init_form_fields() {
        $this->form_fields = array(
            'enabled' => array(
                'title' => __('Etkinleştir/Devre Dışı Bırak', 'paykript'),
                'type' => 'checkbox',
                'label' => __('PayKript ödeme geçidini etkinleştir', 'paykript'),
                'default' => 'no'
            ),
            'title' => array(
                'title' => __('Başlık', 'paykript'),
                'type' => 'text',
                'description' => __('Kullanıcının checkout sırasında göreceği başlık.', 'paykript'),
                'default' => __('USDT ile Öde', 'paykript'),
                'desc_tip' => true,
            ),
            'description' => array(
                'title' => __('Açıklama', 'paykript'),
                'type' => 'textarea',
                'description' => __('Kullanıcının checkout sırasında göreceği açıklama.', 'paykript'),
                'default' => __('TRON ağında USDT ile güvenli ödeme yapın. İşlem ücreti düşük, onay süresi hızlı.', 'paykript'),
                'desc_tip' => true,
            ),
            'api_settings' => array(
                'title' => __('API Ayarları', 'paykript'),
                'type' => 'title',
                'description' => __('PayKript API bağlantı bilgileri', 'paykript'),
            ),
            'api_url' => array(
                'title' => __('API URL', 'paykript'),
                'type' => 'text',
                'description' => __('PayKript API sunucu adresi', 'paykript'),
                'default' => 'https://paykript-production.up.railway.app/api/v1',
                'desc_tip' => true,
            ),
            'api_key' => array(
                'title' => __('API Anahtarı', 'paykript'),
                'type' => 'text',
                'description' => __('PayKript panelinden aldığınız API anahtarı', 'paykript'),
                'desc_tip' => true,
            ),
            'secret_key' => array(
                'title' => __('Secret Key', 'paykript'),
                'type' => 'password',
                'description' => __('PayKript panelinden aldığınız secret key', 'paykript'),
                'desc_tip' => true,
            ),
            'webhook_secret' => array(
                'title' => __('Webhook Secret', 'paykript'),
                'type' => 'password',
                'description' => __('Webhook güvenliği için secret key', 'paykript'),
                'desc_tip' => true,
            ),
            'payment_settings' => array(
                'title' => __('Ödeme Ayarları', 'paykript'),
                'type' => 'title',
                'description' => __('Ödeme süreci ayarları', 'paykript'),
            ),
            'payment_timeout' => array(
                'title' => __('Ödeme Zaman Aşımı (Dakika)', 'paykript'),
                'type' => 'number',
                'description' => __('Ödeme için bekleme süresi', 'paykript'),
                'default' => '15',
                'custom_attributes' => array(
                    'min' => 5,
                    'max' => 60
                ),
                'desc_tip' => true,
            ),
            'test_connection' => array(
                'title' => __('API Bağlantı Testi', 'paykript'),
                'type' => 'button',
                'description' => __('API ayarlarınızı test edin', 'paykript'),
                'desc_tip' => true,
                'class' => 'button-secondary',
                'custom_attributes' => array(
                    'onclick' => 'testPayKriptConnection()'
                )
            )
        );
    }
    
    /**
     * Ödeme işlemi
     */
    public function process_payment($order_id) {
        $order = wc_get_order($order_id);
        
        if (!$order) {
            wc_add_notice(__('Sipariş bulunamadı.', 'paykript'), 'error');
            return array('result' => 'fail');
        }
        
        // PayKript API'ye ödeme talebi gönder
        $payment_data = array(
            'order_id' => $order_id,
            'amount' => $order->get_total(),
            'currency' => 'USDT',
            'webhook_url' => home_url('/wp-json/paykript/v1/webhook'),
            'customer_email' => $order->get_billing_email(),
            'customer_info' => json_encode(array(
                'name' => $order->get_billing_first_name() . ' ' . $order->get_billing_last_name(),
                'phone' => $order->get_billing_phone(),
                'address' => $order->get_billing_address_1()
            )),
            'notes' => 'WooCommerce Order #' . $order_id
        );
        
        $response = $this->create_payment_request($payment_data);
        
        if (is_wp_error($response)) {
            wc_add_notice($response->get_error_message(), 'error');
            return array('result' => 'fail');
        }
        
        // Ödeme bilgilerini order meta'ya kaydet
        $order->update_meta_data('_paykript_payment_id', $response['id']);
        $order->update_meta_data('_paykript_payment_address', $response['payment_address']);
        $order->update_meta_data('_paykript_amount', $response['amount']);
        $order->update_meta_data('_paykript_expires_at', $response['expires_at']);
        $order->save();
        
        // Order notunu ekle
        $order->add_order_note(
            sprintf(
                __('PayKript ödeme talebi oluşturuldu. Payment ID: %s, Adres: %s', 'paykript'),
                $response['id'],
                $response['payment_address']
            )
        );
        
        // Order durumunu 'pending payment' yap
        $order->update_status('pending', __('USDT ödemesi bekleniyor.', 'paykript'));
        
        // Sepeti temizle
        WC()->cart->empty_cart();
        
        // Ödeme sayfasına yönlendir
        return array(
            'result' => 'success',
            'redirect' => $this->get_return_url($order) . '&paykript_payment=1'
        );
    }
    
    /**
     * PayKript API'ye ödeme talebi gönder
     */
    private function create_payment_request($data) {
        $url = rtrim($this->api_url, '/') . '/odemeler/olustur';
        
        $args = array(
            'method' => 'POST',
            'headers' => array(
                'Content-Type' => 'application/json',
                'Authorization' => 'Bearer ' . $this->api_key . ':' . $this->secret_key
            ),
            'body' => json_encode($data),
            'timeout' => 30
        );
        
        $response = wp_remote_request($url, $args);
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', __('API bağlantı hatası: ', 'paykript') . $response->get_error_message());
        }
        
        $body = wp_remote_retrieve_body($response);
        $status_code = wp_remote_retrieve_response_code($response);
        
        if ($status_code !== 200) {
            $error_data = json_decode($body, true);
            $error_message = isset($error_data['detail']) ? $error_data['detail'] : __('Bilinmeyen API hatası', 'paykript');
            return new WP_Error('api_error', $error_message);
        }
        
        return json_decode($body, true);
    }
    
    /**
     * Ödeme durumunu kontrol et
     */
    public function check_payment_status($payment_id, $order_id) {
        $url = rtrim($this->api_url, '/') . '/odemeler/durum/' . $payment_id;
        
        $args = array(
            'method' => 'GET',
            'headers' => array(
                'Authorization' => 'Bearer ' . $this->api_key . ':' . $this->secret_key
            ),
            'timeout' => 15
        );
        
        $response = wp_remote_request($url, $args);
        
        if (is_wp_error($response)) {
            return array(
                'status' => 'error',
                'message' => $response->get_error_message()
            );
        }
        
        $body = wp_remote_retrieve_body($response);
        $status_code = wp_remote_retrieve_response_code($response);
        
        if ($status_code !== 200) {
            return array(
                'status' => 'error',
                'message' => __('Ödeme durumu alınamadı', 'paykript')
            );
        }
        
        $payment_data = json_decode($body, true);
        
        return array(
            'status' => 'success',
            'payment_status' => $payment_data['status'],
            'expires_at' => $payment_data['expires_at'],
            'confirmed_at' => $payment_data['confirmed_at']
        );
    }
    
    /**
     * Thank you sayfasında ödeme bilgilerini göster
     */
    public function thankyou_page($order_id) {
        $order = wc_get_order($order_id);
        
        if (!$order || !isset($_GET['paykript_payment'])) {
            return;
        }
        
        $payment_id = $order->get_meta('_paykript_payment_id');
        $payment_address = $order->get_meta('_paykript_payment_address');
        $amount = $order->get_meta('_paykript_amount');
        $expires_at = $order->get_meta('_paykript_expires_at');
        
        if (!$payment_id) {
            return;
        }
        
        // Ödeme durumu kontrol et
        $payment_status = $this->check_payment_status($payment_id, $order_id);
        
        include plugin_dir_path(dirname(__FILE__)) . 'templates/payment-instructions.php';
    }
    
    /**
     * Admin ayarlarında script ekle
     */
    public function admin_options() {
        echo '<h2>' . esc_html($this->get_method_title()) . '</h2>';
        echo '<table class="form-table">';
        $this->generate_settings_html();
        echo '</table>';
        
        // Test connection JavaScript
        ?>
        <script>
        function testPayKriptConnection() {
            var apiUrl = jQuery('#woocommerce_paykript_api_url').val();
            var apiKey = jQuery('#woocommerce_paykript_api_key').val();
            var secretKey = jQuery('#woocommerce_paykript_secret_key').val();
            
            if (!apiUrl || !apiKey || !secretKey) {
                alert('<?php echo esc_js(__('Lütfen tüm API bilgilerini doldurun.', 'paykript')); ?>');
                return;
            }
            
            jQuery.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'paykript_test_connection',
                    api_url: apiUrl,
                    api_key: apiKey,
                    secret_key: secretKey,
                    nonce: '<?php echo wp_create_nonce('paykript_test'); ?>'
                },
                success: function(response) {
                    if (response.success) {
                        alert('<?php echo esc_js(__('Bağlantı başarılı!', 'paykript')); ?>');
                    } else {
                        alert('<?php echo esc_js(__('Bağlantı hatası: ', 'paykript')); ?>' + response.data);
                    }
                },
                error: function() {
                    alert('<?php echo esc_js(__('Test sırasında hata oluştu.', 'paykript')); ?>');
                }
            });
        }
        </script>
        <?php
    }
    
    /**
     * Ödeme script'lerini yükle
     */
    public function payment_scripts() {
        if (!is_checkout() && !isset($_GET['paykript_payment'])) {
            return;
        }
        
        wp_enqueue_script('paykript-payment', plugin_dir_url(dirname(__FILE__)) . 'assets/payment.js', array('jquery'), '1.0.0', true);
        wp_enqueue_style('paykript-payment', plugin_dir_url(dirname(__FILE__)) . 'assets/payment.css', array(), '1.0.0');
        
        // Ödeme durum kontrolü için ayrı script (thank you sayfasında)
        if (isset($_GET['paykript_payment'])) {
            wp_enqueue_script('paykript-payment-status', plugin_dir_url(dirname(__FILE__)) . 'assets/payment-status.js', array('jquery'), '1.0.0', true);
            
            // Ödeme bilgilerini JavaScript'e geç
            global $wp_query;
            $order_id = $wp_query->get('order-received');
            if ($order_id) {
                $order = wc_get_order($order_id);
                if ($order) {
                    $payment_id = $order->get_meta('_paykript_payment_id');
                    $payment_status_data = $this->check_payment_status($payment_id, $order_id);
                    $current_time = current_time('timestamp');
                    $expires_at = $order->get_meta('_paykript_expires_at');
                    $expires_timestamp = $expires_at ? strtotime($expires_at) : 0;
                    $time_remaining = max(0, $expires_timestamp - $current_time);
                    
                    wp_localize_script('paykript-payment-status', 'paykript_payment_data', array(
                        'payment_id' => intval($payment_id),
                        'order_id' => intval($order_id),
                        'payment_status' => $payment_status_data['payment_status'] ?? 'unknown',
                        'time_remaining' => $time_remaining,
                        'ajax_url' => admin_url('admin-ajax.php'),
                        'nonce' => wp_create_nonce('paykript_check_payment'),
                        'check_payment_text' => __('Kontrol ediliyor...', 'paykript'),
                        'check_payment_btn_text' => __('Ödeme Durumunu Kontrol Et', 'paykript'),
                        'payment_confirmed_text' => __('Ödeme onaylandı! Yönlendiriliyorsunuz...', 'paykript'),
                        'time_expired_text' => __('Süre doldu', 'paykript'),
                        'copied_text' => __('Kopyalandı!', 'paykript')
                    ));
                }
            }
        }
    }
}

// AJAX test connection
add_action('wp_ajax_paykript_test_connection', 'paykript_ajax_test_connection');

function paykript_ajax_test_connection() {
    check_ajax_referer('paykript_test', 'nonce');
    
    $api_url = sanitize_text_field($_POST['api_url']);
    $api_key = sanitize_text_field($_POST['api_key']);  
    $secret_key = sanitize_text_field($_POST['secret_key']);
    
    $test_url = rtrim($api_url, '/') . '/auth/token-kontrol';
    
    $args = array(
        'method' => 'POST',
        'headers' => array(
            'Authorization' => 'Bearer ' . $api_key . ':' . $secret_key
        ),
        'timeout' => 10
    );
    
    $response = wp_remote_request($test_url, $args);
    
    if (is_wp_error($response)) {
        wp_send_json_error($response->get_error_message());
    }
    
    $status_code = wp_remote_retrieve_response_code($response);
    
    if ($status_code === 200) {
        wp_send_json_success();
    } else {
        wp_send_json_error(__('API bağlantısı başarısız. Status: ', 'paykript') . $status_code);
    }
} 