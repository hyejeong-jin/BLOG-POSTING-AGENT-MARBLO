"""
Email service for sending emails through SES or SendGrid.

This module provides functionality to send emails for password resets,
invitations, and other notifications.
"""

from datetime import datetime
from typing import Optional

import httpx
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class EmailService:
    """
    Email service abstraction supporting multiple providers (SES, SendGrid).
    """
    
    @staticmethod
    async def send_password_reset_email(
        to_email: str,
        to_name: str,
        reset_token: str,
        reset_link: str,
    ) -> bool:
        """
        Send a password reset email.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient display name
            reset_token: The reset token for verification
            reset_link: Full reset link URL for the email
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Marblo - Password Reset Request"
        
        html_body = f"""
        <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Password Reset Request</h2>
                    <p>Hello {to_name},</p>
                    <p>We received a request to reset your password. Click the link below to create a new password:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #007bff; color: white; padding: 10px 20px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </p>
                    <p>Or copy this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                        {reset_link}
                    </p>
                    <p><strong>This link expires in 24 hours.</strong></p>
                    <p style="margin-top: 30px; font-size: 12px; color: #999;">
                        If you did not request this password reset, please ignore this email or contact support.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        Hello {to_name},
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_link}
        
        This link expires in 24 hours.
        
        If you did not request this password reset, please ignore this email or contact support.
        """
        
        if settings.email_provider == "sendgrid":
            return await EmailService._send_via_sendgrid(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
        else:
            # Default to SES
            return await EmailService._send_via_ses(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
    
    @staticmethod
    async def _send_via_sendgrid(
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        """
        Send email via SendGrid API.
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            
        Returns:
            True if successful, False otherwise
        """
        if not settings.sendgrid_api_key:
            logger.error("SendGrid API key not configured")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "personalizations": [
                        {
                            "to": [{"email": to_email, "name": to_name}],
                            "subject": subject,
                        }
                    ],
                    "from": {
                        "email": settings.email_from,
                        "name": settings.email_from_name,
                    },
                    "content": [
                        {"type": "text/plain", "value": text_body},
                        {"type": "text/html", "value": html_body},
                    ],
                }
                
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
                )
                
                if response.status_code in (200, 202):
                    logger.info("Password reset email sent successfully via SendGrid", email=to_email)
                    return True
                else:
                    logger.error(
                        "Failed to send email via SendGrid",
                        email=to_email,
                        status=response.status_code,
                        error=response.text,
                    )
                    return False
        except Exception as e:
            logger.error("Error sending email via SendGrid", email=to_email, error=str(e))
            return False
    
    @staticmethod
    async def _send_via_ses(
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        """
        Send email via AWS SES.
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import boto3
            
            # Create SES client
            ses_client = boto3.client(
                "ses",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            
            # Send email
            response = ses_client.send_email(
                Source=f"{settings.email_from_name} <{settings.email_from}>",
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {
                        "Text": {"Data": text_body},
                        "Html": {"Data": html_body},
                    },
                },
            )
            
            logger.info("Password reset email sent successfully via SES", email=to_email)
            return True
        except Exception as e:
            logger.error("Error sending email via SES", email=to_email, error=str(e))
            return False
    
    @staticmethod
    async def send_family_invitation_email(
        to_email: str,
        to_name: str,
        blogger_name: str,
        invitation_token: str,
        expires_at: datetime,
    ) -> bool:
        """
        Send a family member invitation email.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient display name
            blogger_name: Name of the blogger inviting them
            invitation_token: The invitation token for accepting
            expires_at: When the invitation expires
            
        Returns:
            True if email sent successfully, False otherwise
        
        Requirements: 6.1, 6.2
        """
        subject = f"{blogger_name} has invited you to collaborate on Marblo"
        
        # Build acceptance link
        acceptance_link = f"{settings.frontend_url}/invite/accept?token={invitation_token}"
        expires_time = expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        html_body = f"""
        <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>You've been invited to Marblo!</h2>
                    <p>Hello {to_name},</p>
                    <p><strong>{blogger_name}</strong> has invited you to collaborate on their blog using Marblo, an AI-powered blog post generation service.</p>
                    <p>As a family member collaborator, you'll be able to:</p>
                    <ul>
                        <li>Create and edit blog posts</li>
                        <li>Upload and analyze photos</li>
                        <li>Generate AI-powered content</li>
                    </ul>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{acceptance_link}" 
                           style="background-color: #28a745; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block; 
                                  font-size: 16px; font-weight: bold;">
                            Accept Invitation
                        </a>
                    </p>
                    <p>Or copy this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                        {acceptance_link}
                    </p>
                    <p><strong>This invitation expires on {expires_time}.</strong></p>
                    <p style="margin-top: 30px; font-size: 12px; color: #999;">
                        If you did not expect this invitation, you can safely ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        You've been invited to Marblo!
        
        Hello {to_name},
        
        {blogger_name} has invited you to collaborate on their blog using Marblo, an AI-powered blog post generation service.
        
        As a family member collaborator, you'll be able to:
        - Create and edit blog posts
        - Upload and analyze photos
        - Generate AI-powered content
        
        To accept this invitation, click the link below:
        
        {acceptance_link}
        
        This invitation expires on {expires_time}.
        
        If you did not expect this invitation, you can safely ignore this email.
        """
        
        if settings.email_provider == "sendgrid":
            return await EmailService._send_via_sendgrid(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
        else:
            # Default to SES
            return await EmailService._send_via_ses(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )


class EmailService:
    """
    Email service abstraction supporting multiple providers (SES, SendGrid).
    """
    
    @staticmethod
    async def send_family_invitation_email(
        to_email: str,
        to_name: str,
        blogger_name: str,
        invitation_token: str,
        expires_at: datetime,
    ) -> bool:
        """
        Send a family member invitation email.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient display name
            blogger_name: Name of the blogger inviting them
            invitation_token: The invitation token for accepting
            expires_at: When the invitation expires
            
        Returns:
            True if email sent successfully, False otherwise
        
        Requirements: 6.1, 6.2
        """
        subject = f"{blogger_name} has invited you to collaborate on Marblo"
        
        # Build acceptance link
        acceptance_link = f"{settings.frontend_url}/invite/accept?token={invitation_token}"
        expires_time = expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        html_body = f"""
        <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>You've been invited to Marblo!</h2>
                    <p>Hello {to_name},</p>
                    <p><strong>{blogger_name}</strong> has invited you to collaborate on their blog using Marblo, an AI-powered blog post generation service.</p>
                    <p>As a family member collaborator, you'll be able to:</p>
                    <ul>
                        <li>Create and edit blog posts</li>
                        <li>Upload and analyze photos</li>
                        <li>Generate AI-powered content</li>
                    </ul>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{acceptance_link}" 
                           style="background-color: #28a745; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block; 
                                  font-size: 16px; font-weight: bold;">
                            Accept Invitation
                        </a>
                    </p>
                    <p>Or copy this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                        {acceptance_link}
                    </p>
                    <p><strong>This invitation expires on {expires_time}.</strong></p>
                    <p style="margin-top: 30px; font-size: 12px; color: #999;">
                        If you did not expect this invitation, you can safely ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        You've been invited to Marblo!
        
        Hello {to_name},
        
        {blogger_name} has invited you to collaborate on their blog using Marblo, an AI-powered blog post generation service.
        
        As a family member collaborator, you'll be able to:
        - Create and edit blog posts
        - Upload and analyze photos
        - Generate AI-powered content
        
        To accept this invitation, click the link below:
        
        {acceptance_link}
        
        This invitation expires on {expires_time}.
        
        If you did not expect this invitation, you can safely ignore this email.
        """
        
        if settings.email_provider == "sendgrid":
            return await EmailService._send_via_sendgrid(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
        else:
            # Default to SES
            return await EmailService._send_via_ses(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )


