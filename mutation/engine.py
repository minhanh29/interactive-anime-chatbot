from typing import List
from database import AttributeDao, EntityDao, PeopleDao, YourSelfDao
from prompts.json_maker import JSON_DATA_MAKER
from prompts.entity import ENTITY_DESCRIPTION
from prompts.mutation import INFORMATION_SELECTION
from llm.factory import Factory
from config import settings
from schemas import PeopleRow
from utils.json_parser import parse_json


class MutationEngine:
    def select_info(self, dialog, old_knowledge, verbose=0):
        entity_list = EntityDao.get_all()
        entity_list_str = ""
        for item in entity_list:
            entity_list_str += f'ID: {item["id"]} - Name: {item["name"]}\n'

        # determine which need to be added
        prompt = INFORMATION_SELECTION.format(
            entities=entity_list_str,
            old_knowledge=old_knowledge,
            dialog=dialog
        )

        if verbose >= 2:
            print(prompt)

        output = Factory.llm.complete(prompt)
        new_info = output.text.strip()
        if verbose >= 2:
            print(new_info)
        new_info = parse_json(new_info, marker="[]")

        if verbose >= 1:
            print("Selected Information")
            print(new_info)

        return new_info

    def create(self, new_info, verbose=0):
        attribute_list = AttributeDao.get_by_category("people")

        entity_list = EntityDao.get_all()
        entity_list_str = ""
        for item in entity_list:
            entity_list_str += f'ID: {item["id"]} - Name: {item["name"]}\n'

        # create new entities
        entity_list_str, new_info = self.create_new_entities(
            entity_list_str=entity_list_str,
            new_info=new_info,
            verbose=verbose
        )

        attribute_set = set(attribute_list)
        for new_entity in new_info:
            # convert to json format
            attribute_list_str = ", ".join(list(attribute_set))
            prompt = JSON_DATA_MAKER.format(
                attribute_list=attribute_list_str,
                entity_list=entity_list_str,
                entity=new_entity["name"],
                information=".\n".join(new_entity["content"])
            )
            output = Factory.llm.complete(prompt)
            if verbose >= 2:
                print(prompt)

            if verbose >= 1:
                print("Json Data")
                print(new_info)

            output = output.text.strip()
            entity_info = parse_json(output, marker="[]")
            print(entity_info)
            if entity_info is None:
                continue

            entity_info = [PeopleRow(**item) for item in entity_info]

            self.update_attributes(entity_info, attribute_set, verbose)
            self.update_people_value(new_entity, entity_info, attribute_set, verbose)

    def create_new_entities(self, entity_list_str, new_info, verbose=0):
        for new_entity in new_info:
            new_entity_name = new_entity["name"]
            result = EntityDao.get_by_name(new_entity_name)
            if result is None:
                # create description for this entity
                prompt = ENTITY_DESCRIPTION.format(
                    information=".\n".join(new_entity["content"])
                )
                output = Factory.llm.complete(prompt)
                if verbose >= 2:
                    print(prompt)
                    print(output)
                description = output.text.strip()
                entity_id = EntityDao.add(
                    name=new_entity_name,
                    description=description,
                    category="people"
                )
                entity_list_str += f'ID: {entity_id} - Name: {new_entity_name}\n'
                new_entity["id"] = entity_id
                if verbose >= 1:
                    print("Added entity", new_entity_name)
            # else:
            #     # do not update the AI description
            #     if result["id"] == settings.BOT_ENTITY_ID:
            #         continue
            #     new_entity["id"] = result["id"]
            #     prompt = ENTITY_DESCRIPTION.format(
            #         information=result["description"].strip() + "\n" + ".\n".join(new_entity["content"]).strip()
            #     )
            #     output = Factory.llm.complete(prompt)
            #     if verbose >= 2:
            #         print(prompt)
            #         print(output)
            #     description = output.text.strip()
            #     EntityDao.update(
            #         id=result["id"],
            #         description=description
            #     )
            #     if verbose >= 1:
            #         print("Update entity description", result["name"])
        return entity_list_str, new_info

    def update_attributes(self, entity_info: List[PeopleRow], attribute_set, verbose=0):
        if verbose >= 1:
            print("Update attribute table")
        cnt = 0
        for item in entity_info:
            if item.attribute not in attribute_set:
                AttributeDao.add(name=item.attribute, ref=item.ref, category="people")
                attribute_set.add(item.attribute)
                if verbose >= 1:
                    print("Added attribute", item.attribute)
                cnt += 1
        if verbose >= 1:
            print(f"Added {cnt} new attributes")

    def update_people_value(self, new_entity, entity_info: List[PeopleRow], attribute_set, verbose=0):
        if verbose >= 1:
            print("Update People table")
        cnt = 0
        for item in entity_info:
            result = PeopleDao.get_by_entity_id_attribute_value(new_entity["id"], item.attribute, item.value)
            if len(result) > 0:
                # no need to add
                continue

            print("Updating", new_entity["name"])
            # check if this attribute is plural - allow multiple values
            attr_result = AttributeDao.get_by_name(item.attribute)
            if len(attr_result) > 0:
                attr_result = attr_result[0]
            else:
                if verbose >= 1:
                    print("Error. Cannot find attribute", item.attribute)
                continue

            people_result = PeopleDao.get_by_entity_id_and_attribute(new_entity["id"], item.attribute)
            if len(people_result) > 0 and not attr_result["plural"]:
                if verbose >= 1:
                    print("Updating", item.dict())
                PeopleDao.update(
                    id=people_result[0]["id"],
                    value=item.value,
                    content=item.content
                )
            else:
                if verbose >= 1:
                    print("Adding", item.dict())
                PeopleDao.add(entity_id=new_entity["id"], **item.dict())
            cnt += 1
        if verbose >= 1:
            print(f"Added {cnt} new piece of information")
