from marshmallow import fields, Schema


class CompanyAddSchema(Schema):
    id = fields.Integer(required=False)
    title = fields.String(required=True)
    current_stock_price = fields.Integer(required=True)


class CompanySchema(Schema):
    id = fields.Integer()
    title = fields.String()
    current_stock_price = fields.Integer()
    capital = fields.Integer()


class GameSchema(Schema):
    id = fields.Integer()
    chat_id = fields.Integer()
    plyayers = fields.List(fields.Integer())
    companys = fields.List(fields.Integer())
    is_active = fields.Bool()
    created_at = fields.DateTime()
    max_rounds = fields.Integer()
    current_round = fields.Integer()


class PlayerSchem(Schema):
    id = fields.Integer()
    capital = fields.Integer()
    clear_capital = fields.Integer()
    game_id = fields.Integer()
    vk_id = fields.Integer()
    name = fields.Str()
    last_name = fields.Str()
