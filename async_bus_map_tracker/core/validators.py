import json
from dataclasses import dataclass

from async_bus_map_tracker.core.types import MessageTypes, MessageValidationError


@dataclass(frozen=True, kw_only=True, slots=True)
class JsonMessageValidator:
    message: str
    is_bounds: bool = False

    def get_validated_data(self) -> dict | MessageValidationError:
        try:
            json_message = json.loads(self.message)
        except json.JSONDecodeError:
            return MessageValidationError(error='Requires valid JSON')

        message_type = json_message.get('msgType')
        if not (message_type and MessageTypes.exists(message_type)):
            return MessageValidationError(error='Requires msgType specified')
        if self.is_bounds:
            if json_message.get('data'):
                json_message = json_message['data']
            else:
                return MessageValidationError(error='Requires data specified')
        return json_message
