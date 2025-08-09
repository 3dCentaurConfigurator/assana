import openai
from config import Config
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == 'your_openai_api_key_here':
            logger.warning("OpenAI API key not configured. OpenAI features will be disabled.")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.assistant_id = Config.OPENAI_ASSISTANT_ID
        
        # Define available functions for the Assistant
        self.available_functions = {
            "get_appointment_details": {
                "name": "get_appointment_details",
                "description": "Get appointment details for the current user",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "update_appointment_name": {
                "name": "update_appointment_name",
                "description": "Update patient name for appointments",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "new_name": {
                            "type": "string",
                            "description": "The new patient name"
                        }
                    },
                    "required": ["new_name"]
                }
            },
            "update_appointment_datetime_db": {
                "name": "update_appointment_datetime_db",
                "description": "Update appointment date and time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "new_datetime_str": {
                            "type": "string",
                            "description": "The new date and time in format 'Month Day, Year at Hour:Minute AM/PM'"
                        }
                    },
                    "required": ["new_datetime_str"]
                }
            },
            "update_appointment_clinic": {
                "name": "update_appointment_clinic",
                "description": "Update clinic name for appointments",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "new_clinic": {
                            "type": "string",
                            "description": "The new clinic name"
                        }
                    },
                    "required": ["new_clinic"]
                }
            }
        }
        
    def create_chat_completion(self, message, conversation_history=None):
        """
        Create a chat completion using OpenAI's API
        """
        if not self.client:
            return "OpenAI API is not configured. Please set your OPENAI_API_KEY in the .env file to enable AI responses."
        
        # No local greeting handling - using OpenAI web interface instructions only
            
        try:
            # Prepare messages for the API
            messages = []
            
            # No local system message - using OpenAI web interface instructions only
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add the current user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Extract the response
            ai_response = response.choices[0].message.content
            
            logger.info(f"OpenAI response generated successfully")
            return ai_response
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."
    
    def create_assistant_response_with_functions(self, message, whatsapp_number, thread_id=None):
        """
        Create a response using OpenAI Assistant API with function calling capabilities
        """
        # No local greeting handling - using OpenAI web interface instructions only
            
        if not self.client:
            return self.create_chat_completion(message), thread_id
            
        try:
            # Create a new thread if none exists
            if not thread_id:
                thread = self.client.beta.threads.create()
                thread_id = thread.id
            
            # Simple message - let OpenAI Assistant use its web-configured instructions
            enhanced_message = f"User message: {message}\nWhatsApp number: {whatsapp_number}"
            
            # Add the enhanced message to the thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=enhanced_message
            )
            
            # Create a run with tools (functions)
            tools = []
            for func_name, func_def in self.available_functions.items():
                tools.append({
                    "type": "function",
                    "function": func_def
                })
            
            # Run the assistant with tools
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                tools=tools
            )
            
            # Wait for the run to complete
            import time
            while run.status in ["queued", "in_progress"]:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            # Handle function calls if needed
            if run.status == "requires_action" and run.required_action:
                # Get the function calls
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Always use the WhatsApp number from the incoming message
                    # Override any WhatsApp number in the function arguments
                    if "whatsapp_number" in function_args:
                        function_args["whatsapp_number"] = whatsapp_number
                    
                    # Call the appropriate function
                    logger.info(f"Calling function: {function_name} with args: {function_args}")
                    
                    if function_name == "get_appointment_details":
                        from app import get_appointment_details
                        result = get_appointment_details(whatsapp_number)
                        logger.info(f"get_appointment_details result: {result}")
                    elif function_name == "update_appointment_name":
                        from app import update_appointment_name
                        new_name = function_args.get("new_name")
                        logger.info(f"Updating name to: {new_name} for number: {whatsapp_number}")
                        result = update_appointment_name(whatsapp_number, new_name)
                        logger.info(f"update_appointment_name result: {result}")
                    elif function_name == "update_appointment_datetime_db":
                        from app import update_appointment_datetime_db
                        new_datetime = function_args.get("new_datetime_str")
                        logger.info(f"Updating datetime to: {new_datetime} for number: {whatsapp_number}")
                        result = update_appointment_datetime_db(whatsapp_number, new_datetime)
                        logger.info(f"update_appointment_datetime_db result: {result}")
                    elif function_name == "update_appointment_clinic":
                        from app import update_appointment_clinic
                        new_clinic = function_args.get("new_clinic")
                        logger.info(f"Updating clinic to: {new_clinic} for number: {whatsapp_number}")
                        result = update_appointment_clinic(whatsapp_number, new_clinic)
                        logger.info(f"update_appointment_clinic result: {result}")
                    else:
                        result = {"success": False, "message": "Unknown function"}
                        logger.warning(f"Unknown function called: {function_name}")
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                
                # Submit tool outputs
                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                
                # Wait for the run to complete again
                while run.status in ["queued", "in_progress"]:
                    time.sleep(1)
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
            
            if run.status == "completed":
                # Get the response
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                latest_message = messages.data[0]
                
                if latest_message.content:
                    response_text = latest_message.content[0].text.value
                    return response_text, thread_id
            
            return "I apologize, but I'm having trouble processing your request right now.", thread_id
            
        except Exception as e:
            logger.error(f"Error in OpenAI Assistant API call: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now.", thread_id
    
    def create_assistant_response(self, message, thread_id=None):
        """
        Create a response using OpenAI Assistant API (if assistant_id is configured)
        """
        # No local greeting handling - using OpenAI web interface instructions only
            
        if not self.assistant_id:
            return self.create_chat_completion(message)
            
        try:
            # Create a new thread if none exists
            if not thread_id:
                thread = self.client.beta.threads.create()
                thread_id = thread.id
            
            # Add the message to the thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for the run to complete
            import time
            while run.status in ["queued", "in_progress"]:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get the response
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                latest_message = messages.data[0]
                
                if latest_message.content:
                    response_text = latest_message.content[0].text.value
                    return response_text, thread_id
            
            return "I apologize, but I'm having trouble processing your request right now.", thread_id
            
        except Exception as e:
            logger.error(f"Error in OpenAI Assistant API call: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now.", thread_id
