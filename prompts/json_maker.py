JSON_DATA_MAKER = """Human: You are an information extraction tool. Create a json object containing all neccessary information from the given Information.

Below is a list of currently available attributes. You can create new ones if needed.
{attribute_list}

Below is a list of entities and their ID for reference.
{entity_list}

Below is an example output format
### Entity
Isaac

### Information
Isaac Nguyen is a boy. He was born in 29th November 2001. His girlfriend is Paola Tran and his mother is Thao.
He just met his friend today. He feel good about it.

### Observation
I need to update information about the entity named Isaac Nguyen. The neccessary information I can gather from the provided information is his name, gender, birthday, girlfriend and mother. The latter facts about meeting friend is just a temporary event in his life and the information is very generic, so there is nothing to update about it.

### Output
```
[
    {{
        "attribute": "first_name",
        "value": "Isaac",
        "content": "this_person's first name is Isaac",
        "ref": false
    }},
    {{
        "attribute": "last_name",
        "value": "Nguyen",
        "content": "this_person's last name is Nguyen",
        "ref": false
    }},
    {{
        "attribute": "gender",
        "value": "male",
        "content": "this_person's gender is male",
        "ref": false
    }},
    {{
        "attribute": "day_of_birth",
        "value": "29",
        "content": "this_person's day of birth is 29",
        "ref": false
    }},
    {{
        "attribute": "month_of_birth",
        "value": "10",
        "content": "this_person's month of birth is 10",
        "ref": false
    }},
    {{
        "attribute": "year_of_birth",
        "value": "2001",
        "content": "this_person's year of birth is 2001",
        "ref": false
    }},
    {{
        "attribute": "lover",
        "value": "1",
        "content": "this_person's girlfriend is ref_person",
        "ref": true
    }}
]
```
Done.

Begin now! Strictly follow the above output format!
Remember the content is just a verbose version of the attribute and value. Use "this_person" to indicate the target entity. Never use the entity name in the content. For example, in case the entity is Isaac, if attribute is gender and value is male, then the corresponding content must be "this_person's gender is male"
For relationship attributes refering to another entity like lover, mother, father, etc. the value is the ID of that person. If there are no IDs use "none" for the value. Use "ref_person" in the content to refer to the referenced person.
Only select crucial and clear information. You CAN create new attributes if needed.
You MUST enclose the output between the ```

### Entity
{entity}

### Information
{information}

Assistant:
### Observation"""
