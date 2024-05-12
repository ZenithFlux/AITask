<?php
/**
 * Plugin Name: WordPress Site Assistant
 * Description: Adds an AI Assistant to your site.
 * Version: 1.0.0
 * Author: Chaitanya Lakhchaura
 * Text Domain: wordpress-site-assistant
 */

// Exit if accessed directly.
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class WordPress_Site_Assistant {

    static $ASSISTANT_URL = 'http://127.0.0.1:5000/';

    public function __construct() {
        register_activation_hook( __FILE__, [ $this, 'activate_plugin' ] );
        register_deactivation_hook( __FILE__, [ $this, 'deactivate_plugin' ] );
        add_filter( 'theme_page_templates', [ $this, 'add_template' ] );
        add_filter( 'template_include' , [ $this, 'template_path' ] );
        add_action( 'wp_enqueue_scripts', [ $this, 'load_assets' ] );

        // Ajax requests
        add_action("wp_ajax_call_assistant", [ $this, 'send_conversation_to_llm' ]);
        add_action("wp_ajax_delete_conversation", [ $this, 'delete_conversation' ]);
    }

    public static function check_key_exists() {
        if ( ! defined("WORDPRESS_SITE_ASSISTANT_API_KEY") ) {
            wp_die("WORDPRESS_SITE_ASSISTANT_API_KEY not defined!");
        }
    }

    public function activate_plugin() {
        self::check_key_exists();
        $res = wp_remote_post(self::$ASSISTANT_URL . 'db', [
            'timeout' => 30,
            'headers' => [
                'Authorization' => 'Bearer ' . WORDPRESS_SITE_ASSISTANT_API_KEY,
                'Content-Type' => 'application/json',
            ],
            'body' => wp_json_encode([ 'site_url' => home_url() ]),
        ]);
        if ( is_wp_error($res) ) {
            wp_die('Unable to connect to the Assistant server');
        }
        $res_code = $res['response']['code'];
        if ($res_code === 401) {
            wp_die("Wrong WORDPRESS_SITE_ASSISTANT_API_KEY!");
        }
        if ( $res_code !== 200 ){
            error_log("HTTP {$res_code}: {$res['response']['message']}");
            wp_die('Request to the Assistant server was unsuccessful');
        }
        $res = json_decode($res['body'], true);
        update_option('assistant_db_exists', $res["database_present"], false);
        wp_insert_post(
            array(
                'post_title' => 'WordPress Site Assistant',
                'post_name' => 'wordpress-site-assistant',
                'post_status' => 'publish',
                'post_type' => 'page',
                'page_template' => 'blank',
            )
        );
    }


    public function deactivate_plugin() {
        $user_ids = get_users([ 'fields' => 'ID' ]);
        foreach ($user_ids as $user_id) {
            delete_user_meta($user_id, 'llm_chat');
            delete_user_meta($user_id, 'assistant_chat');
        }
        $page = new WP_Query( [ 'pagename' => 'wordpress-site-assistant' ] );
        wp_delete_post( $page->post->ID, true );
        delete_option('assistant_db_exists');
    }


    public function add_template( $page_templates ) {
        $page_templates['blank'] = 'Blank';
        return $page_templates;
    }


    public function template_path( $template ) {
        if ( ! is_page_template( 'blank' )) {
            return $template;
        }
        return plugin_dir_path( __FILE__ ) . 'templates/blank.php';
    }


    public function send_conversation_to_llm() {
        check_ajax_referer('assistant_chat');
        self::check_key_exists();
        $user_id = get_current_user_id();
        $llm_chat = get_user_meta($user_id, 'llm_chat', true);
        $assistant_chat = get_user_meta($user_id, 'assistant_chat', true);
        $llm_chat[] = [ 'role' => 'user', 'content' => wp_unslash($_POST['user_msg']) ];
        $assistant_chat[] = end($llm_chat);
        $res = wp_remote_post(self::$ASSISTANT_URL . 'chat', [
            'timeout' => 30,
            'headers' => [
                'Authorization' => 'Bearer ' . WORDPRESS_SITE_ASSISTANT_API_KEY,
                'Content-Type' => 'application/json',
            ],
            'body' => wp_json_encode([
                'site_url' => home_url(),
                'messages' => $llm_chat,
            ]),
        ]);
        if ( is_wp_error($res) ) {
            wp_die("Unable to connect to the Assistant server");
        }
        $res_code = $res['response']['code'];
        if ($res_code === 401) {
            wp_die("Wrong WORDPRESS_SITE_ASSISTANT_API_KEY!");
        }
        if ($res_code !== 200) {
            error_log($res['body']);
            wp_die('Request to the Assistant server was unsuccessful');
            return;
        }
        $llm_chat = json_decode($res['body'], true);
        $assistant_chat[] = end($llm_chat);
        update_user_meta($user_id, 'llm_chat', $llm_chat);
        update_user_meta($user_id, 'assistant_chat', $assistant_chat);
        wp_die(end($assistant_chat)['content']);
    }


    public function delete_conversation() {
        check_ajax_referer('assistant_chat');
        $user_id = get_current_user_id();
        delete_user_meta($user_id, 'llm_chat');
        delete_user_meta($user_id, 'assistant_chat');
        wp_die();
    }


    public function load_assets() {
        if ( ! is_page('wordpress-site-assistant') ) {
            return;
        }
        add_action( 'wp_body_open', [ $this, 'page_body'] );
        if ( ! is_user_logged_in() || ! get_option('assistant_db_exists') ) {
            return;
        }
        wp_enqueue_style(
            'assistant-css',
            plugins_url('style.css', __FILE__),
            [],
            1,
            'all'
        );
        wp_enqueue_script(
            'assistant-js',
            plugins_url('script.js', __FILE__),
            [ 'jquery' ],
            1,
            [ 'in_footer' => true ],
        );
        wp_localize_script(
            'assistant-js',
            'ajax_obj',
            [ 'url' => admin_url('admin-ajax.php'), 'nonce' => wp_create_nonce('assistant_chat') ]
        );
    }


    public function page_body() {
        if ( ! is_user_logged_in() ) {
            echo '<h2> Must be logged in to use the assistant </h2>';
            return;
        }
        if ( ! get_option('assistant_db_exists') ) {
            echo '<h2> Assistant database has not yet been created for this site </h2>';
            return;
        }
        $user_id = get_current_user_id();
        if ( ! metadata_exists( 'user', $user_id, 'assistant_chat') ) {
            add_user_meta( $user_id, 'assistant_chat', [
                [ 'role' => 'assistant', 'content' => 'Hey, how can I help you?' ],
            ], true);
        }
        if ( ! metadata_exists( 'user', $user_id, 'llm_chat') ) {
            $system_msg = [
                'role' => 'system',
                'content' => 'You are an AI assistant who helps users to '
                            .'get information from the current website.'
                            .'Keep your responses concise unless asked for '
                            .'longer explanations.'
            ];
            $assistant_chat = get_user_meta($user_id, 'assistant_chat', true);
            add_user_meta( $user_id, 'llm_chat', array_merge([ $system_msg ], $assistant_chat ), true);
        }

        $assistant_chat = get_user_meta($user_id, 'assistant_chat', true);
        ?>
            <div class="chat-container">
                <button class="delete-conversation-btn">Delete Conversation</button>
                <h1 class="chat-title">WordPress Site Assistant</h1>
                <div class="chat-box">
                    <?php foreach ($assistant_chat as $msg): ?>
                        <div class="chat-message">
                        <span class="message-sender"><?= ucfirst($msg['role'])?>:</span>
                        <span class="message-text"><?= $msg['content']?></span>
                        </div>
                    <?php endforeach; ?>
                </div>
                <form class="chat-input">
                    <input type="text" placeholder="Type your message...">
                    <button type="submit">Send</button>
                </form>
            </div>
        <?php
    }
}


new WordPress_Site_Assistant();
