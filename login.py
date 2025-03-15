import json
import time
import logging
import cloudscraper
from web3.eth.eth import Eth
from eth_account.messages import encode_defunct


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

proxy = None
proxy_config = json.load(open("config/proxy.json"))
if proxy_config["enable"]:
    username = proxy_config["username"]
    password = proxy_config["password"]
    proxy_dns = proxy_config["proxy_dns"]
    proxy = {"https": "http://{}:{}@{}".format(username, password, proxy_dns)}


def is_json(content):
    try:
        json.loads(content)
        return True
    except ValueError:
        return False


def handle_response(resp):
    ok = resp.status_code >= 200 and resp.status_code < 300

    if not is_json(resp.content):
        if ok:
            return "ok"
        else:
            raise Exception(f"status_code: {resp.status_code}")

    data = resp.json()
    if ok:
        return data
    else:
        if "message" in data:
            raise Exception(data["message"])
        raise Exception(f"status_code: {resp.status_code}")


def get_signature(requests: cloudscraper.CloudScraper, address: str):
    payload = {"address": address, "type": "METAMASK"}
    resp = requests.post(
        "https://monad-api.talentum.id/api/auth/signature", json=payload, proxies=proxy
    )
    data = handle_response(resp)
    return data


def verify_signature(
    requests: cloudscraper.CloudScraper,
    session_id: str,
    signature: str,
):
    payload = {"session_id": session_id, "signature": signature}
    resp = requests.post(
        "https://monad-api.talentum.id/api/auth/verify-signature",
        json=payload,
        proxies=proxy,
    )
    data = handle_response(resp)
    return data


def main():
    keys = []
    with open("config/keys.json") as fp:
        keys = json.load(fp)

    tokens = []
    for pk in keys:
        account = Eth.account.from_key(pk)

        try:
            requests = cloudscraper.create_scraper(disableCloudflareV1=False)
            sig = get_signature(requests, account.address)

            message = encode_defunct(text=sig["message"])
            signed_message = Eth.account.sign_message(message, private_key=pk)

            result = verify_signature(
                requests, sig["session_id"], signed_message.signature.hex()
            )

            tokens.append("Bearer " + result["access_token"])
            logging.info(f"{account.address} 登录成功, 已记录Bearer Token")
        except Exception as e:
            logging.error(f"{account.address} 登录失败, {str(e)}")
            time.sleep(3)

    with open("config/tokens.json", "w") as fp:
        json.dump(tokens, fp)
        logging.info("全部账号登录成功，已更新 config/tokens.json 文件")


if __name__ == "__main__":
    main()
