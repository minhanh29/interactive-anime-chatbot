class HistoryManager:
    def __init__(self, bot_name, max_messages=10):
        self.history = []
        self.user_role = "USER"
        self.bot_role = "BOT"
        self.max_messages = max_messages
        self.overlap_messages = int(max_messages//3)
        self.new_message_count = 0
        self.bot_name = bot_name
        self.default_history = """Human: Who created you?\n\nAssistant: I am created and developed by Isaac Nguyen or Isaac."""
        self.reset()

    def reset(self):
        self.history = []

    def handle_history_size(self):
        while len(self.history) > self.max_messages * 2:
            self.history.pop(0)

    def add_message(self, message, role, speaker_name):
        self.new_message_count += 1
        self.history.append({
            "role": role,
            "speaker_name": speaker_name,
            "message": message.strip()
        })
        self.handle_history_size()

    def add_bot_message(self, message):
        self.add_message(message, self.bot_role, self.bot_name)

    def add_user_message(self, message, user_name="Isaac Nguyen"):
        self.add_message(message, self.user_role, user_name)

    def need_mutation(self):
        return len(self.history) >= self.max_messages and \
            self.new_message_count >= self.max_messages - self.overlap_messages

    def done_mutation(self):
        self.new_message_count = 0

    def to_string(self):
        history_str = ""
        for item in self.history[-self.max_messages:]:
            if item["role"] == self.user_role:
                history_str += "<user>" + item["speaker_name"] + "</user><message>" + item["message"] + "</message>\n"
            elif item["role"] == self.bot_role:
                history_str += "<you>" + self.bot_name + "</you><message>" + item["message"] + "</message>\n"
        return history_str.strip()

    def to_string_for_response(self):
        history_str = ""
        for item in self.history[-self.max_messages:]:
            if item["role"] == self.user_role:
                history_str += "\n\nHuman: <name>" + item["speaker_name"] + "</name><message>" + item["message"] + "</message>"
            elif item["role"] == self.bot_role:
                history_str += "\n\nAssistant: <answer>" + item["message"] + "</answer>"
        return history_str
