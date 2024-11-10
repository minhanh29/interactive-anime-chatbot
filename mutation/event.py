from prompts.mutation import MEMORY_EVENT, IMPORTANCE_SCORE
from llm.factory import Factory
from query.semantic_search import SemanticSearch


class EventEngine:
    def create(self, dialog, knowledge, verbose=0):
        prompt = MEMORY_EVENT.format(
            knowledge=knowledge,
            dialog=dialog
        )

        if verbose >= 2:
            print(prompt)

        output = Factory.llm.complete(prompt)
        output = "<memory>" + output.text.strip()
        if verbose >= 2:
            print(output)

        open_tag = "<memory>"
        end_tag = "</memory>"
        memories = []
        while True:
            start_idx = output.find(open_tag)
            end_idx = output.find(end_tag)
            if start_idx == -1 or end_idx == -1:
                break
            memories.append(output[start_idx + len(open_tag):end_idx].strip())
            output = output[end_idx + len(end_tag):]

        for memory in memories:
            if memory.strip() == "":
                continue
            prompt = IMPORTANCE_SCORE.format(
                memory=memory
            )

            if verbose >= 2:
                print(prompt)

            output = Factory.llm.complete(prompt)
            output = output.text.strip()
            if verbose >= 2:
                print(output)

            end_idx = output.find("</rate>")
            if end_idx == -1:
                print("Cannot rate memory", memory)
                continue

            rate = float(output[:end_idx].strip())
            SemanticSearch.insert(memory, rate)
