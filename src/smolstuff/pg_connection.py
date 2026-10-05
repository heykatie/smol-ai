"""Small Postgres wrapper so WorkflowStore can keep its SQL placeholders."""


class PgConnection:
    def __init__(self, raw) -> None:
        self.raw = raw

    def execute(self, sql, params=()):
        text = sql.replace("?", "%s")
        if text.strip().upper() == "BEGIN IMMEDIATE":
            text = "BEGIN"
        cursor = self.raw.cursor()
        if params:
            cursor.execute(text, params)
        else:
            cursor.execute(text)
        return cursor

    def executescript(self, script: str) -> None:
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self) -> None:
        self.raw.commit()

    def rollback(self) -> None:
        self.raw.rollback()

    def close(self) -> None:
        self.raw.close()
