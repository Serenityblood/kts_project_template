import typing

from admin_api.store.database.database import Database

if typing.TYPE_CHECKING:
    from admin_api.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from admin_api.store.admin.accessor import AdminAccessor
        from admin_api.store.game.accessor import GameAccessor

        self.games = GameAccessor(app)
        self.admins = AdminAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)