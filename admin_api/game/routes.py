import typing

if typing.TYPE_CHECKING:
    from admin_api.web.app import Application


def setup_routes(app: "Application"):
    # from admin_api.game.views import AddCompanyView

    # app.router.add_view("/company.add", AddCompanyView)
    from admin_api.game.views import ListGamesView

    app.router.add_view("/games.list", ListGamesView)
