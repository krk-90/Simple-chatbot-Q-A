import os
import sys
import asyncio
import traceback
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request
from pydantic import BaseModel,field_validator 
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.generative_model import main

MODEL= None

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app:FastAPI):
    global MODEL
    try:
        MODEL = main()
        print("your chatbot has successfully started.")
    except Exception as e:
        print(f"error in starting your chatbot:{e}")
        raise    
    yield

app = FastAPI(title="chatbot-Q&A",version="1.0.0",lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)

class chat_input(BaseModel):
    input_messages : str

class chat_output(BaseModel):
    output_messages : str  

@app.get("/") 
def endpoint():
    return {"message":"your chatbot is ready for chat."}

@app.get("/status")
def status():
    return {
        "status": "unhealthy" if MODEL is None else "healthy",
        "model": MODEL is not None
    }

@app.post("/chat/",response_model=chat_output)
@limiter.limit("10/minute")
async def chat(request:Request,payload:chat_input):
    if MODEL is None:
        raise HTTPException(status_code= 500,detail="chatbot didn't start.")

    try:
        response_output = await asyncio.to_thread(main,payload.input_messages)
        return {"output_messages":str(response_output)}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500,detail=f"chatbot failed to reply:{e}")
