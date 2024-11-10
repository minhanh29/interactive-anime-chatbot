from database import AttributeDao, PeopleDao, YourSelfDao
from prompts.relation import RELATION_GENERATION
from llm.factory import Factory
from schemas import RelationItem, RelationGenerationOutput


# TODO: handle ref relation
class RelationExtractionEngine:
    def __init__(self):
        self.database_list = ["myself", "people"]

    def find_attribute_and_value(self, dao, attribute, value):
        fuzzy_items = dao.get_by_attribute_and_value_fuzzy(attribute, value)
        metaphone_items = dao.get_by_attribute_and_value_metaphone(
            attribute, value
        )

        all_items = fuzzy_items + metaphone_items
        result = []
        visited = set()
        for item in all_items:
            if item["id"] in visited:
                continue
            visited.add(item["id"])
            result.append(item)

        return result

    def query(self, current_context, history, speaker, question, attribute_list, verbose=0):
        prompt = RELATION_GENERATION.format(
            relationship_list="\n".join(attribute_list),
            database_list="\n".join(self.database_list),
            context=current_context,
            history=history,
            speaker=speaker,
            question=question
        )

        if verbose >= 2:
            print(prompt)
        pydantic_output: RelationGenerationOutput = Factory.invoke_llm(
            prompt=prompt,
            response_model=RelationGenerationOutput
        )
        if verbose >= 2:
            print(pydantic_output)
        # output = "{" + output.text.strip()
        # output = parse_json(output)["relations"]
        output = pydantic_output.relations

        context = []
        attribute_set = set(attribute_list)
        for item in output:
            if item.relation not in attribute_set:
                continue

            if item.relation == "none" or item.value == "none":
                continue

            relation = item.relation
            related_database = item.related_database
            if type(related_database) != list:
                related_database = [related_database]

            for entity in related_database:
                result = []
                if entity == "myself":
                    result = self.find_attribute_and_value(YourSelfDao, relation, item.value)
                elif entity == "people":
                    result = self.find_attribute_and_value(PeopleDao, relation, item.value)

                for row in result:
                    context.append(row["content"])

        if verbose >= 1:
            print("-------- Relation context --------")
            print("\n".join(context))
        return context

