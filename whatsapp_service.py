import requests
import json
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.access_token = Config.ACCESS_TOKEN
        self.phone_number_id = Config.PHONE_NUMBER_ID
        self.api_url = Config.WHATSAPP_API_URL
        
        # Check if WhatsApp credentials are configured
        if not self.access_token or self.access_token == 'your_whatsapp_access_token_here':
            logger.warning("WhatsApp credentials not configured. WhatsApp features will be disabled.")
            self.headers = None
        else:
            self.headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
    
    def send_message(self, to_number, message):
        """
        Send a text message via WhatsApp Business API
        """
        if not self.headers:
            logger.warning("WhatsApp not configured. Message not sent.")
            return False, "WhatsApp API is not configured. Please set your WhatsApp credentials in the .env file."
            
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to {to_number}")
                return True, response.json()
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False, response.text
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False, str(e)
    
    def send_typing_indicator(self, to_number, typing=True):
        """
        Send typing indicator to show the bot is typing
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "reaction",
                "reaction": {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual"
                }
            }
            
            if typing:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to_number,
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {
                            "text": "AI is thinking..."
                        }
                    }
                }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Typing indicator sent to {to_number}")
                return True
            else:
                logger.error(f"Failed to send typing indicator: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending typing indicator: {str(e)}")
            return False
    
    def mark_message_as_read(self, message_id):
        """
        Mark a message as read
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Message {message_id} marked as read")
                return True
            else:
                logger.error(f"Failed to mark message as read: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False
    
    def verify_webhook(self, mode, token, challenge):
        """
        Verify WhatsApp webhook
        """
        if mode == "subscribe" and token == Config.VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return True, challenge
        else:
            logger.error("Webhook verification failed")
            return False, None

    def send_template_message(self, to_number, template_name, language_code="en_US", components=None):
        """
        Send a template message via WhatsApp Business API
        """
        if not self.headers:
            logger.warning("WhatsApp not configured. Template message not sent.")
            return False, "WhatsApp API is not configured. Please set your WhatsApp credentials in the .env file."
            
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            # Add components if provided
            if components:
                payload["template"]["components"] = components
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Template message '{template_name}' sent successfully to {to_number}")
                return True, response.json()
            else:
                logger.error(f"Failed to send template message: {response.status_code} - {response.text}")
                return False, response.text
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp template message: {str(e)}")
            return False, str(e)

    def get_available_templates(self):
        """
        Get list of available templates from WhatsApp Business API
        """
        if not self.headers:
            logger.warning("WhatsApp not configured. Cannot fetch templates.")
            return False, "WhatsApp API is not configured."
            
        try:
            url = f"{self.api_url}/{self.phone_number_id}/message_templates"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                templates = response.json()
                logger.info(f"Available templates: {templates}")
                return True, templates
            else:
                logger.error(f"Failed to get templates: {response.status_code} - {response.text}")
                return False, response.text
                
        except Exception as e:
            logger.error(f"Error getting templates: {str(e)}")
            return False, str(e)

    def send_appointment_template(self, to_number, patient_name, appointment_time, template_name="assanatest"):
        """
        Send appointment details using the specified template with parameters
        """
        try:
            # Format appointment time
            if appointment_time:
                booking_str = appointment_time.strftime("%B %d, %Y at %I:%M %p")
            else:
                booking_str = "Not specified"
            
            # Create components for the template with parameters
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": patient_name
                        },
                        {
                            "type": "text", 
                            "text": booking_str
                        }
                    ]
                }
            ]
            
            # Send template with parameters
            return self.send_template_message(to_number, template_name, "en", components)
            
        except Exception as e:
            logger.error(f"Error sending appointment template: {str(e)}")
            return False, str(e)
