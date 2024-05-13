# AITask

Wasserstoff AI Fullstack Developer task.

## Description

This is a WordPress plugin which adds an AI chatbot to your website. The AI chatbot uses Retrieval Augmented Generation (RAG) to fetch the contents of your website and respond based on it, which means users can ask the assistant anything about the contents of your website and the chatbot will be able to answer them.

<img src="https://i.ibb.co/LSyHyNG/frontend.png" title="Assistant Frontend" alt="frontend.png">

## How to use

### Running the Python Backend

1. Clone the repository and move into it.
    ```sh
    git clone https://github.com/ZenithFlux/AITask.git
    cd AITask
    ```

2. Install the required dependencies.
    ```sh
    pip install -r requirements.txt
    ```

3. Set all the environment variables mentioned in `.env.template` file. You can also rename it to `.env` and put the values in it.

    An important variable here is `AUTH_KEY=<Backend-API-Key>`. This key will be needed whenever we want to communicate with the backend.

3. Run the Flask server.
    ```sh
    flask run
    ```

The backend will run at the URL `http://127.0.0.1:5000`. For rest of the README, we will assume this to be the URL of the Python backend.

**Note:** If your backend server is running at a different URL, change the value of the static variable `$ASSISTANT_URL` accordingly in the `wordpress_plugin/wordpress-site-assistant/wordpress-site-assistant.php` file.

### Building the Database

First, to use the Assistant on your website, you must build a database of the contents of your website. Assistant will use this data to generate responses specific to your site. Your website must be a WordPress site.

To do this, send a POST request to `http://127.0.0.1:5000/db` with the following structure:
```http
Authorization: Bearer <Backend-API-Key>
Content-Type: application/json

{
    "site_url": "https://www.yoursite.com",
    "create_if_not_present": true
}
```
You can use a tool like **Postman** or **cURL** for this.

The server will automatically create a database for **yoursite.com**. After this, you will be able to use the AI Assistant on this site.

### Installing the plugin

1. Copy the `wordpress_plugin/wordpress-site-assistant` directory into the `wp-content/plugins` folder of your WordPress website.
2. Add the following line to your `wp-config.php` file or wherever you store the secrets for your WordPress site.
    ```php
    define( 'WORDPRESS_SITE_ASSISTANT_API_KEY', '<Backend-API-Key>' );
    ```
3. Open your WordPress Dashboard > Click on Plugins > Activate the **Wordpress Site Assistant** plugin.
4. Go to your Pages list. You will see that a **Wordpress Site Assistant** page has appeared there. This is where your users can chat with the AI Assistant.

Congratulations, you have now successfully added the **WordPress Site Assistant** to your website.
