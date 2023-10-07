from marshmallow import fields, Schema


class CompanySchema(Schema):
    id = fields.Integer()
    title = fields.String()
    current_stock_price = fields.Integer()
    game_id = fields.Integer()


class PlayerSchema(Schema):
    id = fields.Integer()
    capital = fields.Integer()
    clear_capital = fields.Integer()
    game_id = fields.Integer()
    vk_id = fields.Integer()
    name = fields.Str()
    last_name = fields.Str()


class GameSchema(Schema):
    id = fields.Integer()
    chat_id = fields.Integer()
    players = fields.List(fields.Nested(PlayerSchema))
    companys = fields.List(fields.Nested(CompanySchema))
    is_active = fields.Bool()
    created_at = fields.DateTime()
    max_rounds = fields.Integer()
    current_round = fields.Integer()


class GameInChat(Schema):
    chat_id = fields.Integer(required=True)
