#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/30 0030 下午 4:21
@Author: micheng. <safemonitor@outlook.com>
@File: prpcrypt.py
"""

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex


class Encryption():

    def __init__(self):
        """
        用于对重要数据进行加密, 密钥key长度必须为: 16位(AES-128) 24位(AES-192)  32位(AES-256) Bytes长度
        """
        self.key = "lqpctBm5crSbb&7t"
        self.mode = AES.MODE_CBC

    def encrypt(self, text):
        cryptor = AES.new(self.key, self.mode, b'0000000000000000')

        length = 16
        count = len(text)
        if count < length:
            add = (length - count)
            text = text + ('\0' * add)

        elif count > length:
            add = (length - (count % length))
            text = text + ('\0' * add)

        self.ciphertext = cryptor.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return b2a_hex(self.ciphertext)

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, b'0000000000000000')
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0')


if __name__ == '__main__':
    pc = Encryption()  # 初始化密钥
    import sys

    e = pc.encrypt(sys.argv[1])  # 加密
    d = pc.decrypt(e)  # 解密
    print("加密:", e)
