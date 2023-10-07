import typing

if typing.TYPE_CHECKING:
    from admin_api.web.app import Application


def setup_routes(app: "Application"):
    from admin_api.game.views import ListGamesView
    from admin_api.game.views import ListGamesInChatView
    from admin_api.game.views import ListPlayersView
    from admin_api.game.views import ListCompanysView

    app.router.add_view('/games.list', ListGamesView)
    app.router.add_view('/games.inchat', ListGamesInChatView)
    app.router.add_view('/players.list', ListPlayersView)
    app.router.add_view('/companys.list', ListCompanysView)
