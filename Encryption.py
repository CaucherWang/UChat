from Crypto.Cipher import DES

key = b'20191126'  # 密钥 8位或16位,必须为bytes


def pad(text):
    if len(text) > 16:
        return False
    while len(text) % 16 != 0:
        text += ' '
    return text


def encryptPasswd(text):
    des = DES.new(key, DES.MODE_ECB)  # 创建一个DES实例
    padded_text = pad(text)
    if not padded_text:
        return False
    encrypted_text = des.encrypt(padded_text.encode('ascii'))  # 加密
    return encrypted_text


def decryptPasswd(encrypted_text):
    des = DES.new(key, DES.MODE_ECB)  # 创建一个DES实例
    plain_text = des.decrypt(encrypted_text).decode().rstrip(' ')  # 解密
    return plain_text


def encodeId(text):
    result = pad(text)
    if not result:
        return False
    return result.encode('ascii')


def decodeId(text):
    text = text.decode('ascii')
    return text.rstrip()


def readMessage(text):
    text = text.decode('utf-8')
    for i in range(len(text)):
        if text[i] == '#' and text[i + 1] == '#' and text[i + 2] == '#':
            return text[:i]
    return False


def readRoomList(text):
    i = 0
    result = list()
    while i <= 1021:
        room_no = int.from_bytes(text[i:i + 4], byteorder='big')
        if room_no == 9999:
            break
        result.append((room_no, text[i + 4:i + 20].decode('ascii')))
        i += 20
    return result


def readUserList(text):
    text = text.decode('ascii')
    i = 0
    result = list()
    while i <= 1021:
        if text[i:i + 3] == '###':
            break
        result.append(text[i:i + 16].rstrip())
        i += 16
    return result
