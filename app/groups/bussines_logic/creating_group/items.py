from typing import TypedDict, List

class Member(TypedDict):
    tab: str
    role: str
    mentor_tab: str | None


class ImportData(TypedDict):
    organizer: Member
    group_name: str
    members: List[Member]
