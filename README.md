# Simple Chatbot Q&A

A minimal FastAPI backend that wraps Google's Gemini API for chat, with conversation history stored in MySQL.

## Features

- `POST /chat/` — send a message, get a Gemini-generated reply, both stored in MySQL
- `GET /status` — check whether the model loaded successfully
- `GET /db-check` — check the database connection and list tables
- Rate limiting (10 requests/minute per client) via `slowapi`
- Retry-with-backoff on Gemini `503` (model busy) errors

## Project Structure

```
.
├── backend/
│   └── router.py           # FastAPI app, endpoints, DB access
├── src/
│   └── generative_model.py # Gemini client wrapper
└── .env                    # environment config (not committed)
```

## Requirements

- Python 3.10+
- A running MySQL server (local or remote)
- A Google Gemini API key ([Google AI Studio](https://aistudio.google.com/apikey))

Install dependencies:

```bash
pip install fastapi uvicorn mysql-connector-python python-dotenv slowapi google-genai
```

## Database Setup

Create the database and table before starting the app:

```sql
CREATE DATABASE IF NOT EXISTS chatbot_history;

USE chatbot_history;

CREATE TABLE chat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```


## Environment Variables

Create a `.env` file in the project root or rename .env.example as .env and set below detials:

```dotenv
GOOGLE_API_KEY=your_gemini_api_key_here

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=chatbot_history
DB_PORT=3306
```

## Running

```bash
uvicorn backend.router:app --reload --port 8000
```

Then open:
- http://127.0.0.1:8000/docs — interactive Swagger UI
- http://127.0.0.1:8000/status — model health check
- http://127.0.0.1:8000/db-check — database health check

## Example Request

```json
POST /chat/
{
  "user_id": 2,
  "role": "user",
  "input_messages": "how to cook soup"
}
```

`role` should always be `"user"` when calling from a client — the server hardcodes `"assistant"` for the model's own reply, so that part isn't client-controlled.

Response:

```json
{
  "id": 3,
  "user_id": 2,
  "role": "assistant",
  "output_messages": "Cooking soup is one of the easiest...",
  "time_stamp": "2026-08-20 10:43:22"
}
```
# Working Fastapi for locally:

![Chatbot demo](screen_shot/011.png)
![Chatbot demo](screen_shot/010.png)

# Evalution of chatbot:

![Chatbot demo](screen_shot/009.png)