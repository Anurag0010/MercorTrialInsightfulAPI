from email.message import Message
import os
from .email_sender import EmailSender

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = os.getenv('SMTP_PORT')
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.email_sender = EmailSender(self.smtp_server, self.smtp_port, self.smtp_user, self.smtp_password, self.use_tls)    
        
    def send_activation_email(self, user_email, activation_url):
        # Create the HTML part with a clickable link
        html_body = f"""
        <html>
        <body>
            <p>Hello,</p>
            <p>Welcome to MercorInsightful.com. Click the link below to activate your account:</p>
            <p><a href="{activation_url}">Activate Account</a></p>
            <p>If the link doesn’t work, copy and paste this URL into your browser:</p>
            <p>{activation_url}</p>
        </body>
        </html>
        """        
        self.email_sender.send_email(email_message=html_body,
                                     email_from=self.smtp_user,
                                     email_subject="MercorInsightful: Activate your account",
                                     email_to=[user_email],
                                     is_html=True)
    
    def send_reset_pwd_email(self, user_email, reset_link):
        # Create the HTML part with a clickable link
        html_body = f"""
        <html>
        <body>
            <p>Hello,</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_link}">Activate Account</a></p>
            <p>If the link doesn’t work, copy and paste this URL into your browser:</p>
            <p>{reset_link}</p>
        </body>
        </html>
        """
        self.email_sender.send_email(email_message=html_body,
                                     email_from=self.smtp_user,
                                     email_subject="MercorInsightful: Reset your password",
                                     email_to=[user_email],
                                     is_html=True)
       