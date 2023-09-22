from aiohttp_apispec import request_schema, response_schema

from admin_api.game.schemes import CompanyAddSchema, CompanySchema
from admin_api.web.app import View
from admin_api.web.middlewares import HTTP_ERROR_CODES
from admin_api.web.mixins import AuthRequiredMixin
from admin_api.web.utils import json_response, error_json_response


class AddCompanyView(AuthRequiredMixin, View):
    @request_schema(CompanyAddSchema)
    @response_schema(CompanySchema, 200)
    async def post(self):
        title = self.data['title']
        if await self.request.app.store.games.get_company_by_title(title) is not None:
            return error_json_response(
                http_status=409,
                status=HTTP_ERROR_CODES[409],
                data=self.data,
                message='Такая компания уже существует'

            )
        current_stock_price = self.data['current_stock_price']
        company = await self.request.app.store.games.create_company(
            title=title,
            current_stock_price=current_stock_price
        )
        return json_response(data=CompanySchema().dump(company))


class ListCompanysView(AuthRequiredMixin, View):
    async def get(self):
        pass


class ResetCompanysView(AuthRequiredMixin, View):
    async def get(self):
        pass
