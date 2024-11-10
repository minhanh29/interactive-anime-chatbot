import pika, sys, os
import json
from mutation import MutationEngine, EventEngine


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='mutation')
    mutation_engine = MutationEngine()
    event_engine = EventEngine()

    def callback(ch, method, properties, body):
        print(f" [x] Received {body}")
        print("Start Mutation...")
        body = json.loads(body)
        new_info = mutation_engine.select_info(
            dialog=body["dialog"],
            old_knowledge=body["old_knowledge"],
            verbose=1
        )
        mutation_engine.create(new_info=new_info, verbose=1)
        event_engine.create(
            dialog=body["dialog"],
            knowledge=body["old_knowledge"],
            verbose=1
        )
        print("Donw Mutation.")

    channel.basic_consume(queue='mutation', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

