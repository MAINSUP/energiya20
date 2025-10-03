<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $name    = trim($_POST['name']);
    $email   = trim($_POST['email']);
    $mobile  = trim($_POST['mobile']);
    $service = trim($_POST['service']);
    $note    = trim($_POST['note']);

    $errors = [];

    if (empty($name)) $errors[] = "Name is required";
    if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) $errors[] = "Valid email is required";
    if (empty($service)) $errors[] = "Please select a service";

    if (empty($errors)) {
        $to = "vmail@energiya20.com";  // change to your email
        $subject = "New Quote Request - " . ucfirst($service);
        $body = "Name: $name\nEmail: $email\nMobile: $mobile\nService: $service\nNote:\n$note";

        if (mail($to, $subject, $body, "From: $email")) {
            echo "✅ Thank you, your request has been sent.";
        } else {
            echo "❌ Sorry, message could not be sent.";
        }
    } else {
        echo "⚠️ Errors: " . implode(", ", $errors);
    }
}
?>
