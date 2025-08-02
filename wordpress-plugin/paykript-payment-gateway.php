<?php
/**
 * Plugin Name: PayKript Ödeme Geçidi
 * Plugin URI: https://paykript.com
 * Description: TRON (TRC-20) ağında USDT ile kripto ödeme alma. Güvenli, non-custodial ve düşük komisyonlu.
 * Version: 1.0.0
 * Author: PayKript Team
 * License: MIT
 * Text Domain: paykript
 * Domain Path: /languages
 * Requires at least: 5.0
 * Tested up to: 6.4
 * WC requires at least: 5.0
 * WC tested up to: 8.4
 */

// Güvenlik kontrolü
if (!defined('ABSPATH')) {
    exit;
}

// WooCommerce varlığını kontrol et
add_action('plugins_loaded', 'paykript_init', 11);

function paykript_init() {
    if (!class_exists('WC_Payment_Gateway')) {
        add_action('admin_notices', 'paykript_missing_wc_notice');
        return;
    }
    
    // Ödeme geçidini yükle
    require_once plugin_dir_path(__FILE__) . 'includes/class-wc-gateway-paykript.php';
    
    // WooCommerce'e ödeme geçidini ekle
    add_filter('woocommerce_payment_gateways', 'paykript_add_gateway_class');
}

function paykript_missing_wc_notice() {
    echo '<div class="error"><p><strong>' . 
         esc_html__('PayKript eklentisi WooCommerce gerektirir. Lütfen WooCommerce\'i yükleyip aktifleştirin.', 'paykript') . 
         '</strong></p></div>';
}

function paykript_add_gateway_class($gateways) {
    $gateways[] = 'WC_Gateway_PayKript';
    return $gateways;
}

// Webhook endpoint'i oluştur
add_action('rest_api_init', function () {
    register_rest_route('paykript/v1', '/webhook', array(
        'methods' => 'POST',
        'callback' => 'paykript_handle_webhook',
        'permission_callback' => '__return_true'
    ));
});

function paykript_handle_webhook($request) {
    $body = $request->get_body();
    $signature = $request->get_header('X-PayKript-Signature');
    
    // Webhook secret'ını al
    $gateway = new WC_Gateway_PayKript();
    $webhook_secret = $gateway->get_option('webhook_secret');
    
    if (!$webhook_secret) {
        return new WP_Error('no_webhook_secret', 'Webhook secret tanımlanmamış', ['status' => 400]);
    }
    
    // Signature doğrulama
    $expected_signature = 'sha256=' . hash_hmac('sha256', $body, $webhook_secret);
    
    if (!hash_equals($signature, $expected_signature)) {
        return new WP_Error('invalid_signature', 'Geçersiz imza', ['status' => 401]);
    }
    
    // Webhook verilerini parse et
    $data = json_decode($body, true);
    
    if (!$data || !isset($data['event'])) {
        return new WP_Error('invalid_data', 'Geçersiz webhook verisi', ['status' => 400]);
    }
    
    // Ödeme onaylandı
    if ($data['event'] === 'payment.confirmed') {
        $order_id = sanitize_text_field($data['data']['order_id']);
        $order = wc_get_order($order_id);
        
        if (!$order) {
            return new WP_Error('order_not_found', 'Sipariş bulunamadı', ['status' => 404]);
        }
        
        // Ödemeyi tamamla
        $tx_hash = sanitize_text_field($data['data']['transaction']['tx_hash']);
        $amount = sanitize_text_field($data['data']['amount']);
        
        $order->payment_complete($tx_hash);
        $order->add_order_note(
            sprintf(
                __('USDT ödemesi onaylandı. İşlem Hash: %s, Miktar: %s USDT', 'paykript'),
                $tx_hash,
                $amount
            )
        );
        
        // Log kaydı
        error_log("PayKript: Ödeme onaylandı - Sipariş: {$order_id}, TX: {$tx_hash}");
    }
    
    return ['status' => 'success'];
}

// Plugin aktivasyonu
register_activation_hook(__FILE__, 'paykript_activate');

function paykript_activate() {
    // Webhook endpoint'ini flush et
    flush_rewrite_rules();
}

// Plugin deaktivasyonu
register_deactivation_hook(__FILE__, 'paykript_deactivate');

function paykript_deactivate() {
    flush_rewrite_rules();
}

// Admin script ve style'ları ekle
add_action('admin_enqueue_scripts', 'paykript_admin_scripts');

function paykript_admin_scripts() {
    if (isset($_GET['page']) && $_GET['page'] === 'wc-settings' && 
        isset($_GET['tab']) && $_GET['tab'] === 'checkout' &&
        isset($_GET['section']) && $_GET['section'] === 'paykript') {
        
        wp_enqueue_script(
            'paykript-admin',
            plugin_dir_url(__FILE__) . 'assets/admin.js',
            ['jquery'],
            '1.0.0',
            true
        );
        
        wp_enqueue_style(
            'paykript-admin',
            plugin_dir_url(__FILE__) . 'assets/admin.css',
            [],
            '1.0.0'
        );
    }
}

// Frontend script ve style'ları ekle
add_action('wp_enqueue_scripts', 'paykript_frontend_scripts');

function paykript_frontend_scripts() {
    if (is_checkout()) {
        wp_enqueue_script(
            'paykript-checkout',
            plugin_dir_url(__FILE__) . 'assets/checkout.js',
            ['jquery'],
            '1.0.0',
            true
        );
        
        wp_enqueue_style(
            'paykript-checkout',
            plugin_dir_url(__FILE__) . 'assets/checkout.css',
            [],
            '1.0.0'
        );
        
        // AJAX endpoint'i
        wp_localize_script('paykript-checkout', 'paykript_ajax', [
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('paykript_nonce'),
            'check_payment_text' => __('Ödeme kontrol ediliyor...', 'paykript'),
            'payment_confirmed_text' => __('Ödeme onaylandı! Yönlendiriliyorsunuz...', 'paykript'),
            'payment_expired_text' => __('Ödeme süresi doldu. Lütfen tekrar deneyin.', 'paykript')
        ]);
    }
}

// AJAX: Ödeme durumu kontrolü
add_action('wp_ajax_paykript_check_payment', 'paykript_check_payment_status');
add_action('wp_ajax_nopriv_paykript_check_payment', 'paykript_check_payment_status');

function paykript_check_payment_status() {
    check_ajax_referer('paykript_nonce', 'nonce');
    
    $order_id = intval($_POST['order_id']);
    $payment_id = intval($_POST['payment_id']);
    
    if (!$order_id || !$payment_id) {
        wp_die('Geçersiz parametreler');
    }
    
    $order = wc_get_order($order_id);
    if (!$order) {
        wp_die('Sipariş bulunamadı');
    }
    
    // PayKript API'den ödeme durumunu kontrol et
    $gateway = new WC_Gateway_PayKript();
    $payment_status = $gateway->check_payment_status($payment_id, $order_id);
    
    wp_send_json($payment_status);
}

// Çeviri dosyalarını yükle
add_action('plugins_loaded', 'paykript_load_textdomain');

function paykript_load_textdomain() {
    load_plugin_textdomain('paykript', false, dirname(plugin_basename(__FILE__)) . '/languages/');
}

// Uninstall hook
register_uninstall_hook(__FILE__, 'paykript_uninstall');

function paykript_uninstall() {
    // Eklenti verileri silinebilir (isteğe bağlı)
    delete_option('woocommerce_paykript_settings');
}

// AJAX handlers
add_action('wp_ajax_paykript_check_payment', 'paykript_ajax_check_payment');
add_action('wp_ajax_nopriv_paykript_check_payment', 'paykript_ajax_check_payment');

function paykript_ajax_check_payment() {
    // Nonce kontrolü
    check_ajax_referer('paykript_check_payment', 'nonce');
    
    $order_id = intval($_POST['order_id']);
    $payment_id = intval($_POST['payment_id']);
    
    $order = wc_get_order($order_id);
    if (!$order) {
        wp_send_json_error('Sipariş bulunamadı');
        return;
    }
    
    // PayKript API'den ödeme durumunu kontrol et
    $gateway = new WC_Gateway_PayKript();
    $payment_status = $gateway->check_payment_status($payment_id, $order_id);
    
    wp_send_json($payment_status);
} 