ENTITY_DESCRIPTION = """Human: You are an information summarization tool. Write a short description for the given entity's information.

Below is an example
## Information
- first_name: Mia
- last_name: Nguyen
- gender: female
- date_of_birth: 29th October, 2005
- place_of_birth: Vietnam
- nationality: Vietnamese
- creator: Nguyễn Minh Anh - Mia is a robot created by an AI Engineer named Nguyễn Minh Anh
- character: smart, nice, and empathy

### Output
Mia Nguyen is smart, nice and empathy. She is a Vietnamese female robot created by an AI Engineer named Isaac Nguyen

Begin now! Strictly follow the above output format!
Only include information about the entity's character, gender, birthday, study, occupation, hobby, and some important relationships.

## Information
{information}

Assistant:
### Output
"""


ENTITY_RELATIONSHIP = """Human: You are an information extraction tool. Create a json object containing all neccessary relationship information from the given Information.

Below is a list of currently available attributes. You can create new ones if needed.
{attribute_list}

Below is a list of entities and their ID for reference.
{entity_list}

Below is an example output format
## Current Entity
Isaac Nguyen

## Output
New relationships for Nguyễn Minh Anh are
```
[
    {{
        "attribute": "brother",
        "value": "1",
        "content": "Isaac Nguyen's brother is Phan Trung Tín",
        "ref": true
    }},
    {{
        "attribute": "project",
        "value": "3",
        "content": "Isaac Nguyen has a project named YouHand",
        "ref": true
    }},
]
```
Done.

Begin now! Strictly follow the above output format!
You MUST enclose the output between the ```

## Target Entity
{entity}

## Information
{information}

Assistant:
### Output
New relationships for {entity} are
```
"""
