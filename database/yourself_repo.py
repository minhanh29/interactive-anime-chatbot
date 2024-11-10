from .database_connection import DBRepository
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.expression import column


class YourSelfRepo(DBRepository):
    def __init__(self):
        super().__init__()
        self.table_name = "yourself"

    def add(self, attribute: str, value: str, content: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            INSERT INTO {self.table_name} (attribute, value, content)
                            VALUES (:attribute, :value, :content)
                            RETURNING id;
                '''), ({
                    "attribute": attribute,
                    "value": value,
                    "content": content,
                }))
                first_row = result.first()
                if first_row is not None:
                    return first_row[0]
        return None

    def get_by_attribute_and_value(self, attribute: str, value: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE attribute = :attribute
                            AND value = :value;
                '''), ({
                    "attribute": attribute,
                    "value": value,
                }))
                result = result.fetchall()
                parsed_result = []
                for item in result:
                    parsed_result.append({
                        "id": item[0],
                        "attribute": item[1],
                        "value": item[2],
                        "content": item[3],
                        "ref": item[4],
                    })
                return parsed_result
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
                parsed_result = []
                for item in result:
                    parsed_result.append({
                        "id": item[0],
                        "attribute": item[1],
                        "value": item[2],
                        "content": item[3],
                        "ref": item[4],
                    })
                return parsed_result
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
                parsed_result = []
                for item in result:
                    parsed_result.append({
                        "id": item[0],
                        "attribute": item[1],
                        "value": item[2],
                        "content": item[3],
                        "ref": item[4],
                    })
                return parsed_result
        return []

    def get_by_attribute(self, attribute: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE attribute = :attribute;
                '''), ({
                    "attribute": attribute,
                }))
                result = result.fetchall()
                parsed_result = []
                for item in result:
                    parsed_result.append({
                        "id": item[0],
                        "attribute": item[1],
                        "value": item[2],
                        "content": item[3],
                        "ref": item[4],
                    })
                return parsed_result
        return []

    def get_by_attributes(self, attributes: list):
        list_str = ", ".join([f"'{x}'" for x in attributes])
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE attribute IN ({list_str});
                '''))
                result = result.fetchall()
                parsed_result = []
                for item in result:
                    parsed_result.append({
                        "id": item[0],
                        "attribute": item[1],
                        "value": item[2],
                        "content": item[3],
                        "ref": item[4],
                    })
                return parsed_result
        return []

    def get_all(self):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name};
                '''))
                result = result.fetchall()
                parsed_result = []
                for item in result:
                    parsed_result.append({
                        "id": item[0],
                        "attribute": item[1],
                        "value": item[2],
                        "content": item[3],
                        "ref": item[4],
                    })
                return parsed_result
        return []

    def get_all_attributes(self):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT attribute
                            FROM {self.table_name};
                '''))
                result = result.fetchall()
                return [x[0] for x in result]
        return []


YourSelfDao: YourSelfRepo = YourSelfRepo()
