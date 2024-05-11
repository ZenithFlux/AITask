const $ = jQuery;


window.onload = () => {
    let chat_box = document.querySelector(".chat-box");
    chat_box.scrollTop = chat_box.scrollHeight;
}


function add_new_msg(sender, message) {
    sender = sender[0].toUpperCase() + sender.slice(1);
    const msg_div = `<div class="chat-message">`
        + `<span class="message-sender">${sender}:</span>`
        + `<span class="message-text">${message}</span>`
        + `</div>`;
    const chat_box = $(".chat-box");
    chat_box.append(msg_div);
    chat_box.scrollTop(chat_box.prop("scrollHeight"));
}


$(document).ready(() => {
    $(".chat-input").submit( e => {
        e.preventDefault();
        const user_msg = $(".chat-input input").val().trim();
        if (user_msg === "") return;
        add_new_msg("user", user_msg);
        $(".chat-input input").val("");
        $.post(ajax_obj.url, {
            _ajax_nonce: ajax_obj.nonce,
            action: "call_assistant",
            user_msg: user_msg,
        }, (data) => add_new_msg("assistant", data));
    });

    $(".delete-conversation-btn").click(() => {
        $.post(ajax_obj.url, {
            _ajax_nonce: ajax_obj.nonce,
            action: "delete_conversation",
        }, () => location.reload());
    });
});
