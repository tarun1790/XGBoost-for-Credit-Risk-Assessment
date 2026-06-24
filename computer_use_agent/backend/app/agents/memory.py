import os
import json
from datetime import datetime
from typing import Any
from app.core.config import settings

# Attempt to load ChromaDB
try:
    import chromadb
    HAS_CHROMA = True
except Exception:
    HAS_CHROMA = False

# Attempt to load FAISS and SentenceTransformers
HAS_FAISS = False
try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_FAISS = True
except Exception:
    pass

class MemoryAgent:
    def __init__(self):
        self.chroma_dir = settings.CHROMADB_DIR
        self.fallback_file = os.path.join(self.chroma_dir, "fallback_memory.json")
        os.makedirs(self.chroma_dir, exist_ok=True)
        
        self.client = None
        self.collection = None
        self.embed_model = None
        self.faiss_index = None
        self.faiss_metadata = []
        
        # Load ChromaDB
        if HAS_CHROMA:
            try:
                self.client = chromadb.PersistentClient(path=self.chroma_dir)
                self.collection = self.client.get_or_create_collection(name="agent_memory")
            except Exception as e:
                print(f"[Warning] Failed to start ChromaDB client: {e}. Fallback to JSON memory.")
                self.client = None
                
        # Load SentenceTransformers and FAISS
        if HAS_FAISS:
            try:
                print(f"Loading local embedding model: {settings.HF_EMBEDDING_MODEL}...")
                self.embed_model = SentenceTransformer(settings.HF_EMBEDDING_MODEL)
                # MiniLM-L6-v2 uses 384 dimensions
                self.faiss_index = faiss.IndexFlatL2(384)
                print("FAISS Index initialized successfully!")
            except Exception as e:
                print(f"[Warning] Failed to initialize FAISS: {e}")
                self.faiss_index = None
                
        if not self.client and not self.faiss_index:
            self._init_fallback_db()

    def _init_fallback_db(self):
        if not os.path.exists(self.fallback_file):
            with open(self.fallback_file, "w") as f:
                json.dump([], f)

    def _load_fallback(self) -> list:
        try:
            with open(self.fallback_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_fallback(self, data: list):
        try:
            with open(self.fallback_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving memory fallback: {e}")

    def add_episodic_memory(self, task_goal: str, action_sequence: list, is_success: bool):
        """
        Stores complete execution sequence records for future planning references.
        """
        memory_id = f"mem_{int(datetime.utcnow().timestamp())}"
        metadata = {
            "task_goal": task_goal,
            "is_success": str(is_success),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to FAISS index
        if HAS_FAISS and self.faiss_index and self.embed_model:
            try:
                embedding = self.embed_model.encode([task_goal])[0]
                vector = np.array([embedding], dtype=np.float32)
                self.faiss_index.add(vector)
                self.faiss_metadata.append({
                    "goal": task_goal,
                    "actions": action_sequence,
                    "is_success": is_success
                })
            except Exception as e:
                print(f"FAISS add failed: {e}")

        # Save to Chroma Vector DB if available
        if self.client and self.collection:
            try:
                self.collection.add(
                    documents=[json.dumps(action_sequence)],
                    metadatas=[metadata],
                    ids=[memory_id]
                )
                return
            except Exception as e:
                print(f"Chroma add error: {e}. Falling back.")
                
        # Fallback storage
        fallback_db = self._load_fallback()
        fallback_db.append({
            "id": memory_id,
            "goal": task_goal,
            "actions": action_sequence,
            "is_success": is_success,
            "timestamp": metadata["timestamp"]
        })
        self._write_fallback(fallback_db)

    def find_similar_experience(self, current_goal: str) -> list:
        """
        Queries memory to retrieve historical sequences matching the target task.
        """
        # Retrieve via FAISS first
        if HAS_FAISS and self.faiss_index and self.faiss_index.ntotal > 0 and self.embed_model:
            try:
                embedding = self.embed_model.encode([current_goal])[0]
                query_vector = np.array([embedding], dtype=np.float32)
                # Find top 2 nearest matches
                distances, indices = self.faiss_index.search(query_vector, 2)
                matches = []
                for idx in indices[0]:
                    if idx != -1 and idx < len(self.faiss_metadata):
                        match = self.faiss_metadata[idx]
                        if match["is_success"]:
                            matches.append(match["actions"])
                if matches:
                    return matches
            except Exception as e:
                print(f"FAISS search failed: {e}")

        # Retrieve via ChromaDB
        if self.client and self.collection:
            try:
                results = self.collection.query(
                    query_texts=[current_goal],
                    n_results=2
                )
                if results and results["documents"] and len(results["documents"][0]) > 0:
                    return [json.loads(doc) for doc in results["documents"][0]]
            except Exception as e:
                print(f"Chroma query error: {e}. Searching fallback.")
                
        # Fallback simple keyword search
        fallback_db = self._load_fallback()
        matches = []
        words = current_goal.lower().split()
        for mem in fallback_db:
            score = sum(1 for w in words if w in mem["goal"].lower())
            if score > 0:
                matches.append((score, mem["actions"]))
                
        # Sort matches by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:2]]

    def save_state(self, key: str, val: Any):
        """
        Stores key-value state values (e.g. login credentials, cookies location).
        """
        state_file = os.path.join(self.chroma_dir, "states.json")
        states = {}
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    states = json.load(f)
            except Exception:
                pass
        states[key] = val
        try:
            with open(state_file, "w") as f:
                json.dump(states, f, indent=2)
        except Exception as e:
            print(f"Error saving state memory: {e}")

    def get_state(self, key: str, default: Any = None) -> Any:
        state_file = os.path.join(self.chroma_dir, "states.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    states = json.load(f)
                return states.get(key, default)
            except Exception:
                pass
        return default

memory_agent = MemoryAgent()
