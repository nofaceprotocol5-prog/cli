#!/usr/bin/env python3
"""
GitHub Automation Notification System
Sends notifications via Email, Slack, Discord, Telegram, and Webhook
"""

import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
    
    # ============ EMAIL NOTIFICATIONS ============
    def send_email_notification(self, recipient: str, subject: str, 
                               body: str, repo_name: str = "", status: str = "success") -> bool:
        """Send email notification"""
        logger.info(f"📧 Sending email to {recipient}...")
        
        email_address = os.getenv("GMAIL_ADDRESS")
        email_password = os.getenv("GMAIL_PASSWORD")
        
        if not email_address or not email_password:
            logger.warning("⚠️ Gmail credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_address
            msg['To'] = recipient
            msg['Subject'] = subject
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>🤖 GitHub Automation Notification</h2>
                    <hr>
                    <p><strong>Repository:</strong> {repo_name}</p>
                    <p><strong>Status:</strong> <span style="color: {'green' if status == 'success' else 'red'};">{status.upper()}</span></p>
                    <p><strong>Time:</strong> {self.timestamp}</p>
                    <hr>
                    <div>{body}</div>
                    <hr>
                    <p><small>GitHub 24/7 Automation System</small></p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(email_address, email_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"❌ Email failed: {e}")
            return False
    
    # ============ SLACK NOTIFICATIONS ============
    def send_slack_notification(self, repo_name: str, action: str, 
                               status: str = "success", details: Dict = None) -> bool:
        """Send Slack notification"""
        logger.info(f"💬 Sending Slack notification...")
        
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("⚠️ Slack webhook not configured")
            return False
        
        color = "good" if status == "success" else "danger"
        status_emoji = "✅" if status == "success" else "❌"
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{status_emoji} GitHub Automation Update",
                    "text": f"Repository: *{repo_name}*\nAction: *{action}*",
                    "fields": [
                        {
                            "title": "Status",
                            "value": status.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": self.timestamp,
                            "short": True
                        }
                    ],
                    "footer": "GitHub 24/7 Automation"
                }
            ]
        }
        
        if details:
            payload["attachments"][0]["fields"].append({
                "title": "Details",
                "value": json.dumps(details, indent=2),
                "short": False
            })
        
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info("✅ Slack notification sent")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Slack failed: {e}")
            return False
    
    # ============ DISCORD NOTIFICATIONS ============
    def send_discord_notification(self, repo_name: str, action: str, 
                                 status: str = "success", details: str = "") -> bool:
        """Send Discord notification"""
        logger.info(f"🎮 Sending Discord notification...")
        
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("⚠️ Discord webhook not configured")
            return False
        
        color = 65280 if status == "success" else 16711680  # Green or Red
        status_emoji = "✅" if status == "success" else "❌"
        
        embed = {
            "title": f"{status_emoji} GitHub Automation Update",
            "description": f"**Repository:** {repo_name}\n**Action:** {action}",
            "color": color,
            "fields": [
                {
                    "name": "Status",
                    "value": status.upper(),
                    "inline": True
                },
                {
                    "name": "Time",
                    "value": self.timestamp,
                    "inline": True
                }
            ],
            "footer": {
                "text": "GitHub 24/7 Automation"
            }
        }
        
        if details:
            embed["fields"].append({
                "name": "Details",
                "value": details[:1024],  # Discord limit
                "inline": False
            })
        
        payload = {"embeds": [embed]}
        
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info("✅ Discord notification sent")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Discord failed: {e}")
            return False
    
    # ============ TELEGRAM NOTIFICATIONS ============
    def send_telegram_notification(self, repo_name: str, action: str, 
                                  status: str = "success", details: str = "") -> bool:
        """Send Telegram notification"""
        logger.info(f"📱 Sending Telegram notification...")
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            logger.warning("⚠️ Telegram credentials not configured")
            return False
        
        status_emoji = "✅" if status == "success" else "❌"
        
        message = f"""
{status_emoji} *GitHub Automation Update*

*Repository:* `{repo_name}`
*Action:* {action}
*Status:* {status.upper()}
*Time:* {self.timestamp}
"""
        
        if details:
            message += f"\n*Details:*\n```\n{details[:500]}\n```"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("✅ Telegram notification sent")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Telegram failed: {e}")
            return False
    
    # ============ WEBHOOK NOTIFICATIONS ============
    def send_webhook_notification(self, repo_name: str, action: str, 
                                 status: str = "success", webhook_url: str = None) -> bool:
        """Send custom webhook notification"""
        logger.info(f"🔗 Sending webhook notification...")
        
        webhook_url = webhook_url or os.getenv("CUSTOM_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("⚠️ Webhook URL not configured")
            return False
        
        payload = {
            "event": "github_automation",
            "repository": repo_name,
            "action": action,
            "status": status,
            "timestamp": self.timestamp,
            "source": "github-24-7-automation"
        }
        
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info("✅ Webhook notification sent")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Webhook failed: {e}")
            return False
    
    # ============ MULTI-CHANNEL NOTIFICATIONS ============
    def notify_all(self, repo_name: str, action: str, status: str = "success", 
                  details: str = "", recipients: List[str] = None) -> Dict[str, bool]:
        """Send notifications to all configured channels"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📢 Sending notifications for {repo_name}: {action}")
        logger.info(f"{'='*80}")
        
        results = {}
        
        # Email notifications
        if recipients:
            for email in recipients:
                subject = f"🤖 GitHub Automation: {repo_name} - {action.title()}"
                body = f"""
                <h3>Repository Update</h3>
                <p><strong>Repository:</strong> {repo_name}</p>
                <p><strong>Action:</strong> {action}</p>
                <p><strong>Status:</strong> {status}</p>
                <p><strong>Details:</strong></p>
                <pre>{details}</pre>
                """
                results[f"email_{email}"] = self.send_email_notification(
                    email, subject, body, repo_name, status
                )
        
        # Slack
        results["slack"] = self.send_slack_notification(repo_name, action, status, 
                                                        {"details": details})
        
        # Discord
        results["discord"] = self.send_discord_notification(repo_name, action, status, details)
        
        # Telegram
        results["telegram"] = self.send_telegram_notification(repo_name, action, status, details)
        
        # Webhook
        results["webhook"] = self.send_webhook_notification(repo_name, action, status)
        
        # Summary
        logger.info(f"\n📊 Notification Summary:")
        for channel, success in results.items():
            status_icon = "✅" if success else "⚠️"
            logger.info(f"  {status_icon} {channel}")
        
        return results

# Example usage
if __name__ == "__main__":
    notifier = NotificationManager()
    
    # Example: Notify about fork
    notifier.notify_all(
        repo_name="fastapi-telegram-bot",
        action="forked_and_analyzed",
        status="success",
        details="Successfully forked, added workflows, and pushed to private repo",
        recipients=["your-email@gmail.com"]
    )
