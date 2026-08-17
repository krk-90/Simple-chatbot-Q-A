import time
from google.genai.errors import ServerError
from google import genai 
import os
from dotenv import load_dotenv
import glob
from pathlib import Path


class model:
    def __init__(self, google_api_key: str | None = None):
        self.__google_api_key = google_api_key

    def create_client(self):
        self.client = genai.Client(api_key = self.__google_api_key)  
        return self.client 

    def chat_input(self,chat = None,input_message = str):
        self.response = chat.send_message(input_message)
        return self.response

def main(message="hi,say a poem in one line") -> str:
    path = glob.glob("**/.env",recursive=True)
    if not path:
         raise FileNotFoundError(".env file not found,create one.")
    env_path = Path(path[0])

    load_dotenv(dotenv_path=env_path)
    google_key = os.getenv(key="GOOGLE_API_KEY")
    if not google_key:
        raise ValueError("goole_api_key not found- check yoour .env")
    
    llm_model= model(google_api_key=google_key)
    client = llm_model.create_client()
    chat = client.chats.create(model="gemini-flash-latest",config={
        "max_output_tokens": 1024,
        "temperature": 0.4
    })
    retries = 4
    for attempt in range(retries):
        try:
            response = llm_model.chat_input(chat=chat,input_message=message)
            return response.text
        except ServerError as e:
            if e.code == 503:
                wait = 2 ** attempt
                print(f"Model busy, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Model unavailable after retries")                        

if __name__ == "__main__":
   main()