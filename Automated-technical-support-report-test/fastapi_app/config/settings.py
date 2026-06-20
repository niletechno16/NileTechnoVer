import os

# ---------------- CHATWOOT ----------------
CHATWOOT_URL = os.getenv("CHATWOOT_URL")
ACCOUNT_ID   = os.getenv("ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# ---------------- GROQ KEYS ----------------
GROQ_API_KEYS = [
    os.getenv("GROQ_KEY_1"),
    os.getenv("GROQ_KEY_2"),
    os.getenv("GROQ_KEY_3"),
    os.getenv("GROQ_KEY_4"),
    os.getenv("GROQ_KEY_5"),
]

# ---------------- GEMINI KEYS ----------------
GEMINI_API_KEYS = [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"),
    os.getenv("GEMINI_KEY_4"),
    os.getenv("GEMINI_KEY_5"),
]

# ---------------- CEREBRAS KEYS ----------------
CEREBRAS_API_KEYS = [
    os.getenv("CEREBRAS_KEY_1"),
    os.getenv("CEREBRAS_KEY_2"),
    os.getenv("CEREBRAS_KEY_3"),
    os.getenv("CEREBRAS_KEY_4"),
]

# ---------------- DATABASE ----------------
DB_SERVER   = os.getenv("DB_SERVER")
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT     = int(os.getenv("DB_PORT", "1433"))
DB_TDS_VERSION = os.getenv("DB_TDS_VERSION")
DB_CHARSET     = os.getenv("DB_CHARSET")

# ---------------- TABLE NAMES ----------------
PROBLEM_TABLE  = "customar_problem_byA"
USERS_TABLE    = "users_Details_byA"
CATEGORY_TABLE = "Problem_category_byA"

# ---------------- SIMILARITY THRESHOLD ----------------
CATEGORY_SIMILARITY_THRESHOLD = 0.70
