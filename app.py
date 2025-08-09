from flask import Flask, request, jsonify
import json
import logging
from config import Config
from openai_service import OpenAIService
from whatsapp_service import WhatsAppService
import psycopg2
from datetime import datetime
import threading
import time
import os
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

def update_appointment_clinic(whatsapp_number, new_clinic):
    """Update clinic name for appointments"""
    try:
        params = DatabaseConfig.get_connection_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE book_an_appointment 
            SET clinic_name = %s 
            WHERE whatsapp_number = %s
        """, (new_clinic, whatsapp_number))
        
        updated_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if updated_count > 0:
            return {"success": True, "message": f"Updated clinic to '{new_clinic}' for {updated_count} appointment(s)"}
        else:
            return {"success": False, "message": "No appointments found to update"}
            
    except Exception as e:
        logger.error(f"Database error updating clinic: {str(e)}")
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

def update_patient_name(whatsapp_number, new_name):
    """Update patient name in the database for a WhatsApp number"""
    try:
        params = DatabaseConfig.get_connection_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Update all appointments for this WhatsApp number
        cursor.execute("""
            UPDATE book_an_appointment 
            SET patient_name = %s 
            WHERE whatsapp_number = %s
        """, (new_name, whatsapp_number))
        
        # Commit the changes
        conn.commit()
        updated_count = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        logger.info(f"Updated {updated_count} appointments for {whatsapp_number} with new name: {new_name}")
        return True, updated_count
        
    except Exception as e:
        logger.error(f"Database error updating patient name: {str(e)}")
        return False, 0

def update_appointment_datetime(whatsapp_number, new_datetime_str):
    """Update appointment date and time in the database"""
    try:
        from datetime import datetime
        import re
        
        # Try manual parsing first for common formats
        try:
            # Common format: "August 24, 2025 at 2:00 PM"
            if " at " in new_datetime_str and "," in new_datetime_str:
                # Parse the date part
                date_part = new_datetime_str.split(" at ")[0].strip()
                time_part = new_datetime_str.split(" at ")[1].strip()
                
                # Parse date
                parsed_date = datetime.strptime(date_part, "%B %d, %Y")
                
                # Parse time
                parsed_time = datetime.strptime(time_part, "%I:%M %p")
                
                # Combine date and time
                combined_datetime = parsed_date.replace(
                    hour=parsed_time.hour,
                    minute=parsed_time.minute
                )
                
                datetime_str = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Manual parsing successful: {datetime_str}")
                
                # Update the database
                params = DatabaseConfig.get_connection_params()
                conn = psycopg2.connect(**params)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE book_an_appointment 
                    SET booking_time = %s 
                    WHERE whatsapp_number = %s
                """, (datetime_str, whatsapp_number))
                
                conn.commit()
                updated_count = cursor.rowcount
                cursor.close()
                conn.close()
                
                logger.info(f"Updated {updated_count} appointments for {whatsapp_number} with new datetime: {datetime_str}")
                return True, updated_count, datetime_str
                
        except Exception as manual_error:
            logger.info(f"Manual parsing failed, trying AI: {str(manual_error)}")
        
        # Use AI to parse the datetime string if manual parsing fails
        context = f"""
        You are a helpful medical appointment assistant at Assana Clinic. Parse this date/time string into a proper datetime format for appointment scheduling.
        
        User input: "{new_datetime_str}"
        
        Your task is to:
        1. Extract the date and time from the input
        2. Convert it to ISO format: YYYY-MM-DD HH:MM:SS
        3. If you can parse it, respond with "VALID_DATETIME: YYYY-MM-DD HH:MM:SS"
        4. If you cannot parse it, respond with "INVALID_DATETIME: Please provide date and time in format 'Month Day, Year at Hour:Minute AM/PM' for your Assana Clinic appointment"
        
        Examples:
        - "August 20, 2025 at 3:00 PM" → "VALID_DATETIME: 2025-08-20 15:00:00"
        - "August 24, 2025 at 2:00 PM" → "VALID_DATETIME: 2025-08-24 14:00:00"
        - "tomorrow at 2pm" → "VALID_DATETIME: [calculated date] 14:00:00"
        
        IMPORTANT: Respond with EXACTLY "VALID_DATETIME: [iso_format]" or "INVALID_DATETIME: [message]" - no other text.
        
        Respond with either "VALID_DATETIME: [iso_format]" or "INVALID_DATETIME: [message]"
        """
        
        ai_response = openai_service.create_chat_completion(context)
        logger.info(f"AI response for datetime parsing: '{ai_response}'")
        
        if "VALID_DATETIME:" in ai_response:
            # Extract the datetime
            datetime_str = ai_response.split("VALID_DATETIME:")[1].strip()
            
            # Update the database
            params = DatabaseConfig.get_connection_params()
            conn = psycopg2.connect(**params)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE book_an_appointment 
                SET booking_time = %s 
                WHERE whatsapp_number = %s
            """, (datetime_str, whatsapp_number))
            
            conn.commit()
            updated_count = cursor.rowcount
            cursor.close()
            conn.close()
            
            logger.info(f"Updated {updated_count} appointments for {whatsapp_number} with new datetime: {datetime_str}")
            return True, updated_count, datetime_str
            
        else:
            error_msg = ai_response.split("INVALID_DATETIME:")[1].strip() if "INVALID_DATETIME:" in ai_response else "Invalid date/time format"
            return False, 0, error_msg
            
    except Exception as e:
        logger.error(f"Database error updating appointment datetime: {str(e)}")
        return False, 0, str(e)

def update_clinic_name(whatsapp_number, new_clinic):
    """Update clinic name in the database"""
    try:
        params = DatabaseConfig.get_connection_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Update all appointments for this WhatsApp number
        cursor.execute("""
            UPDATE book_an_appointment 
            SET clinic_name = %s 
            WHERE whatsapp_number = %s
        """, (new_clinic, whatsapp_number))
        
        # Commit the changes
        conn.commit()
        updated_count = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        logger.info(f"Updated {updated_count} appointments for {whatsapp_number} with new clinic: {new_clinic}")
        return True, updated_count
        
    except Exception as e:
        logger.error(f"Database error updating clinic name: {str(e)}")
        return False, 0

# Removed handle_confirmation_response function - now using OpenAI Assistant for all interactions

@app.route('/')
def home():
    """Home endpoint to check if the app is running"""
    return jsonify({
        "status": "success",
        "message": "WhatsApp OpenAI Bot is running!",
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
        "timestamp": time.time()
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

@app.route('/test-openai', methods=['POST'])
def test_openai():
    """Test endpoint for OpenAI integration"""
    try:
        data = request.get_json()
        message = data.get('message', 'Hello, how are you?')
        
        response = openai_service.create_chat_completion(message)
        
        return jsonify({
            "status": "success",
            "message": message,
            "response": response
        })
        
    except Exception as e:
        logger.error(f"Error in test_openai endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/test-template/<whatsapp_number>', methods=['POST'])
def test_template_endpoint(whatsapp_number):
    """Test the assana template directly"""
    try:
        # Test with simple parameters
        success, result = whatsapp_service.send_template_message(
            to_number=whatsapp_number,
            template_name="assanatest",
            language_code="en",
            components=[
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "John Smith"
                        },
                        {
                            "type": "text", 
                            "text": "August 10, 2025 at 2:00 PM"
                        }
                    ]
                }
            ]
        )
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Template test sent successfully to {whatsapp_number}",
                "result": result
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Template test failed: {result}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error testing template: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/check-appointment/<whatsapp_number>', methods=['GET'])
def check_appointment_endpoint(whatsapp_number):
    """Test endpoint to check appointments for a WhatsApp number"""
    try:
        has_appointments, appointments = check_appointment_in_database(whatsapp_number)
        
        if has_appointments:
            appointment_data = []
            for apt in appointments:
                appointment_data.append({
                    'patient_name': apt[0],
                    'booking_time': apt[1].isoformat() if apt[1] else None,
                    'clinic_name': apt[2],
                    'status': apt[3],
                    'created_at': apt[4].isoformat() if apt[4] else None
                })
            
            return jsonify({
                "status": "success",
                "whatsapp_number": whatsapp_number,
                "has_appointments": True,
                "appointment_count": len(appointments),
                "appointments": appointment_data,
                "formatted_message": format_appointment_message(appointments)
            })
        else:
            return jsonify({
                "status": "success",
                "whatsapp_number": whatsapp_number,
                "has_appointments": False,
                "appointment_count": 0,
                "appointments": [],
                "message": "No appointments found for this number."
            })
            
    except Exception as e:
        logger.error(f"Error checking appointment: {str(e)}")
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
            
            # First try to send using Meta template (to bypass 24-hour policy)
            # Template: "assana" (English) with parameters: [Name] and [Date & Time]
            logger.info(f"Attempting to send template 'assana' to {whatsapp_number}")
            
            # Option: Send only database message (set to True to send only appointment data)
            send_only_data = False  # Set to True to send only appointment data
            
            if send_only_data:
                # Send only the appointment details
                appointment_message = format_appointment_message(appointments)
                success, result = whatsapp_service.send_message(whatsapp_number, appointment_message)
                
                if success:
                    logger.info(f"Appointment details sent successfully to {whatsapp_number}")
                    return jsonify({
                        "status": "success",
                        "message": f"Appointment details sent to {whatsapp_number}",
                        "appointment_count": len(appointments),
                        "template_used": "custom_only",
                        "result": result
                    })
                else:
                    logger.error(f"Failed to send appointment details to {whatsapp_number}: {result}")
                    return jsonify({
                        "status": "error",
                        "message": f"Failed to send message: {result}"
                    }), 500
            else:
                # Send template first, then appointment details
                success, result = whatsapp_service.send_appointment_template(
                    whatsapp_number, 
                    patient_name, 
                    booking_time,
                    template_name="assanatest"  # Your new template with {{1}} and {{2}} parameters
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
                # Log the exact error for debugging
                if "does not exist" in str(result):
                    logger.error("Template 'assanatest' does not exist or is not approved")
                elif "Quality pending" in str(result):
                    logger.error("Template 'assanatest' is still in quality review")
                else:
                    logger.error(f"Unknown template error: {result}")
                # Template failed, fallback to custom message
                logger.warning(f"Template failed, falling back to custom message: {result}")
                appointment_message = format_appointment_message(appointments)
                success, result = whatsapp_service.send_message(whatsapp_number, appointment_message)
                
                if success:
                    logger.info(f"Custom appointment message sent successfully to {whatsapp_number}")
                    return jsonify({
                        "status": "success",
                        "message": f"Custom appointment message sent to {whatsapp_number} (template failed)",
                        "appointment_count": len(appointments),
                        "template_used": "custom_fallback",
                        "result": result
                    })
                else:
                    logger.error(f"Failed to send custom appointment message to {whatsapp_number}: {result}")
                    return jsonify({
                        "status": "error",
                        "message": f"Failed to send message: {result}"
                    }), 500
        else:
            logger.info(f"No appointments found for {whatsapp_number}")
            return jsonify({
                "status": "success",
                "message": f"No appointments found for {whatsapp_number}",
                "appointment_count": 0
            })
            
    except Exception as e:
        logger.error(f"Error sending appointment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/update-name/<whatsapp_number>', methods=['POST'])
def update_name_endpoint(whatsapp_number):
    """Manual endpoint to update patient name for testing"""
    try:
        data = request.get_json()
        new_name = data.get('name')
        
        if not new_name:
            return jsonify({"error": "Missing 'name' parameter"}), 400
        
        success, updated_count = update_patient_name(whatsapp_number, new_name)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Updated {updated_count} appointment(s) for {whatsapp_number}",
                "new_name": new_name,
                "updated_count": updated_count
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to update name in database"
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating name: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/check-templates', methods=['GET'])
def check_templates_endpoint():
    """Check available WhatsApp templates"""
    try:
        success, templates = whatsapp_service.get_available_templates()
        
        if success:
            return jsonify({
                "status": "success",
                "templates": templates
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to get templates: {templates}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error checking templates: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("Starting WhatsApp OpenAI Bot...")
    logger.info(f"OpenAI API Key configured: {'Yes' if Config.OPENAI_API_KEY else 'No'}")
    logger.info(f"WhatsApp Access Token configured: {'Yes' if Config.ACCESS_TOKEN else 'No'}")
    
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
