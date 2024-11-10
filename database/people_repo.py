from .database_connection import DBRepository
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.expression import column
from cache import my_cache


class PeopleRepo(DBRepository):
    def __init__(self):
        super().__init__()
        self.table_name = "people"

    def parse_list(self, result):
        parsed_result = []
        for item in result:
            parsed_item = {
                "id": item[0],
                "entity_id": item[1],
                "attribute": item[2],
                "value": item[3],
                "content": item[4],
                "ref": item[5],
            }
            parsed_item["content"] = parsed_item["content"].replace("this_person", my_cache.entity_dict[parsed_item["entity_id"]])
            if parsed_item["ref"]:
                parsed_item["content"] = parsed_item["content"].replace("ref_person", my_cache.entity_dict[int(parsed_item["value"])])
            parsed_result.append(parsed_item)
        return parsed_result


    def add(self, entity_id: int, attribute: str, value: str, content: str, ref: bool):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            INSERT INTO {self.table_name} (entity_id, attribute, value, content, ref)
                            VALUES (:entity_id, :attribute, :value, :content, :ref)
                            RETURNING id;
                '''), ({
                    "entity_id": entity_id,
                    "attribute": attribute,
                    "value": value,
                    "content": content,
                    "ref": ref,
                }))
                first_row = result.first()
                if first_row is not None:
                    return first_row[0]
        return None

    def get_by_entity_id_and_attribute(self, entity_id: int, attribute: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE entity_id = :entity_id
                            AND attribute = :attribute;
                '''), ({
                    "entity_id": entity_id,
                    "attribute": attribute,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_by_entity_id_attribute_value(self, entity_id: int, attribute: str, value: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE entity_id = :entity_id
                            AND attribute = :attribute
                            AND value = :value;
                '''), ({
                    "entity_id": entity_id,
                    "attribute": attribute,
                    "value": value,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_by_attribute_and_value(self, attribute: str, value: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE attribute = :attribute
                            AND value = :value
                            LIMIT 5;
                '''), ({
                    "attribute": attribute,
                    "value": value,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_by_attribute_and_value_fuzzy(self, attribute: str, value: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE attribute = :attribute
                            AND :value % ANY(STRING_TO_ARRAY(value,' '))
                            LIMIT 5;
                '''), ({
                    "attribute": attribute,
                    "value": value,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_by_attribute_and_value_metaphone(self, attribute: str, value: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE attribute = :attribute
                            AND SIMILARITY(METAPHONE(value, 10), METAPHONE(:value, 10)) > 0.1
                            LIMIT 5;
                '''), ({
                    "attribute": attribute,
                    "value": value,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_by_attribute(self, attribute: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE attribute = :attribute
                            LIMIT 5;
                '''), ({
                    "attribute": attribute,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_by_attributes(self, attributes: list):
        list_str = ", ".join([f"'{x}'" for x in attributes])
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE attribute IN ({list_str})
                            LIMIT 10;
                '''))
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_all(self):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name};
                '''))
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_all_attributes(self):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT DISTINCT attribute
                            FROM {self.table_name};
                '''))
                result = result.fetchall()
                return [x[0] for x in result]
        return []

    def update(self, id: int, entity_id: int = None, attribute: str = None, value: str = None, content: str = None, ref: bool = None):
        raw_data = {
            "entity_id": entity_id,
            "attribute": attribute,
            "value": value,
            "content": content,
            "ref": ref,
        }
        data = {}
        sql_str = []
        for key, item in raw_data.items():
            if item is not None:
                data[key] = item
                sql_str.append(f"{key} = :{key}")

        if len(sql_str) == 0:
            print("Nothing to update")
            return id

        sql_str = ", ".join(sql_str)

        data["id"] = id
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            UPDATE {self.table_name}
                            SET {sql_str}
                            WHERE id = :id
                            RETURNING id;
                '''), (data))
                first_row = result.first()
                if first_row is not None:
                    return first_row[0]
        return None


PeopleDao: PeopleRepo = PeopleRepo()
