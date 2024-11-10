from .database_connection import DBRepository
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.expression import column


class AttributeRepo(DBRepository):
    def __init__(self):
        super().__init__()
        self.table_name = "attributes"

    def parse_list(self, result):
        parsed_result = []
        for item in result:
            parsed_result.append({
                "id": item[0],
                "name": item[1],
                "ref": item[2],
                "category": item[3],
                "plural": item[4],
            })
        return parsed_result

    def add(self, name: int, ref: bool, category: str):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            INSERT INTO {self.table_name} (name, ref, category)
                            VALUES (:name, :ref, :category)
                            RETURNING id;
                '''), ({
                    "name": name,
                    "ref": ref,
                    "category": category,
                }))
                first_row = result.first()
                if first_row is not None:
                    return first_row[0]
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
                result = result.fetchall()
                return self.parse_list(result)
        return []

    def get_by_category(self, category):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT name
                            FROM {self.table_name}
                            WHERE category = :category;
                '''), ({
                    "category": category,
                }))
                result = result.fetchall()
                return [x[0] for x in result]
        return []

    def get_by_ref(self, category, ref=True):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT name
                            FROM {self.table_name}
                            WHERE ref = :ref AND category = :category;
                '''), ({
                    "category": category,
                    "ref": ref,
                }))
                result = result.fetchall()
                return [x[0] for x in result]
        return []

    def get_attribute_list(self):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(f'''
                            SELECT name
                            FROM {self.table_name};
                '''))
                result = result.fetchall()
                return [x[0] for x in result]
        return []


AttributeDao: AttributeRepo = AttributeRepo()


