<?php
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $name    = htmlspecialchars($_POST['name']);
    $email   = htmlspecialchars($_POST['email']);
    $subject = htmlspecialchars($_POST['subject']);
    $message = htmlspecialchars($_POST['message']);

    $to      = "vmail@energiya20.com"; // change this to your email
    $headers = "From: $email\r\nReply-To: $email\r\n";
    $body    = "New message from $name\n\n".
               "Email: $email\n\n".
               "Subject: $subject\n\n".
               "Message:\n$message";

    if (mail($to, $subject, $body, $headers)) {
        echo "success";
    } else {
        echo "error";
    }
}
?>