import os
import json
from datetime import datetime
from typing import Any
from app.core.config import settings

# Attempt to load ChromaDB, with a dictionary-based fallback if compilation fails
try:
    import chromadb
    HAS_CHROMA = True
except Exception:
    HAS_CHROMA = False

class MemoryAgent:
    def __init__(self):
        self.chroma_dir = settings.CHROMADB_DIR
        self.fallback_file = os.path.join(self.chroma_dir, "fallback_memory.json")
        os.makedirs(self.chroma_dir, exist_ok=True)
        
        self.client = None
        self.collection = None
        
        if HAS_CHROMA:
            try:
                self.client = chromadb.PersistentClient(path=self.chroma_dir)
                self.collection = self.client.get_or_create_collection(name="agent_memory")
            except Exception as e:
                print(f"[Warning] Failed to start ChromaDB client: {e}. Fallback to JSON memory.")
                self.client = None
                
        if not self.client:
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
        if self.client and self.collection:
            try:
                # Query Chroma using goal text
                results = self.collection.query(
                    query_texts=[current_goal],
                    n_results=2
                )
                if results and results["documents"] and len(results["documents"][0]) > 0:
                    # Return parsed JSON documents list
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
