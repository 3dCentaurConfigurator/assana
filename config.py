import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_ASSISTANT_ID = os.getenv('OPENAI_ASSISTANT_ID')
    
    # WhatsApp Business API Configuration
    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
    PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
    WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
    WHATSAPP_BUSINESS_APP_ID = os.getenv('WHATSAPP_BUSINESS_APP_ID')
    VERSION = os.getenv('VERSION', 'v18.0')
    
    # WhatsApp API URLs
    WHATSAPP_API_URL = f"https://graph.facebook.com/{VERSION}"
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # AI Script Configuration - Assana Clinic Specific
    BUSINESS_NAME = os.getenv('BUSINESS_NAME', 'Assana Clinic')
    BUSINESS_DESCRIPTION = os.getenv('BUSINESS_DESCRIPTION', 'Leading multi-specialty clinic providing comprehensive healthcare services with state-of-the-art facilities and expert medical professionals')
    
    # Clinic Services and Departments
    KEY_SERVICES = os.getenv('KEY_SERVICES', 'Cardiology, Neurology, Orthopedics, Pediatrics, Gynecology, General Surgery, Emergency Medicine, Diagnostic Imaging, Laboratory Services, Pharmacy')
    
    # Clinic Details
    CLINIC_ADDRESS = os.getenv('CLINIC_ADDRESS', '123 Medical Center Drive, Healthcare District')
    CLINIC_PHONE = os.getenv('CLINIC_PHONE', '+1-555-123-4567')
    CLINIC_EMAIL = os.getenv('CLINIC_EMAIL', 'info@assanaclinic.com')
    CLINIC_WEBSITE = os.getenv('CLINIC_WEBSITE', 'www.assanaclinic.com')
    
    # Operating Hours
    EMERGENCY_HOURS = os.getenv('EMERGENCY_HOURS', '24/7 Emergency Services Available')
    OPD_HOURS = os.getenv('OPD_HOURS', 'Monday to Friday: 8:00 AM - 8:00 PM, Saturday: 8:00 AM - 6:00 PM, Sunday: 9:00 AM - 5:00 PM')
    
    # Special Features
    SPECIAL_FEATURES = os.getenv('SPECIAL_FEATURES', 'Advanced ICU, Modern Operating Theaters, Digital X-Ray, MRI, CT Scan, Ultrasound, 24/7 Ambulance Service, Online Appointment Booking')
    
    # Insurance and Payment
    INSURANCE_INFO = os.getenv('INSURANCE_INFO', 'We accept most major insurance plans. Cash, credit cards, and payment plans available. Contact billing department for details.')
    
    # Response Style
    RESPONSE_STYLE = os.getenv('RESPONSE_STYLE', 'professional, caring, and empathetic')
    
    # Clinic Mission and Values
    CLINIC_MISSION = os.getenv('CLINIC_MISSION', 'To provide exceptional healthcare services with compassion, innovation, and excellence, ensuring the well-being of our community')
    CLINIC_VALUES = os.getenv('CLINIC_VALUES', 'Patient-Centered Care, Medical Excellence, Innovation, Compassion, Integrity, Community Service')
