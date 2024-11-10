from multiprocessing import Process, Queue, Pipe, Manager, Value
from character.visual.video_renderer import render_video
from character.agent import MyCharacter
import string
from threading import Thread
import asyncio
import websockets


CHARACTER_DIR = "./data/character"


def character_interaction(frame_queue):
    """
    Function to handle character interaction logic, processing user input
    and responding through WebSocket connection.

    Args:
        frame_queue (Queue): Shared queue for communication between processes.
    """
    # Initialize the character with the data path and the shared queue
    character = MyCharacter(CHARACTER_DIR, frame_queue)

    # Queue to store user input
    user_input_queue = Queue()

    # WebSocket server URL for interaction
    websocket_server_url = 'ws://localhost:8000/answer'

    async def handle_websocket_connection():
        """
        Async function to manage WebSocket connection and communicate
        with the server based on user input.
        """
        # Connect to WebSocket server
        websocket = await websockets.connect(websocket_server_url, ping_interval=None)

        while True:
            # Check if there is any user input in the queue
            if user_input_queue.empty():
                await asyncio.sleep(0.5)  # Wait before checking again
                continue

            # Retrieve the query from the input queue
            user_query = user_input_queue.get()

            # Ignore input if it's empty or contains only punctuation
            if user_query.translate(str.maketrans('', '', string.punctuation)).strip() == "":
                continue

            print("You:", user_query)
            lower_query = user_query.strip().lower()

            # Check if the user wants to exit the conversation
            if ("exit" in lower_query and "please" in lower_query) or lower_query == "exit":
                character.stop()
                print("Exiting conversation...")
                break

            character.thinking()  # Character starts thinking animation

            # Attempt to send the query and receive the response from the server
            for _ in range(2):
                try:
                    await websocket.send(user_query)  # Send user query to the server
                    server_response = await websocket.recv()  # Receive response from the server
                    print("Bot:", server_response)
                    break
                except:
                    # Reconnect WebSocket in case of an error
                    websocket = await websockets.connect(websocket_server_url, ping_interval=None)
                    server_response = "Sorry, there is an error connecting to the server."
                    print("Reconnecting WebSocket...")

            # Character speaks the received response
            character.speak(server_response)

        # Close WebSocket connection
        await websocket.close()
        print("WebSocket connection closed")

    # Start a new thread to listen for user input and put it into the queue
    input_listener_thread = Thread(target=character.listen, args=(user_input_queue,))
    input_listener_thread.start()

    # Run the WebSocket communication in the event loop
    asyncio.get_event_loop().run_until_complete(handle_websocket_connection())

    # Wait for the input listener thread to finish
    input_listener_thread.join()


if __name__ == "__main__":
    # Create a queue for inter-process communication
    frame_queue = Queue()

    # Manager to handle shared state between processes
    manager = Manager()

    # Shared variable for the current video frame
    current_frame = manager.Value('frame', None)

    # Process for character interaction
    interaction_process = Process(target=character_interaction, args=(current_frame,))

    # Process for rendering the character's video
    rendering_process = Process(target=render_video, args=(CHARACTER_DIR, current_frame))

    # Start both processes
    rendering_process.start()
    interaction_process.start()

    # Wait for both processes to complete
    rendering_process.join()
    interaction_process.join()

