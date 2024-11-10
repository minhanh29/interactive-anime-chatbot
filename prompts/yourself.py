YOURSELF_ATTRIBUTE_SELECTION = """Human: You are a attribute selection tool. Select relevant information that may help to answer the given question. When the question mentions "you", it is refers to a girl.

### Attribute List
{attribute_list}

Below is an example
## Dialog History
Q: What is your girlfriend's birthday?
A: It is the 29th of October

### Question
How about yours?

### Output
The relevant attributes to answer the given question are:
```
{{
    "refined_question": "What is your birthday?",
    "attribute_list": ["date_of_birth", "month_of_birth", "year_of_birth"]
}}
```
Done.

Begin now! Strictly follow the above output format!

## Dialog History
{history}

### Question
Isaac (your creator): {question}

Assistant:
### Output
The relevant attributes to answer the given question are:
```"""
