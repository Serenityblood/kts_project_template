from aiohttp.web_exceptions import HTTPUnauthorized, HTTPForbidden
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import get_session, new_session

from admin_api.admin.schemes import AdminSchema
from admin_api.web.app import View
from admin_api.web.middlewares import HTTP_ERROR_CODES
from admin_api.web.utils import json_response, error_json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        email = self.data['email']
        password = self.data['password']
        admin = await self.request.app.store.admins.get_by_email(email)
        if admin is None:
            raise HTTPForbidden('No such user in db')

        if admin.is_password_valid(password):
            session = await new_session(self.request)
            session['admin'] = {"email": admin.email, "id": admin.id}
            return json_response(
                data=AdminSchema().dump(obj=admin)
            )
        raise HTTPForbidden('No such user in db')


class AdminCurrentView(View):
    @response_schema(AdminSchema, 200)
    async def get(self):
        if session := await get_session(self.request):
            admin = await self.request.app.store.admins.get_by_email(
                session['admin']['email']
            )
            return json_response(data=AdminSchema().dump(obj=admin))
        else:
            raise HTTPUnauthorized
