import pika
import json
from time import time
from queue import Queue
from threading import Thread
from datetime import datetime
from .history import HistoryManager
from query import PlanningEngine
from mutation import MutationEngine, EventEngine
from prompts.response import RESPONSE_GENERATION
from prompts.classification import CLASSIFICATION_QUERY
from prompts.mutation import CONTEXT_SUMMARY
from llm.factory import Factory
from database import EntityDao
from config import settings
from utils.custom_thread import ThreadWithReturnValue


class BotBrain:
    def __init__(self):
        bot_info = EntityDao.get_by_id(settings.BOT_ENTITY_ID)
        self.bot_name = bot_info["name"]
        self.system_prompt = bot_info["description"]
        self.history_manager = HistoryManager(bot_name=self.bot_name, max_messages=10)
        self.planning_engine = PlanningEngine()
        self.mutation_engine = MutationEngine()
        self.event_engine = EventEngine()
        self.context = []
        self.prev_context = ""
        self.mutation_queue = Queue()
        self.response_queue = Queue()

    def answer(self, user_input, speaker="Isaac Nguyen", verbose=0):
        if not self.mutation_queue.empty():
            self.prev_context = self.mutation_queue.get()
            self.history_manager.done_mutation()

        user_input = user_input.strip()
        if user_input == "":
            return ""

        # classification_thread = ThreadWithReturnValue(target=self.classify, args=(
        #     user_input,
        #     speaker,
        #     self.response_queue,
        #     verbose
        # ))
        # classification_thread.start()

        full_flow_thread = ThreadWithReturnValue(target=self.full_flow, args=(
            user_input,
            speaker,
            self.response_queue,
            verbose
        ))
        full_flow_thread.start()

        # category, bot_answer = classification_thread.join()
        # if "common" not in category:
        #     bot_answer = full_flow_thread.join()
        bot_answer = full_flow_thread.join()

        self.history_manager.add_user_message(user_input)
        self.history_manager.add_bot_message(bot_answer)

        return bot_answer

    def full_flow(self, user_input, speaker, response_queue, verbose=0):
        # get the context to answer
        history = self.history_manager.to_string()
        context = self.prev_context + "\n" + "\n".join(self.context)
        context, relevances, importances = self.planning_engine.query(
            bot_name=self.bot_name,
            prev_context=context.strip(),
            history=history,
            question=user_input,
            speaker=speaker,
            response_queue=response_queue,
            verbose=verbose
        )
        if context is None:
            return ""

        self.context.extend(context)
        self.context = list(set(self.context))
        context = "\n".join(self.context)
        if self.prev_context != "":
            context = self.prev_context + "\n" + context
        if verbose >= 1:
            print("-------- Full context --------")
            print(context)

        if len(importances) > 0:
            context += "\n" + "\n".join(importances)

        # generate answer
        prompt = RESPONSE_GENERATION.format(
            system_prompt=self.system_prompt,
            current_time=str(datetime.now().strftime("%d %B, %Y, %H:%M:%S")),
            context=context.strip(),
            events="\n".join(relevances),
            history=self.history_manager.to_string_for_response(),
            speaker=speaker,
            user_input=user_input
        )

        if verbose >= 2:
            print(prompt)
        output = Factory.invoke_llm_with_stop_sequence(prompt, stop_sequences=["</answer>"])
        if verbose >= 2:
            print(output)
        # output = output.text.strip()
        output = output.strip()
        start_i = output.find("<answer>") + len("<answer>")
        # end_i = output.find("</answer>")
        bot_answer = output[start_i:].replace("<name>", "").replace("</name>", "").strip()
        return bot_answer

    def classify(self, user_input, speaker, response_queue, verbose=0):
        entities = EntityDao.get_all()
        entities_str = ", ".join([x["name"] for x in entities])
        # generate answer
        prompt = CLASSIFICATION_QUERY.format(
            system_prompt=self.system_prompt,
            current_time=str(datetime.now().strftime("%d %B, %Y, %H:%M:%S")),
            entities=entities_str,
            history=self.history_manager.to_string_for_response(),
            speaker=speaker,
            user_input=user_input
        )

        if verbose >= 2:
            print(prompt)
        output = Factory.invoke_llm_with_stop_sequence(prompt, stop_sequences=["</answer>"])
        if verbose >= 2:
            print(output)
        # output = output.text.strip()
        start_i = output.find("<category>") + len("<category>")
        end_i = output.find("</category>")
        category = output[start_i:end_i].strip()
        print("*" * 10)
        print(f"{category}")
        print("*" * 10)

        response_queue.put(category)
        if "common" not in category:
            return category, ""

        start_i = output.find("<answer>") + len("<answer>")
        # end_i = output.find("</answer>")
        answer = output[start_i:].strip()
        return category, answer

    def update_knowledge(self, force=False, verbose=0):
        if not force and not self.history_manager.need_mutation():
            return

        dialog = self.history_manager.to_string()
        old_knowledge = self.system_prompt.strip() + "\n" + "\n".join(self.context).strip()

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='mutation')

        channel.basic_publish(
            exchange='',
            routing_key='mutation',
            body=json.dumps({
                "dialog": dialog,
                "old_knowledge": old_knowledge
            })
        )
        connection.close()
        # Thread(target=self._update_knowledge, args=(
        #     dialog,
        #     old_knowledge,
        #     self.mutation_queue,
        #     verbose
        # )).start()

        # Thread(target=self.event_engine.create, args=(
        #     dialog,
        #     old_knowledge,
        #     verbose
        # )).start()

    def _update_knowledge(self, dialog, old_knowledge, queue, verbose):
        print("Start Mutation...")
        new_info = self.mutation_engine.select_info(
            dialog=dialog,
            old_knowledge=old_knowledge,
            verbose=verbose
        )
        self.mutation_engine.create(new_info=new_info, verbose=verbose)

        # summarize the current context
        prompt = CONTEXT_SUMMARY.format(
            context=old_knowledge,
            dialog=dialog
        )

        if verbose >= 2:
            print()
            print(prompt)
        output = Factory.llm.complete(prompt)
        if verbose >= 2:
            print(output)

        output = output.text.strip()
        self.mutation_queue.put(output)
        print("Done Mutation...")
