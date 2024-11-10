import json
from tqdm import tqdm
from database import YourSelfDao, EntityDao, PeopleDao, AttributeDao
from llm.factory import Factory
from prompts.entity import ENTITY_DESCRIPTION, ENTITY_RELATIONSHIP
from prompts.json_maker import JSON_DATA_MAKER


def add_yourself_data(dao, json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    print(f"Start inserting data from {json_path} to {dao.table_name}.")
    for item in tqdm(data["data"]):
        YourSelfDao.add(**item)

    print("Done.")


def add_people_data(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)["data"]

    entity_name = []
    name_attr_list = ["last_name", "middle_name", "first_name"]
    name_str_dict = {}
    for item in data:
        if item["attribute"] in name_attr_list:
            name_str_dict[item["attribute"]] = item["value"]
    for key in name_attr_list:
        if key in name_str_dict:
            entity_name.append(name_str_dict[key].strip())
    entity_name = " ".join(entity_name)
    print("Person name:", entity_name)

    print("Create description for the entity")
    information = ""
    for item in data:
        if item["ref"]:
            information += f'- {item["attribute"]}: {item["content"]}\n'
        else:
            information += f'- {item["attribute"]}: {item["value"]}\n'
    prompt = ENTITY_DESCRIPTION.format(
        information=information
    )
    print(prompt)
    output = Factory.llm.complete(prompt)
    description = output.text.strip().split("```")[0]
    print(description)

    print("Create new entity")
    entity_id = EntityDao.add(entity_name, description, category="people")
    print("Entity ID:", entity_id)

    print(f"Start inserting data from {json_path} to {PeopleDao.table_name}.")
    for item in tqdm(data):
        PeopleDao.add(entity_id=entity_id, **item)

    print("Done.")


def data_extraction(txt_path, output_path):
    with open(txt_path, "r") as f:
        data = f.read()

    attribute_list = AttributeDao.get_by_category("people")
    attribute_list_str = ", ".join(attribute_list)

    entity_list = EntityDao.get_all()
    entity_list_str = ""
    for item in entity_list:
        entity_list_str += f'ID: {item["id"]} - Name: {item["name"]}\n'

    prompt = JSON_DATA_MAKER.format(
        attribute_list=attribute_list_str,
        entity_list=entity_list_str,
        information=data
    )
    print(prompt)
    output = Factory.llm.complete(prompt)
    json_data = output.text.strip().split("```")[0]
    json_data = json.loads(json_data)

    print("Update attribute table")
    cnt = 0
    attribute_set = set(attribute_list)
    for item in json_data:
        if item["attribute"] not in attribute_set:
            AttributeDao.add(name=item["attribute"], ref=item["ref"], category="people")
            attribute_set.add(item["attribute"])
            cnt += 1
    print(f"Added {cnt} new attributes")

    print(output.text)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "data": json_data
        }, f, ensure_ascii=False)


def refine_relationships(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)["data"]

    entity_name = []
    name_attr_list = ["last_name", "middle_name", "first_name"]
    name_str_dict = {}
    for item in data:
        if item["attribute"] in name_attr_list:
            name_str_dict[item["attribute"]] = item["value"]
    for key in name_attr_list:
        if key in name_str_dict:
            entity_name.append(name_str_dict[key].strip())
    entity_name = " ".join(entity_name)
    print("Person name:", entity_name)

    attribute_list = AttributeDao.get_by_ref("people", ref=True)
    attribute_list_str = ", ".join(attribute_list)

    entity_list = EntityDao.get_by_category("people")
    entity_list_str = ""
    entity_dict = {}
    for item in entity_list:
        entity_list_str += f'ID: {item["id"]} - Name: {item["name"]}\n'
        entity_dict[item["id"]] = item["name"]

    attribute_set = set(attribute_list)
    for item in data:
        if item["attribute"] not in attribute_set:
            continue

        target_entity = entity_dict[int(item["value"])]

        prompt = ENTITY_RELATIONSHIP.format(
            attribute_list=attribute_list_str,
            entity_list=entity_list_str,
            entity=target_entity,
            information=item["content"]
        )

        print(prompt)
        output = Factory.llm.complete(prompt)
        json_data = output.text.strip().split("```")[0]
        json_data = json.loads(json_data)
        print(output.text)
        for i in json_data:
            PeopleDao.add(entity_id=item["value"], **i)
        print(f"Added {len(json_data)} new relationships for {target_entity}")



def init_attributes():
    data = PeopleDao.get_all()
    attribute_set = set()
    result = []
    for item in data:
        if item["attribute"] in attribute_set:
            continue
        attribute_set.add(item["attribute"])
        result.append([item["attribute"], item["ref"]])

    for item in result:
        AttributeDao.add(name=item[0], ref=item[1], category="people")

if __name__ == "__main__":
    # add_yourself_data(YourSelfDao, "./data/raw_data/yourself.json")
    # data_extraction("./legacy/data/girlfriend.txt", "./data/raw_data/tonhi.json")
    # add_people_data("./data/raw_data/tonhi.json")
    # init_attributes()
    refine_relationships("./data/raw_data/tonhi.json")
