import json
import os
import requests
from utils import envtool
# import envtool


def get_access_token():
    envtool.load_env()
    app_id = os.environ.get("app_id")
    secret = os.environ.get("secret")
    auth_code = os.environ.get("auth_code")

    open_api_url_prefix = "https://ad.oceanengine.com/open_api/"
    uri = "oauth2/access_token/"
    url = open_api_url_prefix + uri
    data = {
        "app_id": app_id,
        "secret": secret,
        "grant_type": "auth_code",
        "auth_code": auth_code
    }
    rsp = requests.post(url, json=data)
    rsp_data = rsp.json()
    if rsp_data.get("data"):
        print(rsp_data)
        with open("./access_token.json", "w", encoding="utf-8") as f:
            json.dump(rsp_data, f, ensure_ascii=False, indent=2)
        print("访问令牌已保存到 account_list")

        access_token = rsp_data.get("data").get("access_token")
        refresh_token = rsp_data.get("data").get("refresh_token")
        # print(rsp_data)
        newtoken = {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

        envtool.refresh_token(newtoken)  # 更新到环境变量中
    else:
        print(rsp_data)

    return rsp_data


def refresh_access_token():
    envtool.load_env()
    app_id = os.environ.get("app_id")
    secret = os.environ.get("secret")
    auth_code = os.environ.get("auth_code")

    refresh_token = os.environ.get("refresh_token")
    print(refresh_token)
    open_api_url_prefix = "https://ad.oceanengine.com/open_api/"
    uri = "oauth2/refresh_token/"
    refresh_token_url = open_api_url_prefix + uri
    data = {
        "app_id": app_id,
        "secret": secret,
        "grant_type": "auth_code",
        "refresh_token": refresh_token
    }
    rsp = requests.post(refresh_token_url, json=data)
    rsp_data = rsp.json()
    print(rsp_data, type(rsp_data))

    if rsp_data:
        # print(rsp_data)
        with open(r".\access_token.json", "w", encoding="utf-8") as f:
            json.dump(rsp_data, f, ensure_ascii=False, indent=2)
        print("访问令牌已保存到 access_token")
        access_token = rsp_data.get("data").get("access_token")
        refresh_token = rsp_data.get("data").get("refresh_token")
        # print(rsp_data)
        newtoken = {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        envtool.refresh_token(newtoken)  # 更新到环境变量中

    return rsp_data


def openajson(file: str):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data


if __name__ == '__main__':
    # data = get_access_token()
    # print(data)

    data = get_access_token()
    print(data)
