# import json
import yaml
from database import YourSelfDao
from prompts.yourself import YOURSELF_ATTRIBUTE_SELECTION
from llm.factory import Factory


class PeopleQueryEngine:
    def query(self, history, question):
        attribute_list = YourSelfDao.get_all_attributes()

        history_str = ""
        for item in history:
            if item["role"] == "USER":
                history_str += "Q: " + item["content"]
            elif item["role"] == "BOT":
                history_str += "A: " + item["content"]

        prompt = YOURSELF_ATTRIBUTE_SELECTION.format(
            attribute_list=attribute_list,
            history=history_str,
            question=question
        )

        output = Factory.llm.complete(prompt)
        output = output.text.strip().split("```")[0]
        # output = json.loads(output)
        output = yaml.safe_load(output)
        print(output)

        refined_question = output["refined_question"]
        rel_attr = output["attribute_list"]
        rel_data = YourSelfDao.get_by_attributes(rel_attr)
        print("REL", rel_data)
        context = ""
        for item in rel_data:
            context += item["content"] + '\n'

        print("Refined Question:", refined_question)
        print("Context", context)



