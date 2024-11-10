from .database_connection import DBRepository
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.expression import column
from cache import my_cache


class EntityRepo(DBRepository):
    def __init__(self):
        super().__init__()
        self.table_name = "entity"

        entities = self.get_all()
        for entity in entities:
            my_cache.entity_dict[entity["id"]] = entity["name"]

    def parse_list(self, result):
        parsed_result = []
        for item in result:
            parsed_result.append({
                "id": item[0],
                "name": item[1],
                "description": item[2],
                "category": item[3],
            })
        return parsed_result

    def parse_one(self, first_row):
        if first_row is not None:
            return {
                "id": first_row[0],
                "name": first_row[1],
                "description": first_row[2],
                "category": first_row[3],
            }
        return None

    def add(self, name: str, description: str, category: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            INSERT INTO {self.table_name} (name, description, category)
                            VALUES (:name, :description, :category)
                            RETURNING id;
                '''), ({
                    "name": name,
                    "description": description,
                    "category": category,
                }))
                first_row = result.first()
                if first_row is not None:
                    my_cache.entity_dict[first_row[0]] = name
                    return first_row[0]
        return None

    def get_by_fuzzy_name(self, name):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE :name % ANY(STRING_TO_ARRAY(name,' '))
                            LIMIT 3;
                '''), ({
                    "name": name,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return None

    def get_by_metaphone_name(self, name):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE SIMILARITY(METAPHONE(name, 10), METAPHONE(:name, 10)) > 0.2
                            LIMIT 3;
                '''), ({
                    "name": name,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return None

    def get_by_name(self, name: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE name = :name;
                '''), ({
                    "name": name,
                }))
                first_row = result.first()
                return self.parse_one(first_row)
        return None

    def get_by_id(self, id: int):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE id = :id;
                '''), ({
                    "id": id,
                }))
                first_row = result.first()
                return self.parse_one(first_row)
        return None

    def get_by_category(self, category: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT *
                            FROM {self.table_name}
                            WHERE category = :category;
                '''), ({
                    "category": category,
                }))
                result = result.fetchall()
                return self.parse_list(result)
        return None

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

    def update(self, id: int, name: str = None, description: str = None, category: str = None):
        raw_data = {
            "name": name,
            "description": description,
            "category": category,
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
                    if name is not None:
                        my_cache.entity_dict[first_row[0]] = name
                    return first_row[0]
        return None


EntityDao: EntityRepo = EntityRepo()

