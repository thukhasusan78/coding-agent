import chromadb
import uuid
import os
from google import genai
from chromadb import Documents, EmbeddingFunction, Embeddings
from src.core.key_manager import KeyManager
from config.settings import settings

# 🔥 Custom Embedding Function using Gemini API (No PyTorch/Local RAM usage)
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.key_manager = KeyManager()

    def __call__(self, input: Documents) -> Embeddings:
        # Key Rotation သုံးပြီး Embedding ယူမယ်
        client = self.key_manager.get_client()
        response = client.models.embed_content(
            model="text-embedding-004", # Lightweight & Fast
            contents=input
        )
        # Gemini Return format ကို Chroma နဲ့ ကိုက်အောင် ညှိမယ်
        return [e.values for e in response.embeddings]

class VectorDB:
    def __init__(self, path="workspace/chroma_db"):
        # Initialize ChromaDB (Persistent)
        self.client = chromadb.PersistentClient(path=path)
        
        # 🔥 FIX: Use Google Cloud Embeddings instead of Local Heavy Model
        self.embedding_fn = GeminiEmbeddingFunction()
        
        # Collections (Knowledge Base)
        self.code_collection = self.client.get_or_create_collection(
            name="codebase",
            embedding_function=self.embedding_fn
        )
        self.notes_collection = self.client.get_or_create_collection(
            name="notes",
            embedding_function=self.embedding_fn
        )
        print(f"🧠 VectorDB Loaded (Cloud Embeddings): {path}")

    def add_code_knowledge(self, file_path: str, content: str):
        """
        Code ဖိုင်တစ်ခုလုံးကို မှတ်ဉာဏ်ထဲထည့်မယ်
        """
        doc_id = str(uuid.uuid4())
        self.code_collection.add(
            documents=[content],
            metadatas=[{"source": file_path}],
            ids=[doc_id]
        )

    def search_relevant_code(self, query: str, n_results=3):
        """
        မေးခွန်းနဲ့ ဆီလျော်တဲ့ ကုဒ်တွေကို ပြန်ရှာပေးမယ် (RAG)
        """
        results = self.code_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        if results['documents']:
            return results['documents'][0] 
        return []

    def save_note(self, note: str):
        self.notes_collection.add(
            documents=[note],
            metadatas=[{"type": "user_note"}],
            ids=[str(uuid.uuid4())]
        )

# Global Instance
vector_db = VectorDB()