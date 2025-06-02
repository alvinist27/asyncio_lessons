import json
from dataclasses import dataclass

from async_bus_map_tracker.core.models import MessageErrors, MessageTypes, MessageValidationError


@dataclass(frozen=True, kw_only=True, slots=True)
class JsonMessageValidator:
    message: str

    def get_validated_data(self) -> dict | MessageValidationError:
        try:
            json_message = json.loads(self.message)
        except json.JSONDecodeError:
            return MessageValidationError(error=MessageErrors.INVALID_JSON)

        message_type = json_message.get('msgType')
        if not (message_type and MessageTypes.exists(message_type)):
            return MessageValidationError(error=MessageErrors.NO_MSG_TYPE)
        if message_type == MessageTypes.NEW_BOUNDS.value:
            if json_message.get('data'):
                json_message = json_message['data']
            else:
                return MessageValidationError(error=MessageErrors.NO_DATA_IN_BOUNDS)
        return json_message
