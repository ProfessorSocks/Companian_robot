# ============================================================
# ROBOT-Q RECENT CONVERSATION HISTORY
# ============================================================
#
# This module stores a small rolling window of the current
# conversation.
#
# This is NOT long-term memory.
#
# Its only job is to let Robot-Q remember the last few
# messages in the active conversation.
# ============================================================


class ConversationHistory:

    def __init__(self, max_messages=6):
        """
        Create a rolling conversation history.

        max_messages=6 means Robot-Q remembers roughly
        three user/assistant exchanges.
        """

        self.max_messages = max_messages
        self.messages = []


    # --------------------------------------------------------
    # ADD MESSAGES
    # --------------------------------------------------------

    def add_user(self, message):
        """Add a message from Camille."""

        self.messages.append({
            "role": "user",
            "content": message
        })

        self._trim()


    def add_assistant(self, message):
        """Add a message from Robot-Q."""

        self.messages.append({
            "role": "assistant",
            "content": message
        })

        self._trim()


    # --------------------------------------------------------
    # READ HISTORY
    # --------------------------------------------------------

    def get_messages(self):
        """
        Return a copy of the current conversation history.

        Returning a copy prevents other parts of Robot-Q
        from accidentally modifying the stored history.
        """

        return list(self.messages)


    # --------------------------------------------------------
    # CLEAR HISTORY
    # --------------------------------------------------------

    def clear(self):
        """Forget the current short-term conversation."""

        self.messages.clear()


    # --------------------------------------------------------
    # INTERNAL
    # --------------------------------------------------------

    def _trim(self):
        """
        Keep only the newest messages.

        Once the history grows beyond max_messages,
        the oldest messages are removed.
        """

        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]