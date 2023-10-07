import typing

from admin_api.admin.views import AdminCurrentView

if typing.TYPE_CHECKING:
    from admin_api.web.app import Application


def setup_routes(app: "Application"):
    from admin_api.admin.views import AdminLoginView

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
