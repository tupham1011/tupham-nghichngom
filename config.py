import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AI Agent Configuration
# Hướng dẫn lấy key: https://aistudio.google.com/app/apikey

# API Key loaded from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")
GEMINI_API_KEY_3 = os.getenv("GEMINI_API_KEY_3")
GEMINI_API_KEY_4 = os.getenv("GEMINI_API_KEY_4")
GEMINI_API_KEY_5 = os.getenv("GEMINI_API_KEY_5")
GEMINI_API_KEY_7 = os.getenv("GEMINI_API_KEY_7")
GEMINI_API_KEY_8 = os.getenv("GEMINI_API_KEY_8")

# Key Rotation Strategy: 1 >> 7 >> 8 >> 5 >> 4 >> 2 >> 3 (User requested Key 1 priority)
GEMINI_KEYS = [
    k for k in [
        GEMINI_API_KEY,
        GEMINI_API_KEY_7, 
        GEMINI_API_KEY_8,
        GEMINI_API_KEY_5,
        GEMINI_API_KEY_4, 
        GEMINI_API_KEY_2, 
        GEMINI_API_KEY_3
    ] 
    if k
]
DEFAULT_GEMINI_KEY = GEMINI_KEYS[0] if GEMINI_KEYS else None
# 'gemini-1.5-flash' là model ổn định và nhanh nhất hiện nay
# 'gemini-2.0-flash' là model thế hệ mới (cần kiểm tra quyền truy cập của API Key)
DEFAULT_MODEL = "gemini-2.5-flash"

# Facebook Configuration
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FACEBOOK_AD_ACCOUNT_ID = os.getenv("FACEBOOK_AD_ACCOUNT_ID")
FACEBOOK_PIXEL_ID = os.getenv("FACEBOOK_PIXEL_ID")
FACEBOOK_LAL_5_AUDIENCE_ID = os.getenv("FACEBOOK_LAL_5_AUDIENCE_ID")
FACEBOOK_EXCLUDE_AUDIENCE_ID = os.getenv("FACEBOOK_EXCLUDE_AUDIENCE_ID")

# Agent 3.1 Crawler Configuration
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

# CRM Column Mappings (Heuristic/Fixed)
CRM_COL_PHONE = "phone"
CRM_COL_EMAIL = "email"
CRM_COL_STATUS = "level"
CRM_COL_VALUE = "value"
