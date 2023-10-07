from aiohttp.web import run_app

from kts_backend.web.app import application

if __name__ == "__main__":
    run_app(application, host='127.0.0.1', port='8000')
