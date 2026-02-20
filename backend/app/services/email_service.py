"""
Email service for sending notifications and alerts.
Handles email composition and delivery using Flask-Mail.
"""
from typing import List, Optional, Dict, Tuple, Union
from flask import current_app
from flask_mail import Message, Mail
from app.repositories.user_repository import UserRepository


class EmailService:
    """Service for sending emails."""
    
    @staticmethod
    def send_email(
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Tuple[Dict, int]:
        """
        Send an email.
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Plain text email body
            html: Optional HTML email body
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            
        Returns:
            Tuple of (result_dict, status_code)
        """
        try:
            # Check if mail is suppressed (for testing)
            if current_app.config.get('MAIL_SUPPRESS_SEND', False):
                print("EMAIL: Sending suppressed (testing mode)")
                return {
                    'message': 'Email sending suppressed (testing mode)',
                    'to': to,
                    'subject': subject
                }, 200
            
            # Validate email configuration
            mail_username = current_app.config.get('MAIL_USERNAME')
            mail_password = current_app.config.get('MAIL_PASSWORD')
            mail_server = current_app.config.get('MAIL_SERVER')
            mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            
            if not mail_username:
                error_msg = 'Email service not configured: MAIL_USERNAME is missing'
                print(f"EMAIL ERROR: {error_msg}")
                return {'error': error_msg}, 500
            
            if not mail_password:
                error_msg = 'Email service not configured: MAIL_PASSWORD is missing'
                print(f"EMAIL ERROR: {error_msg}")
                return {'error': error_msg}, 500
            
            if not mail_sender:
                error_msg = 'Email service not configured: MAIL_DEFAULT_SENDER is missing'
                print(f"EMAIL ERROR: {error_msg}")
                return {'error': error_msg}, 500
            
            print(f"EMAIL: Attempting to send email to {to}, subject: {subject}")
            print(f"EMAIL CONFIG: server={mail_server}, username={mail_username}, sender={mail_sender}")
            
            # Get the existing Mail instance from the app
            # Flask-Mail stores the instance in app.extensions['mail']
            mail = current_app.extensions.get('mail')
            if not mail:
                # Fallback: create new instance if not found
                print("EMAIL WARNING: Mail instance not found in app.extensions, creating new instance")
                mail = Mail(current_app)
            
            # Create message
            msg = Message(
                subject=subject,
                recipients=to if isinstance(to, list) else [to],
                body=body,
                html=html,
                sender=mail_sender,  # Explicitly set sender
                cc=cc,
                bcc=bcc
            )
            
            # Send email with error handling
            try:
                mail.send(msg)
                print(f"EMAIL SUCCESS: Email sent successfully to {to}")
                return {
                    'message': 'Email sent successfully',
                    'to': to,
                    'subject': subject
                }, 200
            except Exception as send_error:
                error_msg = f'Failed to send email via SMTP: {str(send_error)}'
                print(f"EMAIL ERROR: {error_msg}")
                print(f"EMAIL ERROR DETAILS: {type(send_error).__name__}: {send_error}")
                import traceback
                traceback.print_exc()
                return {'error': error_msg}, 500
            
        except Exception as e:
            error_msg = f'Failed to send email: {str(e)}'
            print(f"EMAIL EXCEPTION: {error_msg}")
            import traceback
            traceback.print_exc()
            return {'error': error_msg}, 500
    
    @staticmethod
    def send_alert_notification(
        alert_type: str,
        message: str,
        severity: str,
        camera_name: str,
        recipient_emails: Optional[List[str]] = None
    ) -> Tuple[Dict, int]:
        """
        Send alert notification email.
        
        Args:
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity (low/medium/high/critical)
            camera_name: Name of the camera
            recipient_emails: Optional list of email addresses. If None, sends to all admins.
            
        Returns:
            Tuple of (result_dict, status_code)
        """
        try:
            # Get recipients
            if recipient_emails is None:
                # Get all admin users
                users = UserRepository.find_all()
                recipient_emails = [user.email for user in users if user.is_admin() and user.is_active]
            
            if not recipient_emails:
                return {'error': 'No recipients found'}, 400
            
            # Determine severity color and emoji
            severity_info = {
                'critical': {'color': '#dc3545', 'emoji': '🔴', 'label': 'CRITICAL'},
                'high': {'color': '#fd7e14', 'emoji': '🟠', 'label': 'HIGH'},
                'medium': {'color': '#ffc107', 'emoji': '🟡', 'label': 'MEDIUM'},
                'low': {'color': '#28a745', 'emoji': '🟢', 'label': 'LOW'}
            }
            sev = severity_info.get(severity.lower(), severity_info['medium'])
            
            # Create email content
            subject = f"{sev['emoji']} Security Alert: {alert_type} - {camera_name}"
            
            plain_body = f"""
Security Alert Notification

Alert Type: {alert_type}
Severity: {severity.upper()}
Camera: {camera_name}
Message: {message}

Please review this alert in the Smart CCTV system.
"""
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: {sev['color']}; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .alert-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid {sev['color']}; }}
        .label {{ font-weight: bold; color: #666; }}
        .value {{ margin-bottom: 10px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{sev['emoji']} Security Alert</h1>
            <p style="margin: 0;">{sev['label']} Priority</p>
        </div>
        <div class="content">
            <div class="alert-box">
                <div class="value">
                    <span class="label">Alert Type:</span> {alert_type}
                </div>
                <div class="value">
                    <span class="label">Severity:</span> <strong style="color: {sev['color']};">{severity.upper()}</strong>
                </div>
                <div class="value">
                    <span class="label">Camera:</span> {camera_name}
                </div>
                <div class="value">
                    <span class="label">Message:</span><br>
                    {message}
                </div>
            </div>
            <p>Please review this alert in the Smart CCTV system.</p>
        </div>
        <div class="footer">
            <p>This is an automated notification from Smart CCTV System.</p>
        </div>
    </div>
</body>
</html>
"""
            
            return EmailService.send_email(
                to=recipient_emails,
                subject=subject,
                body=plain_body,
                html=html_body
            )
        except Exception as e:
            return {'error': f'Failed to send alert notification: {str(e)}'}, 500
    
    @staticmethod
    def send_welcome_email(user_email: str, username: str) -> Tuple[Dict, int]:
        """
        Send welcome email to new user.
        
        Args:
            user_email: User's email address
            username: Username
            
        Returns:
            Tuple of (result_dict, status_code)
        """
        subject = "Welcome to Smart CCTV System"
        
        plain_body = f"""
Welcome to Smart CCTV System!

Hello {username},

Your account has been successfully created. You can now log in to the system and start managing your security cameras.

Thank you for using Smart CCTV System!
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Smart CCTV System!</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            <p>Your account has been successfully created. You can now log in to the system and start managing your security cameras.</p>
            <p>Thank you for using Smart CCTV System!</p>
        </div>
        <div class="footer">
            <p>This is an automated email from Smart CCTV System.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_email(
            to=user_email,
            subject=subject,
            body=plain_body,
            html=html_body
        )
    
    @staticmethod
    def send_password_reset_email(user_email: str, reset_token: str, reset_url: str) -> Tuple[Dict, int]:
        """
        Send password reset email.
        
        Args:
            user_email: User's email address
            reset_token: Password reset token
            reset_url: URL for password reset (should include token)
            
        Returns:
            Tuple of (result_dict, status_code)
        """
        subject = "Password Reset Request - Smart CCTV System"
        
        plain_body = f"""
Password Reset Request

You have requested to reset your password for Smart CCTV System.

Click the following link to reset your password:
{reset_url}

If you did not request this password reset, please ignore this email.

This link will expire in 1 hour.
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>You have requested to reset your password for Smart CCTV System.</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #007bff;">{reset_url}</p>
            <p><strong>Note:</strong> If you did not request this password reset, please ignore this email.</p>
            <p style="color: #666; font-size: 12px;">This link will expire in 1 hour.</p>
        </div>
        <div class="footer">
            <p>This is an automated email from Smart CCTV System.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return EmailService.send_email(
            to=user_email,
            subject=subject,
            body=plain_body,
            html=html_body
        )

