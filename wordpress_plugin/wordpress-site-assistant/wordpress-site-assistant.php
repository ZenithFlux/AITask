<?php
/**
 * Plugin Name: WordPress Site Assistant
 * Description: Adds AI Chat Assistant for your site.
 * Version: 1.0.0
 * Author: Chaitanya Lakhchaura
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: wordpress-site-assistant
 */

// Exit if accessed directly.
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class WordPress_Site_Assistant {

    public function __construct() {
        register_activation_hook( __FILE__, array( $this, 'activate_plugin' ) );
        register_deactivation_hook( __FILE__, array( $this, 'deactivate_plugin' ) );
        add_action( 'init', array( $this, 'init_plugin' ));
        add_filter( 'theme_page_templates', array( $this, 'add_template' ) );
        add_filter( 'template_include' , array( $this, 'set_template' ) );
    }


    public function add_template( $page_templates ) {
        $page_templates['blank'] = 'Blank';
        return $page_templates;
    }


    public function activate_plugin() {
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
        $page = new WP_Query( array( 'pagename' => 'wordpress-site-assistant' ) );
        wp_delete_post( $page->post->ID );
    }


    public function init_plugin() {
        add_action( 'admin_menu', array( $this, 'add_admin_menu' ) );
        add_action( 'wp_enqueue_scripts', array( $this, 'enqueue_frontend_scripts' ) );
    }


    public function set_template( $template ) {
        if ( ! is_page( 'wordpress-site-assistant' )) {
            return $template;
        }
        return plugin_dir_path( __FILE__ ) . 'templates/blank.html';
    }


    public function add_admin_menu() {
        // Add menu items here.
    }

    public function enqueue_frontend_scripts() {
        // Enqueue scripts here.
    }

    public function send_conversation_to_api() {
        // Placeholder function. Send conversation history to API and append response.
    }

    public function display_chat_interface() {
        ?>
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Chat Application</title>
                <link rel="stylesheet" href="styles.css">
            </head>
            <body>
                <div class="chat-container">
                    <div class="chat-box">
                        <div class="chat-message">
                            <span class="message-sender">John:</span>
                            <span class="message-text">Hey, how are you?</span>
                        </div>
                        <div class="chat-message">
                            <span class="message-sender">Jane:</span>
                            <span class="message-text">I'm good, thanks for asking!</span>
                        </div>
                        <!-- More chat messages can be added here -->
                    </div>
                    <div class="chat-input">
                        <input type="text" placeholder="Type your message...">
                        <button>Send</button>
                    </div>
                </div>
            </body>
            </html>
        <?php
    }


    public function load_assets() {
        wp_enqueue_style(
            'wordpress-site-assistant',
            plugin_dir_url(__FILE__) . 'style.css',
            array(),
            1,
            'all'
        );

    }
}

// Initialize the plugin.
new WordPress_Site_Assistant();
