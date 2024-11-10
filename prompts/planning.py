PLANNING_GENERATION = """Human: You are an entity and relationships extraction tool. Identify all entities and relationships related to the given question.
If the question related to you, use "myself" as an entity.
Your name is {bot_name}. If the question mention {bot_name}, it means you, hence using "myself".

## Relationship List
{relationship_list}

Format for each entity is as follow
{{
    "thinking": Your internal thinking about what to do,
    "refined_question": Refined version of the question to make it clearer,
    "need_attribute_dimension": Boolean indicator whether need to perform query on attribute dimension. For example, if the human ask you to find who have the same age as him, so you need to perform query on the attribute dimension "age".
    "topics": list of keywords or sentences that are relevant to the conversation,
    "entities": [{{
        "id": id of the entity, you can make it up as long as it is unique,
        "name": name of the entity,
        "relation": relationship between the related_person and this entity,
        "related_person": name of the related person,
        "related_person_id": id of the realted person,
    }}]
}}

Below is an example

## Dialog History
Q: What is your birthday?
A: It is the 29th of October 2005

### Question
Q: How about your creator's girlfiend?

### Output
The relevant entities to answer the given question are:
```
{{
    "thinking": "My ceater is asking about his girlfiend birthday. This only needs to search for entity information about myself, my creator, and his girlfiend, no need for attribute dimension, query.",
    "refined_question": "What is your creator's girlfiend birthday?",
    "need_attribute_dimension": false,
    "topics": ["Birthday", "Month of birth", "Year of Birth", "Lover", "Issac's girlfriend", "Issac's girlfriend's birthday"],
    "entities": [
        {{
            "id": 0,
            "name": "myself",
            "relation": "none",
            "related_person": "none",
            "related_person_id": -1
        }},
        {{
            "id": 1,
            "name": "my creator",
            "relation": "creator",
            "related_person": "me",
            "related_person_id": 0
        }},
        {{
            "id": 2,
            "name": "girlfriend of my creator",
            "relation": "lover",
            "related_person": "my creator",
            "related_person_id": 1
        }},
        {{
            "id": 3,
            "name": "Day of birth",
            "relation": "day_of_birth",
            "related_person": "girlfriend of my creator",
            "related_person_id": 2
        }},
        {{
            "id": 4,
            "name": "Month of birth",
            "relation": "month_of_birth",
            "related_person": "girlfriend of my creator",
            "related_person_id": 2
        }}
    ]
}}
```
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
The relevant entities to answer the given question are:
```
{{"""

