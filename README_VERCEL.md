# Vercel Deployment Guide for WhatsApp OpenAI Bot

This guide explains how to deploy your WhatsApp OpenAI Bot to Vercel.

## Project Structure for Vercel

```
APITest08/
├── api/
│   └── index.py          # Main Vercel serverless function
├── config.py             # Configuration file
├── openai_service.py     # OpenAI integration
├── whatsapp_service.py   # WhatsApp Business API integration
├── updated_openai_instructions.md
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies
├── runtime.txt           # Python version specification
├── .vercelignore         # Files to ignore during deployment
└── README_VERCEL.md      # This file
```

## Environment Variables Required

Set these environment variables in your Vercel project:

### Required Variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `ACCESS_TOKEN` - WhatsApp Business API access token
- `VERIFY_TOKEN` - WhatsApp webhook verification token
- `PHONE_NUMBER_ID` - WhatsApp Business API phone number ID
- `BUSINESS_ACCOUNT_ID` - WhatsApp Business Account ID

### Database Variables:
- `DB_HOST` - PostgreSQL host
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password

### Optional Variables:
- `DEBUG` - Set to "False" for production
- `BUSINESS_NAME` - Your business name (default: "Assana Colorectal & Gut Wellness")

## Deployment Steps

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from project directory**:
   ```bash
   vercel --prod
   ```

4. **Set Environment Variables**:
   - Go to your Vercel dashboard
   - Select your project
   - Go to Settings → Environment Variables
   - Add all required environment variables

5. **Update WhatsApp Webhook URL**:
   - Use your Vercel domain: `https://your-project.vercel.app/webhook`
   - Update this in your WhatsApp Business API configuration

## Key Differences from Local Deployment

1. **Serverless Architecture**: Vercel uses serverless functions, so each request starts fresh
2. **No Background Processes**: Long-running processes aren't supported
3. **Stateless**: No persistent memory between requests
4. **Cold Starts**: First request might be slower due to function initialization

## File Explanations

- **`vercel.json`**: Configures Vercel deployment settings and routes
- **`api/index.py`**: Main application entry point for Vercel
- **`.vercelignore`**: Excludes unnecessary files from deployment
- **`runtime.txt`**: Specifies Python version for Vercel

## Testing Your Deployment

1. Visit `https://your-project.vercel.app/` to check if the app is running
2. Test the health endpoint: `https://your-project.vercel.app/health`
3. Send a test message via WhatsApp to verify webhook functionality

## Monitoring and Logs

- View logs in Vercel dashboard under Functions tab
- Monitor performance and errors in the Vercel analytics

## Troubleshooting

1. **Function Timeout**: Increase `maxDuration` in vercel.json if needed
2. **Import Errors**: Ensure all dependencies are in requirements.txt
3. **Environment Variables**: Double-check all required variables are set
4. **Database Connection**: Verify database credentials and whitelist Vercel IPs

## Support

For issues specific to:
- Vercel deployment: Check Vercel documentation
- WhatsApp Business API: Check Meta Developer documentation
- OpenAI integration: Check OpenAI API documentation
