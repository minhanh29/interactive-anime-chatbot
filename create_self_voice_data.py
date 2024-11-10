from multiprocessing import Process, Queue, Pipe, Manager, Value
from character.visual.video_renderer import render_video
from time import time


def create_data(queue):
    from character.agent import MyCharacter
    character = MyCharacter("./data/character/", queue)

    from threading import Thread
    import asyncio
    from queue import Queue
    input_queue = Queue()

    async def connect_to_server():
        with open("../SelfVoice/transcripts.txt", "r") as f:
            data = f.readlines()

        for line in data:
            character.speak(line.strip())

    t = Thread(target=character.listen, args=(input_queue,))
    t.start()
    asyncio.get_event_loop().run_until_complete(connect_to_server())
    t.join()


if __name__ == "__main__":
    queue = Queue()
    manager = Manager()
    frame = manager.Value('frame', None)
    create_data(frame)
