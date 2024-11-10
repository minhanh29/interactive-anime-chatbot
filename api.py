import string
import uvicorn
from websockets.exceptions import ConnectionClosed
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from manager.brain import BotBrain

# Initialize the chatbot's brain for processing queries
chatbot_brain = BotBrain()

# Initialize FastAPI app
app = FastAPI()

# Allow all origins to access this service for cross-origin requests
allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define root endpoint for checking app's identity
@app.get("/")
def welcome():
    return {"App Name": "Serena Bot"}


# Define health check endpoint to ensure app is running
@app.get("/health")
def health_status():
    return {"status": "good"}


# WebSocket endpoint to receive and respond to client messages
@app.websocket("/answer")
async def handle_websocket_connection(websocket: WebSocket):
    await websocket.accept()  # Accept the WebSocket connection
    try:
        while True:
            # Wait for a text message from the client
            client_query = await websocket.receive_text()
            print("Received query:", client_query)

            # Ignore empty or punctuation-only messages
            if client_query.translate(
                str.maketrans('', '', string.punctuation)
            ).strip() == "":
                continue

            # Process the query using the chatbot's brain and get an answer
            chatbot_response = chatbot_brain.answer(
                client_query.strip(),
                verbose=2
            )

            # Send the response back to the client
            await websocket.send_text(chatbot_response)

            # Update chatbot's internal knowledge after answering
            # chatbot_brain.update_knowledge(verbose=1)
    except (WebSocketDisconnect, ConnectionClosed):
        print("Client disconnected")

# Main entry point to run the application with Uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

