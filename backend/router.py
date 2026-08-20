import os
import sys,glob
import asyncio
from dotenv import load_dotenv
import traceback
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request
from pydantic import BaseModel,field_validator 
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import mysql.connector

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.generative_model import build_model,GenerativeModel

def load_api_key() ->str:
    path = glob.glob("**/.env", recursive=True)
    if not path:
        raise FileNotFoundError(
            ".env file not found. Copy .env.example to .env and add your GOOGLE_API_KEY."
        )
    env_path = Path(path[0])
    load_dotenv(dotenv_path=env_path)
 
    local_host = os.getenv("local_host")
    your_user = os.getenv("your_user")
    your_password = os.getenv("your_password")
    chatbot_history = os.getenv("chatbot_history")
    port=int(os.getenv("port", 3306))
    if not (local_host and your_password and your_user and chatbot_history and port):
        raise ValueError("Database credentials not found - check your .env file.")
    return local_host,your_user,your_password,chatbot_history,port

local_host,your_user,your_password,chatbot_history,port = load_api_key()
database = mysql.connector.connect(
    host = local_host,
    user = your_user,
    password = your_password,
    database = chatbot_history,
    port=port,
    autocommit=True,
)
cursor = database.cursor(dictionary=True)    

MODEL : GenerativeModel | None = None

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app:FastAPI):
    global MODEL
    try:
        MODEL = build_model()
        print("your chatbot has successfully started.")
    except Exception as e:
        print(f"error in starting your chatbot:{e}")
        raise    
    yield

app = FastAPI(title="chatbot-Q&A",version="1.0.0",lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)

class chat_input(BaseModel):
    user_id : int
    role:str
    input_messages : str

class chat_output(BaseModel):
    id:int
    user_id:int
    role:str
    output_messages : str  
    time_stamp:str

@app.get("/") 
def endpoint():
    return {"message":"your chatbot is ready for chat."}

@app.get("/status")
def status():
    return {
        "status": "unhealthy" if MODEL is None else "healthy",
        "model": MODEL is not None
    }

@app.get("/db-check")
def db_check():
    cursor.execute("SHOW TABLES;")
    return {"tables": cursor.fetchall()}


@app.post("/chat/",response_model=chat_output)
@limiter.limit("10/minute")
async def chat(request:Request,payload:chat_input):
    if MODEL is None:
        raise HTTPException(status_code= 500,detail="chatbot didn't start.")

    try:
        response_output = await asyncio.to_thread(MODEL.send_message,payload.input_messages)

        cursor.execute("INSERT INTO chat (user_id, role, message) VALUES (%s, %s, %s)",
            (payload.user_id, payload.role, payload.input_messages))
        database.commit()

        cursor.execute(
            "INSERT INTO chat (user_id, role, message) VALUES (%s, %s, %s)",
            (payload.user_id, "assistant", str(response_output)))
        database.commit()

        cursor.execute("""DELETE FROM chat WHERE id NOT IN (SELECT id FROM (SELECT id FROM chat ORDER BY id DESC LIMIT 20) AS recent)""")
        database.commit()

        cursor.execute("SELECT * FROM chat ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "role": row["role"],
            "output_messages": row["message"],
            "time_stamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500,detail=f"chatbot failed to reply:{e}")
