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
