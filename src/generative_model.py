import time
from google.genai.errors import ServerError
from google import genai 
import os
from dotenv import load_dotenv
import glob
from pathlib import Path


class GenerativeModel:
    def __init__(self, google_api_key: str | None = None):
        self.__google_api_key = google_api_key
        self.client = None

    def create_client(self):
        self.client = genai.Client(api_key = self.__google_api_key)  
        return self.client 

    def send_message(self, input_message: str, model_name: str = "gemini-flash-latest",retries = 4):
            if self.client is None:
                self.create_client()
            chat = self.client.chats.create(model=model_name,config={
                    "max_output_tokens": 1024,
                    "temperature": 0.4
                })

            for attempt in range(retries):
                try:
                    response = chat.send_message(input_message)
                    return response.text
                except ServerError as e:
                    if e.code == 503:
                        wait = 2 ** attempt
                        print(f"Model busy, retrying in {wait}s...")
                        time.sleep(wait)
                    else:
                        raise
            raise RuntimeError("Model unavailable after retries")

def load_api_key() ->str:
    path = glob.glob("**/.env", recursive=True)
    if not path:
        raise FileNotFoundError(
            ".env file not found. Copy .env.example to .env and add your GOOGLE_API_KEY."
        )
    env_path = Path(path[0])
    load_dotenv(dotenv_path=env_path)
 
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        raise ValueError("GOOGLE_API_KEY not found - check your .env file.")
    return google_key

def build_model() -> GenerativeModel:
    google_key = load_api_key()
    llm_model = GenerativeModel(google_api_key=google_key)
    llm_model.create_client()
    return llm_model
 

def main(message="hi,say a poem in one line") -> str:
    llm_model= build_model()
    return llm_model.send_message(message)  

if __name__ == "__main__":
   main()