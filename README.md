# WhatsApp OpenAI Bot

A Python Flask application that integrates WhatsApp Business API with OpenAI to provide ChatGPT-like responses through WhatsApp.

## Features

- 🤖 **AI-Powered Responses**: Uses OpenAI's GPT models for intelligent conversations
- 📱 **WhatsApp Integration**: Seamless integration with WhatsApp Business API
- 🔄 **Conversation Memory**: Maintains conversation context using OpenAI Assistant API
- ⚡ **Real-time Processing**: Instant message processing and response generation
- 🛡️ **Webhook Security**: Secure webhook verification for WhatsApp
- 📊 **Logging**: Comprehensive logging for debugging and monitoring

## Prerequisites

Before running this application, you need:

1. **OpenAI API Key**: Get your API key from [OpenAI Platform](https://platform.openai.com/)
2. **WhatsApp Business API Access**: Set up a WhatsApp Business account and get the required credentials
3. **Public HTTPS URL**: For webhook verification (you can use ngrok for local development)

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd APITest
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory with your credentials:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ASSISTANT_ID=your_openai_assistant_id_here

# WhatsApp Business API Configuration
ACCESS_TOKEN=your_whatsapp_access_token_here
VERIFY_TOKEN=your_whatsapp_verify_token_here
PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
WHATSAPP_BUSINESS_ACCOUNT_ID=your_whatsapp_business_account_id_here
WHATSAPP_BUSINESS_APP_ID=your_whatsapp_business_app_id_here
VERSION=v18.0

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
```

### 3. WhatsApp Business API Setup

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app or use an existing one
3. Add WhatsApp Business API product
4. Configure your webhook URL: `https://your-domain.com/webhook`
5. Set the verify token (same as in your .env file)
6. Subscribe to the `messages` webhook event

### 4. OpenAI Setup

1. Get your API key from [OpenAI Platform](https://platform.openai.com/)
2. (Optional) Create an Assistant in OpenAI for enhanced conversation memory
3. Add the Assistant ID to your .env file

### 5. Local Development with ngrok

For local development, use ngrok to expose your local server:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start your Flask app
python app.py

# In another terminal, expose your local server
ngrok http 5000
```

Use the ngrok URL as your webhook URL in WhatsApp Business API settings.

## Running the Application

### Development Mode

```bash
python app.py
```

### Production Mode

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### Webhook Endpoints

- `GET /webhook` - WhatsApp webhook verification
- `POST /webhook` - Receive WhatsApp messages

### Utility Endpoints

- `GET /` - Home page with app status
- `GET /health` - Health check
- `POST /send-message` - Manually send a WhatsApp message
- `POST /test-openai` - Test OpenAI integration

## Usage Examples

### Test OpenAI Integration

```bash
curl -X POST http://localhost:5000/test-openai \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

### Send Manual Message

```bash
curl -X POST http://localhost:5000/send-message \
  -H "Content-Type: application/json" \
  -d '{"to": "1234567890", "message": "Hello from the bot!"}'
```

## File Structure

```
APITest/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── openai_service.py     # OpenAI API integration
├── whatsapp_service.py   # WhatsApp Business API integration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration Details

### OpenAI Configuration

- **OPENAI_API_KEY**: Your OpenAI API key
- **OPENAI_ASSISTANT_ID**: (Optional) OpenAI Assistant ID for conversation memory

### WhatsApp Configuration

- **ACCESS_TOKEN**: WhatsApp Business API access token
- **VERIFY_TOKEN**: Custom token for webhook verification
- **PHONE_NUMBER_ID**: Your WhatsApp phone number ID
- **WHATSAPP_BUSINESS_ACCOUNT_ID**: Your WhatsApp Business account ID
- **WHATSAPP_BUSINESS_APP_ID**: Your WhatsApp Business app ID
- **VERSION**: WhatsApp API version (default: v18.0)

## Features in Detail

### AI Response Generation

The bot uses OpenAI's GPT models to generate intelligent responses. It can:

- Understand context and maintain conversation flow
- Provide helpful and informative answers
- Handle various types of queries and requests

### Conversation Memory

When using OpenAI Assistant API:

- Maintains conversation threads per user
- Remembers previous interactions
- Provides more contextual responses

### Message Processing

The bot processes incoming WhatsApp messages and:

- Marks messages as read
- Sends typing indicators
- Generates AI responses
- Handles different message types

### Error Handling

Comprehensive error handling for:

- API failures
- Network issues
- Invalid messages
- Configuration errors

## Troubleshooting

### Common Issues

1. **Webhook Verification Fails**
   - Check your VERIFY_TOKEN matches WhatsApp settings
   - Ensure your webhook URL is accessible

2. **Messages Not Received**
   - Verify webhook subscription to 'messages' event
   - Check webhook URL is correct and accessible

3. **OpenAI API Errors**
   - Verify your API key is correct
   - Check your OpenAI account has sufficient credits

4. **WhatsApp API Errors**
   - Verify all WhatsApp credentials are correct
   - Check your WhatsApp Business account status

### Logs

The application provides detailed logging. Check the console output for:

- Webhook verification attempts
- Message processing status
- API call results
- Error messages

## Security Considerations

- Keep your API keys secure and never commit them to version control
- Use HTTPS in production
- Implement rate limiting for production use
- Consider adding authentication for manual endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error messages
3. Verify your configuration
4. Create an issue in the repository

---

**Note**: This application requires active internet connectivity and valid API credentials to function properly.
