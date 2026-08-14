from dataclasses import dataclass


@dataclass
class PhonieTVEvent:
    event_type: str
    event_payload: object

