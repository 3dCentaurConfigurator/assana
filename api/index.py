from flask import Flask, request, jsonify
import json
import logging
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from openai_service import OpenAIService
from whatsapp_service import WhatsAppService
import psycopg2
from datetime import datetime
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
class DatabaseConfig:
    # PostgreSQL Configuration
    DB_HOST = os.getenv('DB_HOST', 'ep-broad-firefly-ad4k1jpt-pooler.c-2.us-east-1.aws.neon.tech')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'neondb')
    DB_USER = os.getenv('DB_USER', 'neondb_owner')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'npg_6bemGOwox1uR')
    
    @classmethod
    def get_connection_params(cls):
        """Get connection parameters as dictionary"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'database': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD
        }

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize services
openai_service = OpenAIService()
whatsapp_service = WhatsAppService()

# Store conversation threads (in production, use a proper database)
conversation_threads = {}

# Database functions for OpenAI Assistant
def get_appointment_details(whatsapp_number):
    """Get appointment details for a WhatsApp number"""
    try:
        params = DatabaseConfig.get_connection_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT patient_name, booking_time, clinic_name, status, created_at
            FROM book_an_appointment 
            WHERE whatsapp_number = %s 
            ORDER BY created_at DESC
        """, (whatsapp_number,))
        
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if appointments:
            formatted_appointments = []
            for apt in appointments:
                formatted_appointments.append({
                    "patient_name": apt[0],
                    "booking_time": apt[1].strftime("%B %d, %Y at %I:%M %p") if apt[1] else "Not set",
                    "clinic_name": apt[2],
                    "status": apt[3],
                    "created_at": apt[4].strftime("%Y-%m-%d %H:%M:%S") if apt[4] else "Not set"
                })
            return {"success": True, "appointments": formatted_appointments}
        else:
            return {"success": False, "message": "No appointments found for this number"}
            
    except Exception as e:
        logger.error(f"Database error getting appointments: {str(e)}")
        return {"success": False, "message": f"Database error: {str(e)}"}

def update_appointment_name(whatsapp_number, new_name):
    """Update patient name for appointments"""
    try:
        logger.info(f"Attempting to update name for {whatsapp_number} to '{new_name}'")
        
        params = DatabaseConfig.get_connection_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # First check if the appointment exists
        cursor.execute("""
            SELECT COUNT(*) FROM book_an_appointment 
            WHERE whatsapp_number = %s
        """, (whatsapp_number,))
        
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} appointments for number {whatsapp_number}")
        
        cursor.execute("""
            UPDATE book_an_appointment 
            SET patient_name = %s 
            WHERE whatsapp_number = %s
        """, (new_name, whatsapp_number))
        
        updated_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Updated {updated_count} rows for name change")
        
        if updated_count > 0:
            return {"success": True, "message": f"Updated name to '{new_name}' for {updated_count} appointment(s)"}
        else:
            return {"success": False, "message": "No appointments found to update"}
            
    except Exception as e:
        logger.error(f"Database error updating name: {str(e)}")
        return {"success": False, "message": f"Database error: {str(e)}"}

def update_appointment_datetime_db(whatsapp_number, new_datetime_str):
    """Update appointment date and time"""
    try:
        from datetime import datetime
        import re
        
        # Try manual parsing for common formats
        datetime_str = None
        
        # Format: "August 24, 2025 at 2:00 PM"
        if " at " in new_datetime_str and "," in new_datetime_str:
            try:
                date_part = new_datetime_str.split(" at ")[0].strip()
                time_part = new_datetime_str.split(" at ")[1].strip()
                parsed_date = datetime.strptime(date_part, "%B %d, %Y")
                parsed_time = datetime.strptime(time_part, "%I:%M %p")
                combined_datetime = parsed_date.replace(hour=parsed_time.hour, minute=parsed_time.minute)
                datetime_str = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        
        # Format: "2025-08-24 14:00:00" (already in ISO format)
        elif re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', new_datetime_str):
            datetime_str = new_datetime_str
        
        # If parsing failed, return error
        if not datetime_str:
            return {"success": False, "message": "Invalid date/time format. Please use format: 'Month Day, Year at Hour:Minute AM/PM' (e.g., 'August 24, 2025 at 2:00 PM')"}
        
        params = DatabaseConfig.get_connection_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE book_an_appointment 
            SET booking_time = %s 
            WHERE whatsapp_number = %s
        """, (datetime_str, whatsapp_number))
        
        updated_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if updated_count > 0:
            return {"success": True, "message": f"Updated appointment time to {new_datetime_str} for {updated_count} appointment(s)"}
        else:
            return {"success": False, "message": "No appointments found to update"}
            
    except Exception as e:
        logger.error(f"Database error updating datetime: {str(e)}")
        return {"success": False, "message": f"Database error: {str(e)}"}

def check_appointment_in_database(whatsapp_number):
    """Check if WhatsApp number exists in book_an_appointment table"""
    try:
        params = DatabaseConfig.get_connection_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Query for appointments with this WhatsApp number
        cursor.execute("""
            SELECT patient_name, booking_time, clinic_name, status, created_at
            FROM book_an_appointment 
            WHERE whatsapp_number = %s 
            ORDER BY created_at DESC
        """, (whatsapp_number,))
        
        appointments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if appointments:
            return True, appointments
        else:
            return False, []
            
    except Exception as e:
        logger.error(f"Database error checking appointments: {str(e)}")
        return False, []

def format_appointment_message(appointments):
    """Format appointment details for WhatsApp message"""
    if not appointments:
        return "No appointments found for this number."
    
    message = "🏥 *Hello! Welcome to Assana Clinic*\n\n"
    message += "Here are your appointment details:\n\n"
    
    for apt in appointments:
        patient_name = apt[0]
        booking_time = apt[1]
        
        # Format booking time
        if booking_time:
            booking_str = booking_time.strftime("%B %d, %Y at %I:%M %p")
        else:
            booking_str = "Not specified"
        
        message += f"👤 *Patient Name:* {patient_name}\n"
        message += f"📅 *Appointment Time:* {booking_str}\n"
        message += "─" * 30 + "\n\n"
    
    message += "Thank you for choosing Assana Clinic! 🙏\n\n"
    message += "📝 *Please confirm:* Is the information above correct?\n"
    message += "Reply with:\n"
    message += "• 'Yes' or 'Correct' - if information is accurate\n"
    message += "• 'No' or 'Wrong' - if any details need to be updated"
    return message

def process_message(message):
    """Process incoming WhatsApp message and generate AI response"""
    try:
        # Extract message details
        message_id = message.get('id')
        from_number = message.get('from')
        message_type = message.get('type')
        timestamp = message.get('timestamp')
        
        logger.info(f"Processing message from {from_number}: {message_type}")
        
        # Mark message as read
        whatsapp_service.mark_message_as_read(message_id)
        
        # Only process text messages
        if message_type != 'text':
            response_text = "I can only process text messages at the moment. Please send me a text message!"
            whatsapp_service.send_message(from_number, response_text)
            return
        
        # Extract text content
        text_content = message.get('text', {}).get('body', '')
        
        if not text_content.strip():
            response_text = "I didn't receive any text. Please send me a message!"
            whatsapp_service.send_message(from_number, response_text)
            return
        
        # Send typing indicator
        whatsapp_service.send_typing_indicator(from_number, True)
        
        # Use OpenAI Assistant API with function calling capabilities for all messages
        logger.info(f"Using OpenAI Assistant with function calling for {from_number}")
        
        response_text, thread_id = openai_service.create_assistant_response_with_functions(
            text_content, 
            from_number
        )
        
        # Send the AI response directly to the user
        success, result = whatsapp_service.send_message(from_number, response_text)
        
        if success:
            logger.info(f"AI response with functions sent successfully to {from_number}")
        else:
            logger.error(f"Failed to send AI response to {from_number}: {result}")
            
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Send error message to user
        try:
            error_message = "I'm sorry, but I encountered an error processing your message. Please try again later."
            whatsapp_service.send_message(from_number, error_message)
        except:
            logger.error("Failed to send error message to user")

@app.route('/')
def home():
    """Home endpoint to check if the app is running"""
    return jsonify({
        "status": "success",
        "message": "WhatsApp OpenAI Bot is running on Vercel!",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "send_message": "/send-message",
            "test_openai": "/test-openai",
            "check_appointment": "/check-appointment/<whatsapp_number>",
            "send_appointment": "/send-appointment/<whatsapp_number>",
            "update_name": "/update-name/<whatsapp_number>"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "platform": "vercel"
    })

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify WhatsApp webhook"""
    try:
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        logger.info(f"Webhook verification request: mode={mode}, token={token}")
        
        success, response = whatsapp_service.verify_webhook(mode, token, challenge)
        
        if success:
            return challenge
        else:
            return jsonify({"error": "Verification failed"}), 403
            
    except Exception as e:
        logger.error(f"Error in webhook verification: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages"""
    try:
        data = request.get_json()
        logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")
        
        # Extract the message data
        if 'object' in data and data['object'] == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('value', {}).get('messages'):
                        for message in change['value']['messages']:
                            # Process the message
                            process_message(message)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/send-message', methods=['POST'])
def send_message():
    """Manual endpoint to send a message (for testing)"""
    try:
        data = request.get_json()
        to_number = data.get('to')
        message = data.get('message')
        
        if not to_number or not message:
            return jsonify({"error": "Missing 'to' or 'message' parameter"}), 400
        
        success, result = whatsapp_service.send_message(to_number, message)
        
        if success:
            return jsonify({"status": "success", "result": result})
        else:
            return jsonify({"status": "error", "result": result}), 500
            
    except Exception as e:
        logger.error(f"Error in send_message endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/send-appointment/<whatsapp_number>', methods=['POST'])
def send_appointment_endpoint(whatsapp_number):
    """Send appointment message using Meta template with fallback"""
    try:
        logger.info(f"Checking appointments for: {whatsapp_number}")
        
        # Check database for appointments
        has_appointments, appointments = check_appointment_in_database(whatsapp_number)
        
        if has_appointments:
            # Get the first appointment details
            first_appointment = appointments[0]  # Get the most recent appointment
            patient_name = first_appointment[0]
            booking_time = first_appointment[1]
            
            # Send template message
            success, result = whatsapp_service.send_appointment_template(
                whatsapp_number, 
                patient_name, 
                booking_time,
                template_name="assanatest"
            )
        
            if success:
                logger.info(f"Appointment template sent successfully to {whatsapp_number}")
                return jsonify({
                    "status": "success",
                    "message": f"Appointment template sent to {whatsapp_number}",
                    "appointment_count": len(appointments),
                    "template_used": "assanatest",
                    "result": result
                })
            else:
                logger.error(f"Template failed with error: {result}")
                # Template failed, fallback to custom message
                appointment_message = format_appointment_message(appointments)
                success, result = whatsapp_service.send_message(whatsapp_number, appointment_message)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": f"Custom appointment message sent to {whatsapp_number} (template failed)",
                        "appointment_count": len(appointments),
                        "template_used": "custom_fallback",
                        "result": result
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": f"Failed to send message: {result}"
                    }), 500
        else:
            return jsonify({
                "status": "success",
                "message": f"No appointments found for {whatsapp_number}",
                "appointment_count": 0
            })
            
    except Exception as e:
        logger.error(f"Error sending appointment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Vercel serverless function handler
def handler(request):
    """Vercel serverless function handler"""
    return app(request.environ, lambda status, headers: None)

# For Vercel, the app should be callable directly
if __name__ == '__main__':
    app.run(debug=True)
