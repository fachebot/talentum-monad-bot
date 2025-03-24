import hashlib
import binascii
from Crypto.Cipher import AES
from eth_account import Account


class Keystore:
    def __init__(self, address, ciphertext):
        self.address = address
        self.ciphertext = ciphertext


# 全局常量
salt = binascii.unhexlify("57185eb887f524fb66cbb2391193b487")
iv = binascii.unhexlify("86b3e10b7c968f347656c55029098df5")


def encrypt_private_key(private_key, password):
    """
    加密私钥函数

    Args:
        private_key: 原始私钥字符串
        password: 加密密码

    Returns:
        包含地址和加密私钥的密钥库对象
    """
    # 从私钥创建钱包
    account = Account.from_key(private_key)
    address = account.address

    # 生成加密密钥
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000, 16)

    # 加密私钥
    cipher = AES.new(
        key, AES.MODE_CTR, nonce=b"", initial_value=int.from_bytes(iv, byteorder="big")
    )
    ciphertext = cipher.encrypt(private_key.encode("utf-8"))

    return Keystore(
        address=address, ciphertext=binascii.hexlify(ciphertext).decode("ascii")
    )


def decrypt_private_key(keystore, password):
    """
    解密私钥函数

    Args:
        keystore: 密钥库对象
        password: 加密时使用的密码

    Returns:
        解密后的原始私钥字符串
    """
    # 获取加密文本
    ciphertext = keystore.ciphertext

    # 生成解密密钥
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000, 16)

    # 解密私钥
    encrypted_buffer = binascii.unhexlify(ciphertext)
    decipher = AES.new(
        key, AES.MODE_CTR, nonce=b"", initial_value=int.from_bytes(iv, byteorder="big")
    )
    decrypted = decipher.decrypt(encrypted_buffer)

    private_key = decrypted.decode("utf-8")

    # 验证解密后的私钥是否正确
    account = Account.from_key(private_key)
    decrypted_address = account.address

    if decrypted_address.lower() != keystore.address.lower():
        raise ValueError("地址不匹配")

    return private_key
