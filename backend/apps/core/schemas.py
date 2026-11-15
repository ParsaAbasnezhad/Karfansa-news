from ninja import Schema


class HealthOut(Schema):
    status: str
    checks: dict[str, str]
