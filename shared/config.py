import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_mistralai import ChatMistralAI

load_dotenv()

# 2. הגדרות נתיבים
# כאן אתה שם את הנתיב לפרויקט שאתה רוצה לסרוק
REPO_PATH = r"C:\Users\Remah\OneDrive\Documents\interview\coveredhealth"
REPO_SEED_PATH = r"C:\Users\Remah\OneDrive\Documents\interview\coveredhealth\seed_data"
TEST_FRAMEWORK = "pytest"
MOCK_TOOL = "unittest.mock"

# הגדרות מודלים
EMBEDDING_MODEL_NAME = "gemini-embedding-001"
EMBEDDING_MODEL_VERSION = "v1"
LLM_MODEL_NAME = "gemini-2.5-flash"


# dirname פעמיים כדי לעלות רמה אחת מעל תיקיית shared
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTOR_STORE_PATH = os.path.join(DATA_DIR, "vector_store")

# --- החלק החשוב שמונע שגיאות ---
# פקודה שיוצרת את תיקיית data אם היא לא קיימת
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"📁 Created missing directory: {DATA_DIR}")

# פונקציה שתחזיר לנו את ה-Embedding (כדי שלא נאתחל כל פעם ידנית)
def get_embeddings_model():
    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL_NAME, version=EMBEDDING_MODEL_VERSION)
    # return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_model(provider: str = "groq", temperature: float = 0):
    """
    Factory function להחזרת מודל LLM לפי ספק.
    """
    
    if provider == "groq":
        return ChatGroq(
            # model_name="qwen/qwen3-32b",
            # model_name="llama-3.3-70b-versatile",
            # model_name="llama-3.1-8b-instant",
            # model_name="openai/gpt-oss-20b",
            model_name="openai/gpt-oss-120b",
            temperature=temperature,
            max_tokens=4096
        )
        
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=temperature
        )
        
    elif provider == "deepseek":
        # return ChatDeepSeek(
        #         model="deepseek-chat", 
        #         temperature=0
        # )

        # DeepSeek עובד הכי טוב דרך ה-SDK של OpenAI או המחלקה היעודית
        return ChatOpenAI(
            model='deepseek-chat', 
            openai_api_base='https://api.deepseek.com/v1', # או ה-URL של הספק שלך
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            max_tokens=2048,
            temperature=temperature,
            tiktoken_model_name='gpt-4o'
        )
        
    elif provider == "ollama":
        return ChatOllama(
            model="llama3.2:3b",
            # model = "qwen2.5-coder:3b",
            # model = "gemma2:9b",
            temperature=temperature,
            num_ctx=8192
        )

    elif provider == "mistral":
        return ChatMistralAI(
            model="codestral-latest",
            temperature=0
         )

    elif provider == "open_router":
        return ChatOpenAI(
        # המודל החינמי של Qwen 3 (בדוק את השם המדויק באתר שלהם, לרוב זה :free)
        # model="qwen/qwen3-coder:free",
        model="google/gemini-3-flash-preview",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
        # זה יפתור את אזהרת ה-GPT-2 וה-NotImplementedError
        tiktoken_model_name="gpt-4o" 
    )
    
    elif provider == "github":
        return ChatOpenAI(
        base_url="https://models.inference.ai.azure.com",
        # model="gpt-4o-mini"
        model="gpt-4o"
        # model="meta-llama/llama-3.3-70b-versatile"
    )

    # ברירת מחדל במידה ולא נמצא ספק
    raise ValueError(f"Provider {provider} is not supported.")


def setup_node_llm(config, tools=None):
    """
    מחלצת את ה-provider מהקונפיגורציה, מאתחלת את המודל ומצמידה כלים אם יש.
    """
    # 1. שליפת ה-Provider
    configurable = config.get("configurable", {})
    provider = configurable.get("model_provider", "groq")
    print(f"📁 setup_node_llm provider: {provider}")

    # 2. קבלת המופע מה-Factory (הפונקציה שבנית קודם)
    llm = get_model(provider)
    
    # 3. הצמדת כלים רק אם הועברו כאלו
    if tools:
        return llm.bind_tools(tools)
    
    return llm