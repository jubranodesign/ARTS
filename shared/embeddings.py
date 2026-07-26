from langchain_google_genai import GoogleGenerativeAIEmbeddings

EMBEDDING_MODEL_NAME = "gemini-embedding-001"
EMBEDDING_MODEL_VERSION = "v1"


def get_embeddings_model():
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL_NAME, version=EMBEDDING_MODEL_VERSION
    )
