from marshmallow import Schema, fields

class AdminSchema(Schema):
    id = fields.Int(dump_only=True)
    tg_id = fields.Int(required=True)
    password_hash = fields.Str(required=True)