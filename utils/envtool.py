import os
from dotenv import load_dotenv,set_key,find_dotenv
env_path=find_dotenv(r".env")

if not env_path:
    raise Exception(f"找不到{env_path}")
def refresh_token(lists:dict):
    if not lists:
        # 列表无信息
        return

    for key,value in lists.items():
        set_key(env_path,key,str(value))
        print(key,"已更新")
    load_env()
def load_env():
    load_dotenv(env_path, override=True)
