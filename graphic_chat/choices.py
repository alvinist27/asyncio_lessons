from enum import Enum


class ReadConnectionStateChanged(Enum):
    INITIATED = 'устанавливаем соединение'
    ESTABLISHED = 'соединение установлено'
    CLOSED = 'соединение закрыто'

    def __str__(self):
        return str(self.value)


class SendingConnectionStateChanged(Enum):
    INITIATED = 'устанавливаем соединение'
    ESTABLISHED = 'соединение установлено'
    CLOSED = 'соединение закрыто'

    def __str__(self):
        return str(self.value)


class NicknameReceived:
    def __init__(self, nickname):
        self.nickname = nickname


class QueueNames(Enum):
    MESSAGES = 'messages'
    MESSAGES_TO_SAVE = 'messages_to_save'
    SENDING_MESSAGES = 'sending_messages'
    STATUS_UPDATES = 'status_updates'
    WATCHDOG = 'watchdog'

    def __str__(self):
        return str(self.value)
