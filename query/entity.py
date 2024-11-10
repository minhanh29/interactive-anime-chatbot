from database import EntityDao, PeopleDao, YourSelfDao
from prompts.planning import PLANNING_GENERATION
from llm.factory import Factory
from config import settings
from schemas import PlanningGenerationOutput


class EntityEngine:
    def find_entity_by_name(self, name):
        fuzzy_names = EntityDao.get_by_fuzzy_name(name)
        metaphone_names = EntityDao.get_by_metaphone_name(name)
        all_names = fuzzy_names + metaphone_names
        result = []
        visited = set()
        for item in all_names:
            if item["id"] in visited:
                continue
            visited.add(item["id"])
            result.append(item)

        return result

    def add_to_dict(self, dict_obj, key, data: list):
        if key in dict_obj:
            dict_obj[key].extend(data)
        else:
            dict_obj[key] = data

    def query(self, bot_name, prev_context, history, speaker, question, attribute_list, verbose=0):
        prompt = PLANNING_GENERATION.format(
            bot_name=bot_name,
            relationship_list="\n".join(attribute_list),
            context=prev_context,
            history=history,
            speaker=speaker,
            question=question
        )

        if verbose >= 2:
            print(prompt)
        pydantic_output: PlanningGenerationOutput = Factory.invoke_llm(
            prompt=prompt,
            response_model=PlanningGenerationOutput
        )
        if verbose >= 2:
            print(pydantic_output)

        refined_question = pydantic_output.refined_question
        entity_objects = pydantic_output.entities

        context = []
        visited_entities = set()
        proccessed = {}
        for item in entity_objects:
            if item.relation not in attribute_list:
                proccessed[item.id] = []
                continue

            if item.related_person_id == -1 or item.related_person == "none" or item.relation == "none":
                if item.name == "myself" or "Serena" in item.name:  # summary already in the default prompt
                    self.add_to_dict(proccessed, item.id, [{
                        "id": 0,
                        "category": "myself"
                    }])
                    continue
                else:
                    entities = self.find_entity_by_name(item.name)
                    if verbose >= 2:
                        print("Matched Entity for", item.name, entities)
                    for entity in entities:
                        if entity["id"] in visited_entities:
                            continue

                        context.append(entity["description"])
                        visited_entities.add(entity["id"])
                    self.add_to_dict(proccessed, item.id, [{
                        "id": x["id"],
                        "category": x["category"]
                    } for x in entities])

                if item.relation != "none": # summary:
                    if item.name == "myself" or "Serena" in item.name:
                        result = YourSelfDao.get_by_attribute(
                            item.relation
                        )
                        for row in result:
                            context.append(row["content"])
                        self.add_to_dict(proccessed, item.id, [{
                            "id": 0,
                            "category": "myself"
                        }])
                    else:
                        entities = self.find_entity_by_name(item.name)
                        if verbose >= 2:
                            print("Matched Entity for", item.name, entities)

                        temp = []
                        ids = []
                        for entity in entities:
                            if entity["id"] in visited_entities:
                                continue

                            temp.append(entity["description"])
                            result = PeopleDao.get_by_entity_id_and_attribute(
                                int(entity["id"]),
                                item.relation
                            )

                            for row in result:
                                temp.append(row["content"])
                                if row["ref"]:
                                    target_id = int(row["value"])
                                    if target_id not in visited_entities:
                                        ids.append({
                                            "id": target_id,
                                            "category": "people" if target_id != settings.BOT_ENTITY_ID else "myself"
                                        })
                                        visited_entities.add(target_id)
                        context.extend(temp)
                        self.add_to_dict(proccessed, item.id, ids)


        if verbose >= 2:
            print("Proccessed", proccessed)

        while True and len(proccessed) > 0:
            if len(proccessed) == len(entity_objects):
                break

            for item in entity_objects:
                if item.id in proccessed:
                    continue
                if item.related_person_id not in proccessed:
                    continue

                temp = []
                ids = []
                for entity_info in proccessed[item.related_person_id]:
                    if entity_info["category"] == "myself":
                        result = YourSelfDao.get_by_attribute(
                            item.relation
                        )
                    elif entity_info["category"] == "people":
                        result = PeopleDao.get_by_entity_id_and_attribute(
                            int(entity_info["id"]),
                            item.relation
                        )

                    for row in result:
                        temp.append(row["content"])
                        if row["ref"]:
                            target_id = int(row["value"])
                            if target_id not in visited_entities:
                                ids.append({
                                    "id": target_id,
                                    "category": "people" if target_id != settings.BOT_ENTITY_ID else "myself"
                                })
                                visited_entities.add(target_id)

                                # add entity info
                                if target_id != settings.BOT_ENTITY_ID:
                                    temp.append(EntityDao.get_by_id(target_id)["description"])
                context.extend(temp)
                proccessed[item.id] = ids

        if verbose >= 1:
            print("-------- Entity context --------")
            print(context)

        context = list(set(context))
        return refined_question, context, pydantic_output.need_attribute_dimension
