from fastapi import FastAPI
from dotenv import load_dotenv
import gradio as gr
import requests

load_dotenv()

from app.routers import rag, ingest

app = FastAPI(
    title="FastAPI RAG Practice",
    description="A minimal project to learn RAG with FastAPI.",
    version="0.1.0",
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(rag.router)
app.include_router(ingest.router)

# Gradio Chat Interface
def predict(message, history):
    """
    Sends the user's message to the RAG API and returns the answer.
    """
    try:
        response = requests.get("http://127.0.0.1:8001/rag/search", params={"q": message})
        response.raise_for_status()
        data = response.json()

        answer = data.get("answer", "No answer found.")
        results = data.get("results", [])

        # Format sources
        sources_text = "\n\n**Sources:**\n"
        for i, res in enumerate(results):
            score = res.get("score", 0)
            text = res.get("text", "").strip()
            # Truncate text if it's too long for display
            display_text = text[:200] + "..." if len(text) > 200 else text
            sources_text += f"{i+1}. (Score: {score:.4f}) {display_text}\n"

        return answer + sources_text

    except requests.exceptions.RequestException as e:
        return f"Error communicating with RAG API: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# Create the Gradio Chat Interface
demo = gr.ChatInterface(
    fn=predict,
    title="RAG Chatbot",
    description="Ask questions about your knowledge base.",
)

# Mount Gradio app to FastAPI
app = gr.mount_gradio_app(app, demo, path="/gradio")
