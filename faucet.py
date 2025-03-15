import json
import time
import logging
import cloudscraper
from datetime import datetime


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


def unix_timestamp():
    dt = datetime.now()
    ts = int(time.mktime(dt.timetuple()))
    return ts


def faucets(requests: cloudscraper.CloudScraper, bearer_token: str, wallet_id: str):
    payload = {"user_wallet_address_id": wallet_id}
    url = f"https://monad-api.talentum.id/api/faucets"
    resp = requests.post(
        url,
        headers={
            "authorization": bearer_token,
        },
        json=payload,
        proxies=proxy,
    )
    return handle_response(resp)


def checkin_faucets(requests: cloudscraper.CloudScraper, bearer_token: str):
    url = f"https://monad-api.talentum.id/api/faucets"
    resp = requests.get(
        url,
        headers={
            "authorization": bearer_token,
        },
        proxies=proxy,
    )
    data = handle_response(resp)
    return int(data["seconds_to_next_checkin"])


def get_wallet_addresses(requests: cloudscraper.CloudScraper, bearer_token: str):
    url = f"https://monad-api.talentum.id/api/v2/wallet-addresses"
    resp = requests.get(
        url,
        headers={
            "authorization": bearer_token,
        },
        proxies=proxy,
    )
    wallets = handle_response(resp)
    return wallets[0]


def main():
    with open("config/tokens.json") as fp:
        bearer_tokens = json.load(fp)

    wallet_addresses = {}
    next_checkin_dict = {}

    while True:
        for token in bearer_tokens:
            requests = cloudscraper.create_scraper(disableCloudflareV1=False)

            if token in next_checkin_dict:
                ts = unix_timestamp()
                next_checkin = next_checkin_dict.get(token)
                if ts < next_checkin:
                    continue

            if not token in wallet_addresses:
                try:
                    wallet = get_wallet_addresses(requests, token)
                    wallet_id = wallet["id"]
                    wallet_address = wallet["address"]
                    wallet_addresses.update({token: (wallet_id, wallet_address)})
                except Exception as e:
                    logging.error(f"获取钱包地址失败, {str(e)}")
                    time.sleep(30)
                    continue

            (wallet_id, wallet_address) = wallet_addresses.get(token)

            if token not in next_checkin_dict:
                try:
                    seconds_to_next_checkin = checkin_faucets(requests, token)
                    if seconds_to_next_checkin > 0:
                        ts = unix_timestamp()
                        next_checkin_dict.update({token: ts + seconds_to_next_checkin})
                        logging.info(
                            f"{wallet_address} 还需等待 {seconds_to_next_checkin} 秒"
                        )
                        time.sleep(30)
                        continue
                except Exception as e:
                    logging.error(f"{wallet_address} 检查状态失败, {str(e)}")
                    time.sleep(30)
                    continue

            try:
                logging.info(f"{wallet_address} 开始领水")
                result = faucets(requests, token, wallet_id)

                next_checkin_dict.pop(token, None)
                logging.info(f"{wallet_address} 领水成功, {result}")
            except Exception as e:
                next_checkin_dict.pop(token, None)
                logging.error(f"{wallet_address} 领水失败, {str(e)}")
                time.sleep(30)


if __name__ == "__main__":
    main()
