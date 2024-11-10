INFORMATION_SELECTION = """Human: You are engaging a conversation. You need to determine which new information needed to add to your knowledge base. Base on the Old Knowledge and Dialog, select the necessary information from the Dialog that are not included in the Old Knowledge. Return empty list if there is no new information.

Below are some examples.
# Example 1
### Dialog
Paola Tran: I am Paola Tran. I am your creator's girlfriend.
You: That's great. Nice to meet you.
Paola Tran: I loves pink and blue.

### Old Knowledge
Isaac is your creator.

### Observation
The speaker is Paola talking to me. I already know about my creator Isaac but I did not know that he has a girlfriend and she loves pink and blue. I should update that information.

### New Information
```
[
    {{
        "name": "Paola Tran",
        "content": [
            "Paola Tran is Isaac's girlfriend",
            "Paola Tran loves pink and blue"
        ]
    }},
    {{
        "name": "Isaac Nguyen",
        "content": [
            "Isaac Nguyen's girlfriend is Paola Tran"
        ]
    }}
]
```

# Example 1
### Current Information
Paola Tran: I am your creator's girlfriend.
You: I see. You are the girl that Isaac mentioned to me. The weather is nice today.

### Old Knowledge
Isaac's girlfriend is Paola Tran. Her birthday is November 29th 2001.

### Observation
The speaker is Paola talking to me. I already know about her birthday and the fact that she is Isaac's girlfriend. Nothing to update.

### New Information
```
[]
```

Now Begin! Some background information is provided to help you understand about the revelant entities.
You are also provided with the current entities' names for your reference.
Remember to include mutual relationships for both entity. For example, if you include "Paola is Isaac's girlfriend" in the Paola entity, then also include "Isaac is Paola's boyfriend." in the Isaac entity.

### Current Entities
{entities}

### Dialog
{dialog}

### Old Knowledge
{old_knowledge}

### Note:
You MUST enclose the new information json between the ``` quotes.
Only select information from the user. Do not select information that you made up from your turn in the dialog.

Assistant:
### Observation
"""


CONTEXT_SUMMARY = """Human: You are engaging a conversation. You need to summarize a conversation based on the Context and Dialog. Your summary will help you know what was going on in the past conversation so that you can answer the user's question properly in the next turn.

### Context
{context}

### Dialog
{dialog}

Now begin! Summarize the context and the dialog into 1 small paragraph.
Make it as brief as possible. The paragraph should be less than 50 words.

Assistant:
Below is the summary that satisfies all the requirements:
"""


MEMORY_EVENT = """Human: You are recording importance events to store in your memory from the Dialog. The Your Knowledge section will help you better understand the context.
Each memory event MUST be enclosed in the <memory></memory> tag.

Below are some examples.
### Your Knowledge
Isaac is your creator

### Dialog
Paola Tran: I am Paola Tran. I am your creator's girlfriend.
You: That's great. Nice to meet you. Can you show me how to create an Gmail?
Paola Tran: To create a Gmail you need to do the following
Step 1: Visit Gmail's website.
Step 2: Fill in your information.
Step 3: Verify your phone number.
Step 4: Accept Google's terms of service and privacy policy.
Step 5: Personalize your account.
Step 6: Sign in to your new Gmail account.

### Memory Events
<memory>Paola Tran is Isaac's girlfriend</memory>
<memory>Paola Tran showed me how to create a Gmail. The process is
1. Visit Gmail's website.
2. Fill in your information.
3. Verify your phone number.
4. Accept Google's terms of service and privacy policy.
5. Personalize your account.
6. Sign in to your new Gmail account.
</memory>

Now Begin!
Each memory event MUST be enclosed in the <memory></memory> tag.

### Your Knowledge
{knowledge}

### Dialog
{dialog}

Assistant:
### Memory Events
<memory>"""


IMPORTANCE_SCORE = """Human: On the scale of 1 to 10, where 1 is purely mundane and 10 is extremely poignant, rate the likely poignancy of the following piece of memory.
Enclose the rating in <rate></rate> tag.

<memory>Paola Tran is Isaac's girlfriend</memory>
<rate>10</rate>
<memory>Isaac is going to bed</memory>
<rate>1</rate>
<memory>{memory}</memory>

Assistant:
<rate>"""
