from pydantic import BaseModel, Field

class Chat(BaseModel):
    id: int
    
class User(BaseModel):
    id: int
    
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