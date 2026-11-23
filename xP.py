# -*- coding: utf-8 -*-
import time
import requests, json, binascii, time, urllib3, base64, datetime, re, socket, threading, random, os, sys
from protobuf_decoder.protobuf_decoder import Parser
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from random import choice

try:
    import psutil
except ImportError:
    psutil = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


LANGS = ["en", "bn"]


def random_badge():
    badge_list = [
        "909000014", "909000141", "909039008", "909045017", "1001000043",
        "1001000005", "1001000004", "1001000003", "1001000002",
        "1309000065", "1309000071", "1309000112", "1309000162",
        "1309000134", "1309000261", "1309000262"
    ]
    return random.choice(badge_list)


def EnC_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return cipher.encrypt(pad(bytes.fromhex(HeX), AES.block_size)).hex()


def ArA_CoLor():
    Tp = ["32CD32", "00BFFF", "00FA9A", "90EE90", "FF4500", "FF6347", "FF69B4",
          "FF8C00", "FF6347", "FFD700", "FFDAB9", "F0F0F0", "F0E68C", "D3D3D3",
          "A9A9A9", "D2691E", "CD853F", "BC8F8F", "6A5ACD", "483D8B", "4682B4",
          "9370DB", "C71585", "FF8C00", "FFA07A"]
    return random.choice(Tp)


def DEc_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return unpad(cipher.decrypt(bytes.fromhex(HeX)), AES.block_size).hex()


def xBunnEr():
    avatar_list = [
        '902000141', '902000114', '902000126', '902000144', '902000147',
        '902000152', '902000161', '902000162', '902000150', '902000135',
        '902000128', '902000083', '902000149', '902000148', '902000146',
        '902000186', '902000305', '902000306', '902027027', '902027022',
        '902027016', '902027017', '902037004'
    ]
    return int(random.choice(avatar_list))


def EnC_PacKeT(HeX, K, V):
    return AES.new(K, AES.MODE_CBC, V).encrypt(pad(bytes.fromhex(HeX), 16)).hex()


def DEc_PacKeT(HeX, K, V):
    return unpad(AES.new(K, AES.MODE_CBC, V).decrypt(bytes.fromhex(HeX)), 16).hex()


def EnC_Uid(H, Tp):
    e, H = [], int(H)
    while H:
        e.append((H & 0x7F) | (0x80 if H > 0x7F else 0))
        H >>= 7
    return bytes(e).hex() if Tp == 'Uid' else None


def EnC_Vr(N):
    N = int(N)
    if N < 0:
        N = 0
    H = []
    while True:
        BesTo = N & 0x7F
        N >>= 7
        if N:
            BesTo |= 0x80
        H.append(BesTo)
        if not N:
            break
    return bytes(H)


def CrEaTe_VarianT(field_number, value):
    field_number = int(field_number)
    value = int(value)
    field_header = (field_number << 3) | 0
    return EnC_Vr(field_header) + EnC_Vr(value)


def DEc_Uid(H):
    n = s = 0
    for b in bytes.fromhex(H):
        n |= (b & 0x7F) << s
        if not b & 0x80:
            break
        s += 7
    return n


def CrEaTe_LenGTh(field_number, value):
    field_number = int(field_number)
    field_header = (field_number << 3) | 2
    encoded_value = value.encode() if isinstance(value, str) else value
    return EnC_Vr(field_header) + EnC_Vr(len(encoded_value)) + encoded_value


def CrEaTe_ProTo(fields):
    packet = bytearray()
    for field, value in fields.items():
        try:
            field = int(field)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict):
            nested_packet = CrEaTe_ProTo(value)
            packet.extend(CrEaTe_LenGTh(field, nested_packet))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    nested_packet = CrEaTe_ProTo(item)
                    packet.extend(CrEaTe_LenGTh(field, nested_packet))
                elif isinstance(item, bool):
                    packet.extend(CrEaTe_VarianT(field, int(item)))
                elif isinstance(item, int):
                    packet.extend(CrEaTe_VarianT(field, item))
                elif isinstance(item, (str, bytes)):
                    packet.extend(CrEaTe_LenGTh(field, item))
        elif isinstance(value, bool):
            packet.extend(CrEaTe_VarianT(field, int(value)))
        elif isinstance(value, int):
            packet.extend(CrEaTe_VarianT(field, value))
        elif isinstance(value, str) or isinstance(value, bytes):
            packet.extend(CrEaTe_LenGTh(field, value))
    return packet


def DecodE_HeX(H):
    R = hex(H)
    F = str(R)[2:]
    if len(F) == 1:
        F = "0" + F
        return F
    else:
        return F


def Fix_PackEt(parsed_results):
    result_dict = {}
    for result in parsed_results:
        field_data = {}
        field_data['wire_type'] = result.wire_type
        if result.wire_type == "varint":
            field_data['data'] = result.data
        if result.wire_type == "string":
            field_data['data'] = result.data
        if result.wire_type == "bytes":
            field_data['data'] = result.data
        elif result.wire_type == 'length_delimited':
            field_data["data"] = Fix_PackEt(result.data.results)
        result_dict[result.field] = field_data
    return result_dict


def DeCode_PackEt(input_text):
    try:
        parsed_results = Parser().parse(input_text)
        parsed_results_objects = parsed_results
        parsed_results_dict = Fix_PackEt(parsed_results_objects)
        json_data = json.dumps(parsed_results_dict)
        return json_data
    except Exception as e:
        print(f"error {e}  xC4.py:143 - CDX.py:138")
        return None


Key, Iv = (
    bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56]),
    bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
)


def Ua():
    versions = [
        '4.0.18P6', '4.0.19P7', '4.0.20P1', '4.1.0P3', '4.1.5P2', '4.2.1P8',
        '4.2.3P1', '5.0.1B2', '5.0.2P4', '5.1.0P1', '5.2.0B1', '5.2.5P3',
        '5.3.0B1', '5.3.2P2', '5.4.0P1', '5.4.3B2', '5.5.0P1', '5.5.2P3'
    ]
    models = [
        'SM-A125F', 'SM-A225F', 'SM-A325M', 'SM-A515F', 'SM-A725F', 'SM-M215F', 'SM-M325FV',
        'Redmi 9A', 'Redmi 9C', 'POCO M3', 'POCO M4 Pro', 'RMX2185', 'RMX3085',
        'moto g(9) play', 'CPH2239', 'V2027', 'OnePlus Nord', 'ASUS_Z01QD',
    ]
    android_versions = ['9', '10', '11', '12', '13', '14']
    languages = ['en-US', 'es-MX', 'pt-BR', 'id-ID', 'ru-RU', 'hi-IN']
    countries = ['USA', 'MEX', 'BRA', 'IDN', 'RUS', 'IND']
    version = random.choice(versions)
    model = random.choice(models)
    android = random.choice(android_versions)
    lang = random.choice(languages)
    country = random.choice(countries)
    return f"GarenaMSDK/{version}({model};Android {android};{lang};{country};)"


def random_channel():
    channel = random.choice(['en', 'bn'])
    return channel


def GLobaL(T, K, V):
    fields = {1: 3, 2: {2: 5, 3: "en"}}
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '1215', K, V)


def ChaT_sQ(T, N, U, sQ, K, V):
    fields = {1: N, 2: {1: int(U), 3: "en", 4: str(sQ)}}
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '1215', K, V)


def ReFLeSH_Yr():
    fields = {4: 264304360}
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0519', Key, Iv)


def LeVe_C(cid, K, V):
    fields = {}
    fields[1] = 4
    fields[2] = {}
    fields[2][1] = int(cid)
    fields[2][2] = 5
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '1201', K, V)


def Send_GhosTs(Uid, Nm, sQ, K, V, lang=None):
    if lang is None:
        lang = random.choice(LANGS)
    fields = {
        1: 61,
        2: {1: int(Uid), 2: {1: int(Uid), 2: 1159, 3: f'{Nm}', 5: 12, 6: 9999,
                            7: 1, 8: {2: 1, 3: 1}, 9: 3, 10: lang},
        3: sQ
    }}
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0519', K, V)


def Send_InV(N, U, K, V):
    fields = {1: 2, 2: {1: int(U), 2: "BD", 4: N}}
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0519', K, V)


RANK_LMT = [
    301, 302, 303, 304, 305, 306, 307, 308, 309, 310,
    311, 312, 313, 314, 315, 316, 317, 318, 319, 320,
    321, 322, 323, 324, 325, 326, 327, 328, 329, 330
]


def Join_Sq(K, V, lang="en"):
    fields = {
        1: 69,
        2: {
            2: lang,
            4: 1,
            5: 2,
            6: 3,
            7: 301,
            8: 301,
            10: "\u0001\u0007\t\n\u000b\u0012\u0019\u001a ')",
            11: 1,
            12: {
                1: "08FFF3BF1BAC848402085E0444440000006300030060002D32F5102313BCA523467625141101041efea78a17ca3ca4f96aa04d770000004f1e1e1001cacfa16d",
                2: 1078,
                3: "rPTP\u0016\b\u0006N\u0005\u0003_\bQ\f\u0001P\u0003\u0004\u0004\u0000\u0001\u0001\u0000\u000e\u0002\u0000UP\u000b\fS\u0001\\T\u0004\u0006UX\r\u0000\u0016\b\u0007NsYILL\u001d\t\u001a\u0003\u001f\u0017\b\nI\u0005_xp\u0005[aIozsdK@voV|q\u000fp\nc\u007f\u000bqx\b\u001a\u0007N|YkYsVtL}bs~^Tq\u007fOYxUVZ_TXeE\u000b\u0017_W[A\u0016ez\u001bsIH\u0007Ia[t~cSiCmPf^^U\tYS]\u000e_}\u0003\u0005q\f\u0003|\u0004\u0015\u0003\u0005HTlm\f\u0012sttgAu@@}oS\u0002[\u0012lx\rUY~\u0007W\u0004\u001b\rIM\u0001b\u0019_jj\u001ao\u0000rAl^JSG|RO\u0019x\u001fV@Ft\u0004\u0015\u0000J\u0004\u0000}\u0000d\fweA@[{ScAgpouVp\u0004\\xn\\w\t\u001a\u0001I_R[}uPn\t\u0002AqX\n_W\u000b^\u0002@Xpy\u0002LK\u0017B\b\u001a\u0007\nJEwZ_t[@b\u001d\u0003z{M\u0001\u0001\u0005v\u0004UW\u0000^lsZ]E\t\u001a\u000bI}\u0012\u0007Veg\b|C\u001e\u000bP\u0006^b\fY@\u001eV\u0005u\u001dr\u0012o\u0005\b\u001a\u0002NPM~YB\u007f`w\u0003gm\fJdl\u007f\u0003aBW\u0016KO\u0002~sw\u000b\u0017\u000b\bID~\u0000\u0019W]KvRyK]gbFKM\u0004\u0002Ax\u0001C]vOt\b\u001a\u0003NYBJQ}SW]sDVLU\u001ea~^BU~hO\u001a\fmlE\u000b",
                4: "wY\\S",
                6: 12,
                7: "\u0012~quosu\u0004\u0016\u0012",
                8: "1.132.6",
                9: 3,
                10: 2,
                11: "0003626253513637456372725663416456324b796f566c586c6449716f4662743755656f5a4c633547475052557472782f7646515a4c54753272754d7432676d6875504f4d6c5a74444371496c4c5944447961546572366864394e6774365462364e754549774959395243614f3348793873666b47696c6444656b36394846426e3657442b31415430695566336e42714b41724b38315945743231393671617a4e61434144514f6772466c6e614358306f646849436b35625347476963687a6e61764850757264562b5a4365576d4a6470736f556961504d544c3039587662345530674b6453486d4a396b2b56476767432f6d525972613965476c52444d4a4d45566b36434a4458786e6a6263327a7a4c536e32576a5a4977646f7a305750796368415a4970636f61366c6d35794474636c734c3953514c74615055617370626549314f6b5a5a3265517062786837774152464e617a4642795661354a79546e675558425a796246566565464f656a6b6d53585a714e5764567a65314443583858737a414364795246636332624e6a7438476e4866396d61744d492b766a33577a6446526c537073655350582f364945714157546c45306a6958785674656144586a2f6878716b49312b6339695534736f52666578526e757548486d4f33583839476277475678695475774278764772746532616732582f4f4f51497a44314d644177475177386e364b584c646c4f44547274654f7448306170324174674e6d4634694d6a654c484e4c70504c366964694e5850594633413d3d"
            },
            17: "\u0001\u0002\u0003\u0004\u0005",
            18: "\u0001\u0002\u0003\u0004\u0005",
            21: [
                {1: 3, 2: 394},
                {1: 4, 2: 391},
                {1: 5, 2: 192},
                {1: 29, 2: 204},
                {1: 22, 2: 120},
                {1: 14, 2: 175},
                {1: 21}
            ],
            24: "a_6837612683929527434",
            26: "https://dl-sg-production.freefiremobile.com/D5A73B5E05EC88BB7181_7104104913_107_1767710870_0",
            28: {1: 81, 2: 8},
            29: 16
        }
    }
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0519', K, V)


def RefLeSh(K, V, lang="en"):
    fields = {
        1: 67,
        2: {1: lang, 6: 315, 7: 322, 10: 1, 12: 1, 13: {}, 14: {}}
    }
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0519', K, V)


def trydecyasser(pack):
    try:
        r = pack['5']['data']['3']['data']['31']['data']
    except KeyError:
        r = pack['5']['data']['31']['data']
    except:
        return None
    return r


def yasser_Chat(uid, code, K, I, lang="en"):
    fields = {
        1: 3,
        2: {1: uid, 3: lang, 4: str(code)}
    }
    yasser_fields = str(CrEaTe_ProTo(fields).hex())
    return GeneRaTePk(str(yasser_fields), '1215', K, I)


def yasser_quitcaht(uid, K, I, lang="en"):
    fields = {
        1: 4,
        2: {1: uid, 3: lang}
    }
    yasser_fields = str(CrEaTe_ProTo(fields).hex())
    return GeneRaTePk(str(yasser_fields), '1215', K, I)


def yasser_SendInv(bot_uid, uid, K, V):
    fields = {
        1: 33,
        2: {
            1: int(uid), 2: "ME", 3: 1, 4: 1, 6: "yyt", 7: 330, 8: 1000,
            9: 100, 10: "DZ", 12: 1, 13: int(uid), 16: 1,
            17: {2: 159, 4: "y[WW", 6: 11, 8: "1.118.1", 9: 3, 10: 1},
            18: 306, 19: 18, 24: xBunnEr(), 26: {},
            27: {1: 11, 2: int(bot_uid), 3: 999},
            28: {}, 31: {1: 1, 2: 32768}, 32: 32768,
            34: {1: bot_uid, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"}
        }
    }
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0519', K, V)


def yasser_Msg(msg, owner, bot, K, I, lang="en"):
    """
    Squad-chat message packet (opcode 1201).
    field 1 = sender uid (bot)
    field 2 = room owner uid (target)
    """
    fields = {
        1: bot,
        2: owner,
        4: str(msg),
        5: 1756580149,
        7: 2,
        8: 904990072,
        9: {
            1: "ariyan_DEV",
            2: xBunnEr(),
            4: 330,
            5: 827001005,
            8: "ariyan_dev",
            10: 1,
            11: 1,
            13: {1: 2},
            14: {
                1: 1158053040,
                2: 8,
                3: ("\u0010\u0015\b\n\u000b\u0015\f\u000f"
                    "\u0011\u0004\u0007\u0002\u0003\r\u000e"
                    "\u0012\u0001\u0005\u0006")
            }
        },
        10: lang,
        13: {2: 2, 3: 1}
    }
    Pk = CrEaTe_ProTo(fields).hex()
    Pk = "080112" + EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return GeneRaTePk(Pk, '1201', K, I)


def ExiT(K, V):
    fields = {1: 7, 2: {1: int(00000000)}}
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0519', K, V)


def reflesh(uid, K, V):
    fields = {
        1: 1,
        2: {
            1: {1: uid, 2: 14, 4: 84},
            2: {6: 9},
            3: {1: uid, 2: 5, 4: 68},
            4: {2: 1596891}
        }
    }
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0519', K, V)

def dance(teamcode,uid,K,V):
    fields={1:21,2:{1:uid,2:909000012,5:{1:uid,3:909000012}}}
    return GeneRaTePk(str(CrEaTe_ProTo(fields).hex()), '0515', K, V)

def GeT_Time(timestamp):
    last_login = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    diff = now - last_login
    h, rem = divmod(diff.seconds, 3600)
    m, s = divmod(rem, 60)
    return h, m, s


def send_keep_alive(K, V):
    fields = {1: 99, 2: {1: int(time.time()), 2: 1}}
    packet_hex = str(CrEaTe_ProTo(fields).hex())
    return GeneRaTePk(packet_hex, '0519', K, V)


# ═════════════════════════════════════════════════════════════
#  AUTO-RESTART FUNCTIONS — DISABLED
# ═════════════════════════════════════════════════════════════
def ResTarTinG():
    print('\n[Auto-Restart DISABLED] ResTarTinG() called — ignored')
    return


def AuTo_ResTartinG():
    print('\n[Auto-Restart DISABLED] AuTo_ResTartinG() called — ignored')
    return


def xMsGFixinG(n):
    return '🗿'.join(str(n)[i:i + 1] for i in range(0, len(str(n)), 1))


def LogOuT(A):
    R = requests.Session().get(
        f'https://100067.connect.garena.com/oauth/logout?access_token={A}&refresh_token='
    )
    print('LoGOuT =>  xC4.py:439 - CDX.py:424', R.text)
    return R.status_code == 200 and '0' in R.text


def GeneRaTePk(Pk, N, K, V):
    PkEnc = EnC_PacKeT(Pk, K, V)
    _ = DecodE_HeX(int(len(PkEnc) // 2))
    if len(_) == 2:
        HeadEr = N + "000000"
    elif len(_) == 3:
        HeadEr = N + "00000"
    elif len(_) == 4:
        HeadEr = N + "0000"
    elif len(_) == 5:
        HeadEr = N + "000"
    return bytes.fromhex(HeadEr + _ + PkEnc)


def send_msg_all_langs(sock, msg, owner, bot, key, iv):
    sent = 0
    for lang in LANGS:
        try:
            pkt = yasser_Msg(msg, owner, bot, key, iv, lang=lang)
            sock.sendall(pkt)
            sent += 1
        except:
            pass
    return sent


def send_ghost_all_langs(sock, target_uid, nm, squad_code, key, iv):
    sent = 0
    for lang in LANGS:
        try:
            pkt = Send_GhosTs(target_uid, nm, squad_code, key, iv, lang=lang)
            sock.sendall(pkt)
            sent += 1
        except:
            pass
    return sent