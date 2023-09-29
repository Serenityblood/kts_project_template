import yaml


def build_query(host: str, method: str, params: dict) -> str:
    url = host + method + "?"
    if "v" not in params:
        params["v"] = "5.131"
    url += "&".join([f"{k}={v}" for k, v in params.items()])
    return url


def config_from_yaml(config_path):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

        config = {'bot': {
            'group_id': raw_config['bot']['group_id'],
            'token': raw_config['bot']['token']
        }}
        return config
