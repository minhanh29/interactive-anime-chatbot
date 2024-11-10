RELATION_GENERATION = """Human: You are an relation extraction tool. Identify all relations related to the given question.

## Relationship List
{relationship_list}

## Database List
{database_list}

Format for each entity is as follow
{{
    "relation": relationship between the related_person and this entity,
    "value": value for realtion to query, if not applicable return "none"
    "related_database": database used to search for the relation (myself, people, animal, ...)
}}

Below is an example

## Dialog History
Q: What is your birthday?
A: It is the 29th of October 2023

### Question
Q: Who else has the same birthday as yours?

### Output
The relevant relations to answer the given question are:
```
{{
    "refined_question": "Find all people who were born in 29th October",
    "relations": [
        {{
            "relation": "day_of_birth",
            "value": "29",
            "related_database": ["myself", "people"]
        }},
        {{
            "relation": "month_of_birth",
            "value": "10",
            "related_database": ["myself", "people"]
        }},
        {{
            "relation": "month_of_birth",
            "value": "October",
            "related_database": ["myself", "people"]
        }}
    ]
}}
```
Not sure if month_of_birth is number or text, so give both.
Done.

####
Begin now! Strictly follow the above output format!
Only use relations from the Relationship List. If nothing mathes, pick the ones that most relevant.
Make sure that your output JSON is readable by python json.loads()

## Context
{context}

## Dialog History
{history}

### Question
{speaker}: {question}

Assistant:
### Output
The relevant relations to answer the given question are:
```
{{"""


