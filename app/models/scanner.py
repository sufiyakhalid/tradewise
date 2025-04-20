from pydantic import BaseModel


class ScannerItem(BaseModel):
    name: str
    url: str
    description: str
    table_id: str
