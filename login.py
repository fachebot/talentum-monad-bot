import os
import json
import time
import getpass
import logging
import cloudscraper
from web3.eth.eth import Eth
from eth_account.messages import encode_defunct

from keystore import decrypt_private_key


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


def load_from_keys_json():
    """从keys.json加载明文私钥"""
    try:
        with open("config/keys.json") as fp:
            keys = json.load(fp)
            logging.info(f"已从config/keys.json加载 {len(keys)} 个私钥")
            return keys
    except FileNotFoundError:
        logging.error("未找到config/keys.json文件")
        return []
    except Exception as e:
        logging.error(f"从keys.json加载私钥时出错: {str(e)}")
        return []


class Keystore:
    def __init__(self, address, ciphertext):
        self.address = address
        self.ciphertext = ciphertext


def load_from_keystores_json():
    """从keystores.json加载加密的私钥"""
    try:
        with open("config/keystores.json") as fp:
            keystores = json.load(fp)
            if not keystores:
                logging.warning("keystores.json为空")
                return []

            # 提示用户输入密码
            password = getpass.getpass("请输入解密密码: ")

            keys = []
            # 解密所有私钥
            for ks in keystores:
                keystore = Keystore(ks["address"], ks["ciphertext"])
                try:
                    private_key = decrypt_private_key(keystore, password)
                    keys.append(private_key)
                    logging.info(f"成功解密地址 {ks['address']} 的私钥")
                except Exception as e:
                    logging.error(f"解密地址 {ks['address']} 的私钥失败: {str(e)}")

            logging.info(f"已从config/keystores.json成功解密 {len(keys)} 个私钥")
            return keys
    except FileNotFoundError:
        logging.error("未找到config/keystores.json文件")
        return []
    except Exception as e:
        logging.error(f"从keystores.json加载私钥时出错: {str(e)}")
        return []


def load_private_keys():
    """
    让用户选择从哪个文件加载私钥
    """
    keys_exists = os.path.exists("config/keys.json")
    keystores_exists = os.path.exists("config/keystores.json")

    if not keys_exists and not keystores_exists:
        logging.error("未找到config/keys.json和config/keystores.json文件, 无法加载私钥")
        return []

    print("\n请选择加载私钥的方式:")
    options = []

    if keys_exists:
        print("1. 从config/keys.json加载明文私钥")
        options.append("keys")

    if keystores_exists:
        print(
            f"{2 if keys_exists else 1}. 从config/keystores.json加载加密私钥（需要密码）"
        )
        options.append("keystores")

    while True:
        try:
            choice = int(input("\n请输入选项编号: "))
            if 1 <= choice <= len(options):
                selected = options[choice - 1]
                break
            else:
                print(f"无效的选项, 请输入1到{len(options)}之间的数字")
        except ValueError:
            print("请输入有效的数字")

    if selected == "keys":
        return load_from_keys_json()
    else:
        return load_from_keystores_json()


def main():
    keys = load_private_keys()
    if not keys:
        logging.error("没有找到有效的私钥，程序退出")
        return

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
        logging.info("全部账号登录成功, 已更新 config/tokens.json 文件")


if __name__ == "__main__":
    main()
