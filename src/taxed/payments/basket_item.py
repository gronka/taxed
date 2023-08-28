from taxed.core import EmptySchema

class BasketItem(EmptySchema):
    AdminNotes: str
    ItemId: str
    ItemType: str
    Name: str
    Price: int
