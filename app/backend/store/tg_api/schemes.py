from pydantic import BaseModel, Field

class Chat(BaseModel):
    id: int
    
class User(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None

    @property
    def display_name(self) -> str:
        name = self.first_name
        if self.last_name:
            name += f" {self.last_name}"
        return name
    
class Message(BaseModel):
    message_id: int
    chat: Chat
    from_user: User = Field(..., alias="from")
    text: str | None = None

class CallbackQuery(BaseModel):
    id: str
    from_user: User = Field(..., alias="from")
    message: Message | None = None
    data: str | None = None

class Update(BaseModel):
    update_id: int
    message: Message | None = None
    callback_query: CallbackQuery | None = None