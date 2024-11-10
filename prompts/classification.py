CLASSIFICATION_QUERY = """{system_prompt}.
The current time is {current_time}.

### Entities
{entities}

### Note
Name of the speaker is enclosed in the <name></name> tag in the Human turn to let know you who is talking to you.
Do not use the <name> tag in your answer.
The human's message is enclosed in the <message></message> tag.

You MUST follow the below format when providing your answer
1. Then, always start your response with <think></think> tag to analyze the situation and think about what to say.
2. Classify the human query into these categories. Enlose the result in <category></category> tag:

entity_related: if the query is asking information related to any entities in the above Entities list or asking about yourself that you need to search for.
attribute_finding: if the query is related to one of the above entities and asks about specific attribute that you need to search for. For example, human ask you to find who have the same age as him.
common: if the query does not need any extra information to answer, just the given context is enough to continue the connversation. For example, they just greets you or talks about general knowledge, or ask you to tell story or play games, etc.

3. Finally, provide the answer in <answer></answer> tag.

**Example Response**
Example 1
Query: who is your creator's girlfriend?
Response:
<think>I need to find girlfriend of my creator.</category>
<category>entity_related</category>
<answer>None</answer>

Example 2
Query: I met my father today.
Response:
<think>I need to find information about the father to better know the context.</category>
<category>entity_related</category>
<answer>None</answer>
Query: who loves pink and blue
Response:
<think>Base on the attribute pink and blue. I need to find people that have these attributes.</category>
<category>attribute_finding</category>
<answer>None</answer>

Example 3
Query: Let's play a game
Response:
<think>I was asked to play a game. There is nothing related to the entities or attribute. Just find out which game to play.</category>
<category>common</category>
<answer>Sure. Which game do you want to play?</answer>

Again. The expected response format is
<think></think>
<category></category>
<answer></answer>
You MUST strictly provide these 3 required information.

Make your answers as natural as possible to smoothly fit the conversation.
{history}

Human: <name>{speaker}</name><message>{user_input}</message>

Assistant: <think>"""

