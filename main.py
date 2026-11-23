# -*- coding: utf-8 -*-
import json, base64, datetime, re, http.client, ssl, gzip, asyncio, gc, sys, os, time
import threading, queue, socket, struct, traceback, uuid
from io import BytesIO
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import jwt, urllib3, hashlib, hmac, string, random, requests
from protobuf_decoder.protobuf_decoder import Parser
from google.protobuf.timestamp_pb2 import Timestamp
from rich.console import Console
from cfonts import render, say
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

import xK
from xP import *

# ================== Config ==================
RCD = 1
RDT = .1
RES = 20000
OBV = "ob55"
RF = False
RAF = {"BD": "accounts.txt"}
ADMIN_UID = "622534362"

TOKEN_FILE = "token.json"
TOKEN_WORKERS = 15
TOKEN_MAX_RETRY = 10
TOKEN_RETRY_DELAY = 2.0
TOKEN_REFRESH_INTERVAL = 3 * 60 * 60   # ৩ ঘণ্টা (১০,৮০০ সেকেন্ড) পরপর পুরোনো টোকেন ডিলিট করে নতুন বানাবে

zahid_enc  = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
zahid_enc1 = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])
zahid_key  = b"Yg&tc%DEuh6%Zc^8"
zahid_iv   = b"6oyZDr22E3ychjM%"

LOGIN_SERVERS = ["https://loginbp.ppmainecoonghj.com/"]

console = Console()
lock = threading.Lock()
sem = threading.Semaphore(10000)
connected_bots = {}
connected_lock = threading.Lock()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

login_url = LOGIN_SERVERS[0]
ob = "OB55"
verr = None
host = "loginbp.ppmainecoonghj.com"
active_count = 0

GRANT_URL = "https://ffmconnect.ppmainecoonghj.com/api/v2/oauth/guest/token:grant"

# ================== Timing ==================
STAY_TIME = 15.0             # সেকেন্ড: মোট ১৫ সেকেন্ড গ্রুপে থাকবে
CHAT_AUTH_WAIT   = 0.25
CHAT_JOIN_WAIT   = 0.25
CHAT_RETRY_DELAY = 0.15
SECOND_MSG_DELAY = 1.0       # ১ম মেসেজের ১ সেকেন্ড পর ২য় মেসেজ পাঠাবে
EMOTE_AFTER_MSG_WAIT = 0.20  # ২য় মেসেজের পর ইমোট মারার বিরতি
JOIN_TIMEOUT = 1.5
JOIN_REFRESH = 0.5
CYCLE_RETRY_DELAY = 0.1
JOIN_MAX_TRIES = 100
AUTH_RETRY_DELAY = 3.0
BOT_CRASH_RESTART_DELAY = 2.0

# ================== Greeting, /s1 & Emote Config ==================
S1_BADGE_VALUE = 1048576     # mahir.py এর /s1 ব্যাজ ভ্যালু

GREETING_1 = "Hi, I am ARIYAN"

# দ্বিতীয় মেসেজ বক্স (আপনি আপনার নিজের মতো লেখা বদলে নিতে পারবেন)
GREETING_2 = (
    "[B][00BFFF]■ ARIYAN STORE ■\n"
    "[B][00BFFF]────────────────\n"
    "[B][FFD700]কি কি পাবেন\n"
    "[B][00BFFF]├─[00FF00]TCP Bot\n"
    "[B][00BFFF]├─[00FF00]Glory Bot\n"
    "[B][00BFFF]└─[00FF00]Carding Diamond\n"
    "[B][00BFFF]────────────────\n"
    "[B][FFD700]CONTACT INFO\n"
    "[B][00BFFF]├─[00FF00]Telegram [FFFFFF]@AriyanPrime_A9x\n"
    "[B][00BFFF]└─[00FF00]WhatsApp [FFFFFF]⓪①⑥①⓪③⑥⑨①①⑤\n"
    "[B][00BFFF]────────────────"
)

EMOTE_ID = 909000063         # ← এখানে আপনার নিজের পছন্দের ইমোট আইডি বসিয়ে নিন

HR = {
    "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "Accept": "*/*",
    "Accept-Encoding": "deflate, gzip",
    "X-GA-SV": "1790797445",
    "Authorization": "Bearer",
    "X-GA": "v1 1",
    "ReleaseVersion": ob,
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Unity-Version": "2018.4.12f1",
}

COLORS = [
    "32CD32", "00BFFF", "00FA9A", "90EE90", "FF4500", "FF6347", "FF69B4",
    "FF8C00", "FFD700", "FFDAB9", "F0F0F0", "F0E68C", "D3D3D3", "A9A9A9",
    "D2691E", "CD853F", "BC8F8F", "6A5ACD", "483D8B", "4682B4", "9370DB",
    "C71585", "FFA07A", "FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF",
    "00FFFF", "FFFFFF", "FF1493", "7CFC00", "DC143C", "00CED1", "9400D3",
    "F08080", "20B2AA", "B22222", "DAA520", "00FF7F", "6495ED", "DDA0DD",
    "2E8B57", "3CB371", "6B8E23", "808000", "B8860B", "CD5C5C", "8B0000",
]

AVATAR_LIST = [
    902000011, 902000013, 902047016, 902049015,
    902000154, 902000127, 902000207, 902000305,
    902037031, 902042011, 902053016, 902053018
]


def ArA_CoLor():
    return random.choice(COLORS)


def zahid_add_bot(b, o, r):
    with connected_lock:
        connected_bots[b] = {
            'bot_uid': b, 'original_uid': o, 'region': r,
            'time': datetime.now().strftime("%H:%M:%S"),
        }


def zahid_remove_bot(b):
    with connected_lock:
        connected_bots.pop(b, None)


# ================== Proto helpers ==================
def zahid_find_proto_start(d):
    if not d: return 0
    for i, x in enumerate(d):
        if x == 0x08: return i
    return 0


def zahid_read_varint(d, p):
    v = 0; s = 0
    while True:
        if p >= len(d): raise ValueError("truncated")
        b = d[p]; p += 1
        v |= (b & 0x7F) << s
        if not b & 0x80: return v, p
        s += 7
        if s > 70: raise ValueError("too long")


def zahid_is_printable(t):
    return all(c.isprintable() or c in "\r\n\t" for c in t)


def zahid_put_field(r, k, v):
    if k in r:
        if type(r[k]) is not list: r[k] = [r[k]]
        r[k].append(v)
    else:
        r[k] = v


def zahid_proto_decode(d, depth=0):
    r = {}; p = 0
    try:
        while p < len(d):
            tag, p = zahid_read_varint(d, p)
            f = tag >> 3; w = tag & 7
            if f <= 0: raise ValueError("bad")
            if w == 0:
                v, p = zahid_read_varint(d, p)
            elif w == 1:
                if p + 8 > len(d): raise ValueError("trunc")
                v = struct.unpack("<Q", d[p:p + 8])[0]; p += 8
            elif w == 2:
                ln, p = zahid_read_varint(d, p)
                if p + ln > len(d): raise ValueError("trunc")
                raw = d[p:p + ln]; p += ln
                try:
                    tx = raw.decode("utf-8")
                    if zahid_is_printable(tx): v = tx
                    else:
                        n = zahid_proto_decode(raw, depth + 1)
                        v = n if n else raw.hex()
                except:
                    try:
                        n = zahid_proto_decode(raw, depth + 1)
                        v = n if n else raw.hex()
                    except:
                        v = raw.hex()
            elif w == 5:
                if p + 4 > len(d): raise ValueError("trunc")
                v = struct.unpack("<I", d[p:p + 4])[0]; p += 4
            else:
                raise ValueError("bad wire")
            zahid_put_field(r, str(f), v)
        return r
    except:
        return r


def zahid_get_raw_field(d, tf):
    try:
        p = 0
        while p < len(d):
            tag, p = zahid_read_varint(d, p)
            f = tag >> 3; w = tag & 7
            if w == 0: v, p = zahid_read_varint(d, p)
            elif w == 1:
                if p + 8 > len(d): return None
                v = d[p:p + 8]; p += 8
            elif w == 2:
                ln, p = zahid_read_varint(d, p)
                if p + ln > len(d): return None
                v = d[p:p + ln]; p += ln
            elif w == 5:
                if p + 4 > len(d): return None
                v = d[p:p + 4]; p += 4
            else:
                return None
            if f == tf: return v
        return None
    except:
        return None


def zahid_to_text(v):
    if type(v) is str: return v
    if type(v) is bytes: return v.decode("utf-8", errors="ignore")
    return str(v)


def zahid_varint_encode(v):
    o = bytearray(); v = int(v)
    while v > 127:
        o.append((v & 127) | 128); v >>= 7
    o.append(v)
    return bytes(o)


def zahid_proto_encode(fields):
    o = bytearray()
    for f, v in fields.items():
        if type(v) is dict:
            n = zahid_proto_encode(v)
            o.extend(zahid_varint_encode((f << 3) | 2))
            o.extend(zahid_varint_encode(len(n)))
            o.extend(n)
        elif type(v) is int:
            o.extend(zahid_varint_encode(f << 3))
            o.extend(zahid_varint_encode(v))
        elif type(v) is str:
            e = v.encode()
            o.extend(zahid_varint_encode((f << 3) | 2))
            o.extend(zahid_varint_encode(len(e)))
            o.extend(e)
        elif type(v) is bytes:
            o.extend(zahid_varint_encode((f << 3) | 2))
            o.extend(zahid_varint_encode(len(v)))
            o.extend(v)
    return bytes(o)


# ================== xC4.py / mahir.py হুবহু প্যাকেট জেনারেটর ==================
def xc4_generate_pk(pk_bytes, header_hex, key, iv):
    """xC4.py এর GeneRaTePk এর হুবহু রূপ"""
    enc = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(pk_bytes, 16))
    length_hex = len(enc).to_bytes(4, "big").hex()
    return bytes.fromhex(header_hex + length_hex) + enc


def xc4_auth_chat(owner_uid, chat_code, key, iv):
    """xC4.py এর AutH_Chat(3, OwNer_UiD, CHaT_CoDe, key, iv) এর হুবহু রূপ (1215)"""
    fields = {
        1: 3,
        2: {
            1: int(owner_uid),
            3: "en",
            4: str(chat_code),
        },
    }
    raw = zahid_proto_encode(fields)
    return xc4_generate_pk(raw, "1215", key, iv)


def xc4_send_squad_msg(msg_text, owner_uid, key, iv, region="BD"):
    """xC4.py এর xSEndMsgsQ(Msg, id, K, V, region) এর হুবহু রূপ (080112 + 1201)"""
    avatar = random.choice(AVATAR_LIST)
    fields = {
        1: int(owner_uid),
        2: int(owner_uid),
        4: str(msg_text),
        5: int(time.time()),
        8: 904990072,
        9: {
            1: "[FFFFFF]ARIYAN",
            2: avatar,
            3: 2,
            4: 329,
            5: 800000304,
            6: 66,
            7: 66,
            8: "ONLY ARIYAN",
            9: 66,
            10: 66,
            11: 1,
            12: 66,
            13: {1: 68, 2: 67},
            14: {
                1: 1158053040,
                2: 8,
                3: b"\x10\x15\x08\x0A\x0B\x15\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06",
            },
        },
        10: "en",
        13: {66: 66},
        14: {
            11: {
                1: 3,
                2: 7,
                3: 170,
                4: 999,
                5: 1,
                6: str(region),
                8: 2,
                9: 2,
            }
        },
    }
    inner = zahid_proto_encode(fields)
    pk_bytes = bytes.fromhex("080112") + zahid_varint_encode(len(inner)) + inner
    return xc4_generate_pk(pk_bytes, "1201", key, iv)


def xc4_emote_pkt(bot_uid, emote_id, key, iv, region="BD"):
    """mahir.py এর Emote_k(TarGeT, idT, K, V, region) এর হুবহু রূপ (বট নিজে ইমোট করবে)"""
    b_uid = int(bot_uid)
    fields = {
        1: 21,
        2: {
            1: b_uid,
            2: 909000001,
            5: {
                1: b_uid,
                3: int(emote_id),
            },
        },
    }
    reg_l = str(region).lower()
    if reg_l == "ind":
        p_type = "0514"
    elif reg_l == "bd":
        p_type = "0519"
    else:
        p_type = "0515"

    raw = zahid_proto_encode(fields)
    return xc4_generate_pk(raw, p_type, key, iv)


def xc4_s1_badge_pkt(target_uid, key, iv, region="BD", badge_value=S1_BADGE_VALUE):
    """mahir.py এর /s1 (request_join_with_badge, badge=1048576) এর হুবহু রূপ"""
    reg_up = str(region).upper()
    fields = {
        1: 33,
        2: {
            1: int(target_uid),
            2: reg_up,
            3: 1,
            4: 1,
            5: bytes([1, 7, 9, 10, 11, 18, 25, 26, 32]),
            6: "[C][B][FF0000] ARIYAN",
            7: 330,
            8: 1000,
            10: reg_up,
            11: bytes([49, 97, 99, 52, 98, 56, 48, 101, 99, 102, 48, 52, 55, 56,
                       97, 52, 52, 50, 48, 51, 98, 102, 56, 102, 97, 99, 54, 49, 50, 48, 102, 53]),
            12: 1,
            13: int(target_uid),
            14: {
                1: 2203434355,
                2: 8,
                3: b"\x10\x15\x08\x0a\x0b\x13\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06",
            },
            16: 1,
            17: 1,
            18: 312,
            19: 46,
            23: bytes([16, 1, 24, 1]),
            24: random.choice(AVATAR_LIST),
            26: "",
            28: "",
            31: {
                1: 1,
                2: int(badge_value),
            },
            32: int(badge_value),
            34: {
                1: int(target_uid),
                2: 8,
                3: bytes([15, 6, 21, 8, 10, 11, 19, 12, 17, 4, 14, 20, 7, 2, 1, 5, 16, 3, 13, 18]),
            },
        },
        10: "en",
        13: {
            2: 1,
            3: 1,
        },
    }
    reg_l = str(region).lower()
    if reg_l == "ind":
        p_type = "0514"
    elif reg_l == "bd":
        p_type = "0519"
    else:
        p_type = "0515"

    raw = zahid_proto_encode(fields)
    return xc4_generate_pk(raw, p_type, key, iv)


# ================== Version ==================
def zahid_update_version():
    global login_url, ob, verr, host
    try:
        from google_play_scraper import app as gp
        d = gp("com.dts.freefireth", lang="en", country="ME")
        version = d["version"]
    except Exception:
        version = "1.132.1"
    try:
        x = requests.get(
            "https://version.ggwhitehawk.com/live/ver.php"
            f"?version={version}&lang=en&device=android&channel=android"
            f"&appsttore=googleplay&region=en&whitelist_version=1.3.0"
            f"&whitelist_sp_version=1.0.0&device_name=google%20G011A"
            f"&device_CPU=ARMv7%20VFPv3%20NEON%20VMH"
            f"&device_GPU=Adreno%20(TM)%20640&device_mem=1993",
            timeout=10,
        ).json()
        login_url = x["server_url"]
        ob = x["latest_release_version"]
        verr = x["remote_version"]
        host = login_url.split("https://", 1)[1].split("/", 1)[0]
    except Exception:
        login_url = LOGIN_SERVERS[0]
        ob = "OB55"
        verr = version
        host = "loginbp.ppmainecoonghj.com"
    return login_url, ob, verr


login_url, ob, version = zahid_update_version()
HR["ReleaseVersion"] = ob


# ================== MajorLogin Payload ==================
def zahid_build_login_payload(open_id, access_token, region="BD"):
    try:
        r = requests.head("https://www.google.com", timeout=3)
        sd = r.headers.get("Date")
        if sd:
            from datetime import datetime as _dt, timezone as _tz
            dt = _dt.strptime(sd, "%a, %d %b %Y %H:%M:%S GMT")
            server_time_str = dt.replace(tzinfo=_tz.utc).strftime("%Y-%m-%d %H:%M:%S")
        else:
            server_time_str = str(datetime.now())[:-7]
    except Exception:
        server_time_str = str(datetime.now())[:-7]

    def _get_ip():
        for u in ("https://api.ipify.org", "https://ifconfig.me/ip", "https://ipinfo.io/ip"):
            try:
                rr = requests.get(u, timeout=3, verify=False)
                ip = rr.text.strip()
                if ip and ip.count(".") == 3: return ip
            except Exception:
                continue
        return "59.152.5.188"

    P = {}

    if region == "IND":
        P[3]=server_time_str; P[4]="free fire"; P[5]=1; P[7]="1.134.14"
        P[8]="Android OS 14 / API-34 (UP1A.231005.007/E156BXXS6AYD4)"
        P[9]="Handheld"; P[10]="airtel"; P[11]="CarrierDataNetwork"
        P[12]=2340; P[13]=1080; P[14]="295"
        P[15]="ARM64 FP ASIMD AES | 2200 | 8"; P[16]=5586
        P[17]="Mali-G57 MC2"; P[18]="OpenGL ES 3.2 v1.r38p1"
        P[19]="Google|f4d8aefb-7549-4778-a92b-2ed885bf9ec4"
        P[20]=_get_ip(); P[21]="en"; P[22]=open_id; P[23]="4"
        P[24]="Handheld"; P[25]="samsung SM-A155F"; P[26]="IND"
        P[29]=access_token; P[30]=1; P[41]="airtel"; P[42]="4G"
        P[57]="7428b253defc164018c604a1ebbfebdf"
        P[60]=108009; P[61]=3859; P[62]=5023
        P[64]=3987; P[65]=108009; P[66]=3987; P[67]=108009
        P[70]=4; P[73]=3
        P[74]="/data/app/~~OlJmIW-Yzl-44x2WnJP4Nw==/com.garena.game.ffi-_eDk_pQQMiFk1YUeqwJBvQ==/lib/arm64"
        P[76]=3
        P[77]="dd9d4c174e0472d34b7fd34bd5924bc9|/data/app/~~OlJmIW-Yzl-44x2WnJP4Nw==/com.garena.game.ffi-_eDk_pQQMiFk1YUeqwJBvQ==/base.apk"
        P[78]=3; P[79]=2; P[81]="64"; P[83]="2019121269"
        P[85]=3; P[86]="OpenGLES2"; P[87]=8191; P[88]=4
        P[90]="Coimbatore"; P[91]="TN"; P[92]=9570; P[93]="android"
        P[94]="KqsHT54jON6bxITmlrRyOrXWBqKqZ4BoqPzT/mhtriAfRt2dt7gC8pnAJfj11alcEUA5sD8BshSYQhxXT9RFmU6YzcI1FKK4MwxJcF4+kvelPD1H"
        P[95]=111207; P[96]='{"cur_rate":null,"support_etc2":false}'
        P[97]=1; P[99]="4"; P[100]="4"; P[104]=11921; P[105]=1
        P[106]="https://dl-tata.freefireind.in/live/ABHotUpdates/|https://core-tata.freefireind.in/live/ABHotUpdates/|dff941d41e6e3a9e76f05ed71fdc8d87"
        P[107]="1.6168622e0868ddbd"

    elif region == "ME":
        P[3]=server_time_str; P[4]="free fire"; P[5]=1; P[7]="1.134.14"
        P[8]="Android OS 15 / API-35 (AP3A.240905.015.A2/185014)"
        P[9]="Handheld"; P[10]="TUNTEL"; P[11]="WIFI"
        P[12]=1600; P[13]=719; P[14]="234"
        P[15]="ARM64 FP ASIMD AES | 1820 | 8"; P[16]=2798
        P[17]="Mali-G57"
        P[18]="OpenGL ES 3.2 v1.r49p1-04eac0.2848c17a2fd4e9340e06555168eaa3c9"
        P[19]="Google|f744e396-5694-4e65-995d-97a958f2bd1f"
        P[20]=_get_ip(); P[21]="en"; P[22]=open_id; P[23]="4"
        P[24]="Handheld"; P[25]="INFINIX Infinix X6725"; P[26]="ME"
        P[29]=access_token; P[30]=1; P[41]="TUNTEL"; P[42]="WIFI"
        P[57]="7428b253defc164018c604a1ebbfebdf"
        P[60]=49973; P[61]=11338; P[62]=854
        P[64]=11466; P[65]=49973; P[66]=11466; P[67]=49973
        P[73]=2
        P[74]="/data/app/~~lHFxTCCbupG2QVJmsURtZw==/com.dts.freefireth-N3aCHpHNXpdxjD80uIIbww==/lib/arm64"
        P[76]=1
        P[77]="b8e0cd5e295eee42f5860d3c86e483dd|/data/app/~~lHFxTCCbupG2QVJmsURtZw==/com.dts.freefireth-N3aCHpHNXpdxjD80uIIbww==/base.apk"
        P[78]=3; P[79]=2; P[81]="64"; P[83]="2019121229"
        P[85]=3; P[86]="OpenGLES2"; P[87]=8191; P[88]=4
        P[92]=15078; P[93]="android"
        P[94]="KqsHTx3+QOmBRR1WKvaWewlcpqJBfjki+PPHQoQG8+0yV+Uos7gUFFjHMQ/e7u6han6Fl77r7c3vMN3p8UbKgN+nfycQCgwBmWgBzomx2gj84c+p"
        P[95]=111207; P[96]='{"cur_rate":[90,60,120],"support_etc2":false}'
        P[97]=1; P[99]="4"; P[100]="4"
        P[102]="\x17]ENWU\x0eR5"
        P[104]=52882; P[105]=1
        P[106]="https://dl.ak.freefiremobile.com/live/ABHotUpdates/|https://core-ak.freefiremobile.com/live/ABHotUpdates/|6b2078db9d22dd98f8e9386a39af8462"
        P[107]="c8e41b7a93f02d56e1a94c7b8203f5d1"

    else:  # BD default
        P[3]=server_time_str; P[4]="free fire"; P[5]=1; P[7]="1.134.14"
        P[8]="Android OS 14 / API-34 (UP1A.231005.007/V816.0.15.0.UNQMIXM)"
        P[9]="Handheld"; P[10]="Grameenphone"; P[11]="CarrierDataNetwork"
        P[12]=1666; P[13]=750; P[14]="352"
        P[15]="ARM64 FP ASIMD AES | 2400 | 8"; P[16]=5563
        P[17]="Mali-G57 MC2"
        P[18]="OpenGL ES 3.2 v1.r32p1-01eac0.0a0b917d9265b4c01be9925306306139"
        P[19]="Google|9cc73f7a-91f6-40f6-87ec-5b67e597eb8c"
        P[20]=_get_ip(); P[21]="en"; P[22]=open_id; P[23]="8"
        P[24]="Handheld"; P[25]="Xiaomi 2312DRAABI"; P[26]="BD"
        P[29]=access_token; P[30]=1; P[41]="Grameenphone"; P[42]="Cellular"
        P[57]="7428b253defc164018c604a1ebbfebdf"
        P[60]=109685; P[61]=58294; P[62]=797; P[63]=18000
        P[64]=58818; P[65]=109685; P[66]=58818; P[67]=109685
        P[73]=2
        P[74]="/data/app/~~cqQgpdMykLQEM3odipXatw==/com.dts.freefireth-G6e5yOt1dtuXG5Ambhj18g==/lib/arm64"
        P[76]=1
        P[77]="b8e0cd5e295eee42f5860d3c86e483dd|/data/app/~~cqQgpdMykLQEM3odipXatw==/com.dts.freefireth-G6e5yOt1dtuXG5Ambhj18g==/base.apk"
        P[78]=3; P[79]=2; P[81]="64"; P[83]="2019121229"
        P[85]=3; P[86]="OpenGLES2"; P[87]=4095; P[88]=8
        P[89]=b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
        P[90]="Dhaka"; P[91]="C"; P[92]=8043; P[93]="android"
        P[94]="KqsHT4XbSZhqerDNUhjbS3DxG/4+I62zQU2tZFJN91kBUICAlZ5yujshLKvjlk/KiShfKfis8EeB1PMhFHIodWPncZC4fCHYF3TcTwNj95aWY/S3"
        P[95]=111207; P[96]='{"cur_rate":[60,90,120],"support_etc2":false}'
        P[97]=1; P[98]=1; P[99]="4"; P[100]="4"
        P[102]="GQ]        e"; P[103]=1
        P[104]=45174; P[105]=1
        P[106]="https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|https://core-bs.ggpolarbear.com/live/ABHotUpdates/|a4332cb1c1a84e51dd77441e4856ed5a"
        P[107]="1.9393e7b8e53e8aeb"

    proto_encoded = zahid_proto_encode(P)
    return AES.new(zahid_key, AES.MODE_CBC, zahid_iv).encrypt(pad(proto_encoded, 16))


def zahid_build_auth_token(uid, token, ts, key, iv, mode="online"):
    ah = f"{int(uid):x}"
    if len(ah) > 16: raise ValueError("too long")
    ah = ah.zfill(16)
    enc = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(token.encode(), 16)).hex()
    th = f"{int(ts):08x}"
    tsz = (len(enc) // 2).to_bytes(4, "big").hex()
    if mode == "chat":
        return f"9015{ah}{th}{tsz}{enc}"
    else:
        return f"9015{ah}{th}00000000{tsz}{enc}"


def zahid_decrypt_major_login(resp):
    class A: pass
    a = A()
    ld = zahid_proto_decode(resp)
    if not ld: return None
    au = ld.get("1")
    if type(au) is list: au = au[0]
    if au is None or not isinstance(au, int) or au < 1000000: return None
    tb = ld.get("8")
    if type(tb) is list: tb = tb[0]
    if not isinstance(tb, (str, bytes)): return None
    tok = zahid_to_text(tb)
    if not tok.startswith("eyJ"): return None
    ub = ld.get("10")
    if type(ub) is list: ub = ub[0]
    url = zahid_to_text(ub) if ub else None
    if not url: return None
    ts = ld.get("21")
    if type(ts) is list: ts = ts[0]
    if not isinstance(ts, int): return None
    kb = zahid_get_raw_field(resp, 22)
    ib = zahid_get_raw_field(resp, 23)
    if not kb or not ib: return None
    a.token = tok; a.account_uid = au; a.key = kb; a.iv = ib
    a.timestamp = ts; a.url = url
    return a


def zahid_decrypt_login_data(data):
    class P: pass
    p = P()
    pd = zahid_proto_decode(data)
    if not pd: return None
    ob_ = pd.get("14")
    if type(ob_) is list: ob_ = ob_[0]
    op = zahid_to_text(ob_) if ob_ else None
    cb = pd.get("32")
    if type(cb) is list: cb = cb[0]
    cp_ = zahid_to_text(cb) if cb else None
    if not op or not cp_: return None
    p.Online_IP_Port = op; p.AccountIP_Port = cp_
    p.Clan_ID = None; p.Clan_Compiled_Data = b''; p.AccountName = "Unknown"
    return p


api_sem = threading.Semaphore(10)


def zahid_guest_access(uid, pw):
    with api_sem:
        headers = {
            'User-Agent': "GarenaMSDK/4.0.44(RMX5070 ;Android 14;en;GB;app 1.132.1 2019121229;)",
            'Accept': "application/json",
            'Content-Type': "application/json; charset=utf-8",
            'Accept-Encoding': "gzip",
            'Connection': "Keep-Alive",
        }
        data = {
            "client_id": 100067,
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_type": 2,
            "device_id": f"02-{uuid.uuid4()}",
            "password": pw,
            "response_type": "token",
            "uid": int(uid),
        }
        try:
            r = requests.post(GRANT_URL, json=data, headers=headers, timeout=20, verify=False)
            if r.status_code != 200: return None, None
            result = r.json().get("data", {})
            oid = result.get("open_id")
            atk = result.get("access_token")
            if not oid or not atk: return None, None
            return oid, atk
        except Exception:
            return None, None


def zahid_major_login(payload):
    global login_url
    ut = [login_url] + [s for s in LOGIN_SERVERS if s != login_url]
    seen = set()
    ut = [x for x in ut if not (x in seen or seen.add(x))]
    for base in ut:
        try:
            try:
                th = base.split("https://", 1)[1].split("/", 1)[0]
                socket.gethostbyname(th)
            except:
                continue
            u = f"{base.rstrip('/')}/MajorLogin"
            r = requests.post(u, data=payload, headers=HR, timeout=20, verify=False)
            if r.status_code in (200, 201):
                body = r.content
                start = zahid_find_proto_start(body)
                trimmed = body[start:]
                if len(trimmed) < 200: return None
                if trimmed:
                    login_url = base
                    return trimmed
        except:
            continue
    return None


def zahid_get_login_data(url, payload, token):
    headers = HR.copy()
    headers["Authorization"] = f"Bearer {token}"
    ut = [url] + [s for s in LOGIN_SERVERS if s != url]
    seen = set()
    ut = [x for x in ut if not (x in seen or seen.add(x))]
    for base in ut:
        try:
            try:
                th = base.split("https://", 1)[1].split("/", 1)[0]
                socket.gethostbyname(th)
            except:
                continue
            u = f"{base.rstrip('/')}/GetLoginData"
            r = requests.post(u, data=payload, headers=headers, timeout=20, verify=False)
            if r.status_code in (200, 201):
                body = r.content
                start = zahid_find_proto_start(body)
                trimmed = body[start:]
                if trimmed: return trimmed
        except:
            continue
    return None


# ================== Token.json I/O & Validation ==================
def zahid_session_to_json(sess):
    return {
        'uid': str(sess['uid']),
        'region': sess['region'],
        'bot_uid': str(sess['bot_uid']),
        'auth': sess['auth'],
        'auth_online': sess['auth_online'],
        'ip': sess['ip'],
        'port': sess['port'],
        'ip2': sess['ip2'],
        'port2': sess['port2'],
        'key': base64.b64encode(sess['key']).decode(),
        'iv': base64.b64encode(sess['iv']).decode(),
        'token': sess.get('token', ''),
        'created_at': datetime.now().isoformat(),
    }


def zahid_json_to_session(item, password=None):
    return {
        'uid': str(item['uid']),
        'password': password,
        'region': item.get('region', 'BD'),
        'bot_uid': str(item['bot_uid']),
        'auth': item['auth'],
        'auth_online': item['auth_online'],
        'ip': item['ip'],
        'port': item['port'],
        'ip2': item['ip2'],
        'port2': item['port2'],
        'key': base64.b64decode(item['key']),
        'iv': base64.b64decode(item['iv']),
        'token': item.get('token', ''),
    }


def zahid_load_saved_tokens(path=TOKEN_FILE):
    saved = {}
    if not os.path.exists(path):
        return saved
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data.get('sessions', []):
            try:
                u = str(item.get('uid', '')).strip()
                if u:
                    saved[u] = zahid_json_to_session(item)
            except Exception:
                continue
    except Exception:
        pass
    return saved


def zahid_upsert_single_token(sess, path=TOKEN_FILE):
    with lock:
        data = {'saved_at': datetime.now().isoformat(), 'count': 0, 'sessions': []}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {'saved_at': datetime.now().isoformat(), 'count': 0, 'sessions': []}
        uid_str = str(sess['uid'])
        sessions = [s for s in data.get('sessions', []) if str(s.get('uid')) != uid_str]
        sessions.append(zahid_session_to_json(sess))
        data['sessions'] = sessions
        data['count'] = len(sessions)
        data['saved_at'] = datetime.now().isoformat()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def _is_jwt_expired(token_str, buffer_sec=60):
    if not token_str:
        return True
    try:
        parts = token_str.split(".")
        if len(parts) < 2:
            return True
        b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(b64).decode())
        exp = payload.get("exp")
        if exp and (time.time() + buffer_sec) >= float(exp):
            return True
        return False
    except Exception:
        return True


def zahid_test_session_online(sess):
    if _is_jwt_expired(sess.get('token', '')):
        return False

    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.settimeout(3.0)
        s.connect((sess['ip'], int(sess['port'])))
        s.sendall(bytes.fromhex(sess['auth_online']))
        s.settimeout(1.2)
        try:
            resp = s.recv(4096)
            if resp == b'':
                return False
        except socket.timeout:
            pass
        s.sendall(send_keep_alive(sess['key'], sess['iv']))
        return True
    except Exception:
        return False
    finally:
        try:
            if s: s.close()
        except Exception:
            pass


# ================== PHASE 1: Token Builder ==================
def zahid_build_session(uid, password, region):
    for attempt in range(TOKEN_MAX_RETRY):
        try:
            oid, atk = zahid_guest_access(uid, password)
            if not atk or not oid:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            pyl = zahid_build_login_payload(oid, atk, region=region)
            resp = zahid_major_login(pyl)
            if not resp:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            ad = zahid_decrypt_major_login(resp)
            if not ad:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            url = ad.url.rstrip("/")
            ld = zahid_get_login_data(url, pyl, ad.token)
            if not ld:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            ports = zahid_decrypt_login_data(ld)
            if not ports:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            op = ports.Online_IP_Port
            cp_ = ports.AccountIP_Port
            if not op or not cp_:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            oip, oport = op.split(":")
            cip, cport = cp_.split(":")

            ac = zahid_build_auth_token(int(ad.account_uid), ad.token, int(ad.timestamp), ad.key, ad.iv, mode="chat")
            ao = zahid_build_auth_token(int(ad.account_uid), ad.token, int(ad.timestamp), ad.key, ad.iv, mode="online")

            return {
                'uid': str(uid),
                'password': password,
                'region': region,
                'auth': ac,
                'auth_online': ao,
                'ip': oip, 'port': oport,
                'ip2': cip, 'port2': cport,
                'key': ad.key, 'iv': ad.iv,
                'bot_uid': str(ad.account_uid),
                'token': ad.token,
            }
        except Exception as e:
            with lock:
                console.print(f"[dim red]{uid} token err: {type(e).__name__}[/dim red]")
            time.sleep(TOKEN_RETRY_DELAY)

    return None


# ================== Chat Helper ==================
def _connect_and_auth_chat(ip2, port2, auth, target_uid, chat_code, key, iv):
    sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sc.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sc.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sc.settimeout(4.0)
    sc.connect((ip2, int(port2)))

    sc.sendall(bytes.fromhex(auth))
    time.sleep(CHAT_AUTH_WAIT)

    sc.settimeout(0.2)
    try:
        auth_ack = sc.recv(4096)
        if auth_ack == b'':
            raise ConnectionError("chat_auth_rejected")
    except socket.timeout:
        pass

    sc.sendall(xc4_auth_chat(target_uid, chat_code, key, iv))
    time.sleep(CHAT_JOIN_WAIT)
    return sc


def _send_chat_and_check(sc, pkt):
    sc.sendall(pkt)
    sc.settimeout(0.35)
    try:
        ack = sc.recv(4096)
        if ack == b'':
            raise ConnectionError("chat_server_closed_after_send")
    except socket.timeout:
        pass


# ================== PHASE 2: Single Account Online ==================
def zahid_run_session(sess, gen_stop_event):
    bot_uid = sess['bot_uid']
    region = sess['region']
    auth = sess['auth']
    auth_online = sess['auth_online']
    ip = sess['ip']; port = sess['port']
    ip2 = sess['ip2']; port2 = sess['port2']
    key = sess['key']; iv = sess['iv']

    with lock:
        console.print(f"[green]Bot {bot_uid} {region} LOGGED IN[/green]")

    zahid_add_bot(bot_uid, str(sess['uid']), region)

    cycle_num = 0
    consecutive_join_fails = 0

    while not RF and not gen_stop_event.is_set():
        cycle_num += 1
        sock_online = None
        sock_chat = None
        target_uid = None
        squad_code = None
        chat_code = None

        try:
            # ১) গ্রুপে জয়েন হওয়া (এবং সেই সকেটটাই sock_online হিসেবে ধরে রাখা)
            for attempt in range(JOIN_MAX_TRIES):
                if RF or gen_stop_event.is_set(): break
                try:
                    sock_online = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock_online.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    sock_online.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 524288)
                    sock_online.settimeout(0.8)
                    sock_online.connect((ip, int(port)))
                    sock_online.sendall(bytes.fromhex(auth_online))
                    time.sleep(0.05)

                    deadline = time.time() + JOIN_TIMEOUT
                    last_send = 0
                    while time.time() < deadline:
                        if RF or gen_stop_event.is_set(): break
                        if time.time() - last_send > JOIN_REFRESH:
                            try:
                                sock_online.sendall(Join_Sq(key, iv))
                                last_send = time.time()
                            except:
                                break
                        try:
                            sock_online.settimeout(0.15)
                            data = sock_online.recv(65536)
                            if not data:
                                break
                            hex_data = data.hex()
                            if hex_data.startswith('0500') and len(hex_data) > 100:
                                try:
                                    js = DeCode_PackEt(hex_data[10:])
                                    if js:
                                        packet = json.loads(js)
                                        f5 = packet.get('5', {}).get('data', {})
                                        t_uid = f5.get('1', {}).get('data')
                                        ch = f5.get('17', {}).get('data')
                                        sq = f5.get('31', {}).get('data')
                                        if t_uid and ch is not None and sq is not None:
                                            target_uid = t_uid
                                            chat_code = ch
                                            squad_code = sq
                                            break
                                except:
                                    pass
                        except socket.timeout:
                            continue
                        except (ConnectionResetError, OSError):
                            break
                        except:
                            continue

                    if target_uid:
                        break
                    try: sock_online.close()
                    except: pass
                    sock_online = None
                    time.sleep(CYCLE_RETRY_DELAY)
                except:
                    try:
                        if sock_online: sock_online.close()
                    except: pass
                    sock_online = None
                    time.sleep(CYCLE_RETRY_DELAY)

            if RF or gen_stop_event.is_set():
                try:
                    if sock_online:
                        if target_uid:
                            sock_online.sendall(ExiT(key, iv))
                        sock_online.close()
                except: pass
                break

            if not sock_online or not target_uid:
                consecutive_join_fails += 1
                if consecutive_join_fails >= 3 and sess.get('password'):
                    with lock:
                        console.print(f"[yellow]{sess['uid']} token expired/failed, rebuilding...[/yellow]")
                    new_sess = zahid_build_session(sess['uid'], sess['password'], region)
                    if new_sess:
                        zahid_upsert_single_token(new_sess)
                        sess = new_sess
                        bot_uid = sess['bot_uid']
                        auth = sess['auth']
                        auth_online = sess['auth_online']
                        ip = sess['ip']; port = sess['port']
                        ip2 = sess['ip2']; port2 = sess['port2']
                        key = sess['key']; iv = sess['iv']
                        consecutive_join_fails = 0
                time.sleep(0.05)
                continue

            consecutive_join_fails = 0
            # মোট ১৫ সেকেন্ড গ্রুপে থাকার টাইমার শুরু
            stay_end = time.time() + STAY_TIME

            with lock:
                console.print(f"[cyan]{bot_uid} JOINED cycle {cycle_num} -> owner={target_uid} | chat_code={chat_code}[/cyan]")

            # ২) গ্রুপে ঢোকার সময় একবারই /s1 ব্যাজ রিকোয়েস্ট পাঠানো (প্রতি সাইকেলে ১ বার)
            s1_sent = False
            s1_err = None
            try:
                s1_pkt = xc4_s1_badge_pkt(target_uid, key, iv, region=region, badge_value=S1_BADGE_VALUE)
                sock_online.sendall(s1_pkt)
                s1_sent = True
            except Exception as ex:
                s1_err = f"{type(ex).__name__}: {ex}"

            with lock:
                if s1_sent:
                    console.print(f"[bold blue]{bot_uid} S1 REQUEST SENT (cycle {cycle_num}) -> owner={target_uid}[/bold blue]")
                else:
                    console.print(f"[bold red]{bot_uid} S1 REQUEST FAILED (cycle {cycle_num}) -> err={s1_err}[/bold red]")

            # ৩) ১ম মেসেজ পাঠানো (GREETING_1)
            msg1_sent = False
            msg1_err = None
            msg1_text = f"[c][b][{ArA_CoLor()}]{GREETING_1}"

            for _ in range(3):
                if RF or gen_stop_event.is_set(): break
                try:
                    sock_chat = _connect_and_auth_chat(ip2, port2, auth, target_uid, chat_code, key, iv)
                    pkt1 = xc4_send_squad_msg(msg1_text, target_uid, key, iv, region=region)
                    _send_chat_and_check(sock_chat, pkt1)
                    msg1_sent = True
                    msg1_err = None
                    break
                except Exception as ex:
                    msg1_err = f"{type(ex).__name__}: {ex}"
                    try:
                        if sock_chat: sock_chat.close()
                    except: pass
                    sock_chat = None
                    time.sleep(CHAT_RETRY_DELAY)

            with lock:
                if msg1_sent:
                    console.print(f"[bold green]{bot_uid} MESSAGE 1 SENT (1201, cycle {cycle_num}) -> owner={target_uid}[/bold green]")
                else:
                    console.print(f"[bold red]{bot_uid} MESSAGE 1 FAILED (cycle {cycle_num}) -> err={msg1_err}[/bold red]")

            # ৪) ১ সেকেন্ড বিরতি দিয়ে ২য় মেসেজ বক্স পাঠানো (GREETING_2)
            msg2_sent = False
            msg2_err = None
            if not RF and not gen_stop_event.is_set():
                time.sleep(SECOND_MSG_DELAY)
                for _ in range(2):
                    if RF or gen_stop_event.is_set(): break
                    try:
                        if not sock_chat:
                            sock_chat = _connect_and_auth_chat(ip2, port2, auth, target_uid, chat_code, key, iv)
                        pkt2 = xc4_send_squad_msg(GREETING_2, target_uid, key, iv, region=region)
                        _send_chat_and_check(sock_chat, pkt2)
                        msg2_sent = True
                        msg2_err = None
                        break
                    except Exception as ex:
                        msg2_err = f"{type(ex).__name__}: {ex}"
                        try:
                            if sock_chat: sock_chat.close()
                        except: pass
                        sock_chat = None
                        time.sleep(CHAT_RETRY_DELAY)

                with lock:
                    if msg2_sent:
                        console.print(f"[bold green]{bot_uid} MESSAGE 2 SENT (1201, cycle {cycle_num}) -> owner={target_uid}[/bold green]")
                    else:
                        console.print(f"[bold red]{bot_uid} MESSAGE 2 FAILED (cycle {cycle_num}) -> err={msg2_err}[/bold red]")

            # ৫) ২য় মেসেজ দেওয়ার পরপরই বট নিজে ১টি ইমোট মারবে (online socket দিয়ে)
            emoted = False
            emote_err = None
            if not RF and not gen_stop_event.is_set() and EMOTE_ID:
                time.sleep(EMOTE_AFTER_MSG_WAIT)
                try:
                    emote_pkt = xc4_emote_pkt(bot_uid, int(EMOTE_ID), key, iv, region=region)
                    sock_online.sendall(emote_pkt)
                    emoted = True
                except Exception as ex:
                    emote_err = f"{type(ex).__name__}: {ex}"

                with lock:
                    if emoted:
                        console.print(f"[bold magenta]{bot_uid} EMOTE SENT (cycle {cycle_num}) -> emote_id={EMOTE_ID}[/bold magenta]")
                    else:
                        console.print(f"[bold red]{bot_uid} EMOTE FAILED (cycle {cycle_num}) -> err={emote_err}[/bold red]")

            # ৬) বাকি সময়সহ মোট ১৫ সেকেন্ড গ্রুপে দাঁড়িয়ে থাকা
            last_ka = time.time()
            while time.time() < stay_end and not RF and not gen_stop_event.is_set():
                try:
                    sock_online.settimeout(0.5)
                    chunk = sock_online.recv(4096)
                    if chunk == b'':
                        remaining = stay_end - time.time()
                        if remaining > 0:
                            time.sleep(min(remaining, 0.5))
                        continue
                except socket.timeout:
                    pass
                except Exception:
                    time.sleep(0.5)

                if time.time() - last_ka >= 5.0:
                    try:
                        sock_online.sendall(send_keep_alive(key, iv))
                        last_ka = time.time()
                    except Exception:
                        pass

            # ৭) ১৫ সেকেন্ড পর (অথবা ৩ ঘণ্টার রিফ্রেশে) গ্রুপ থেকে বের হওয়া
            if sock_online:
                try:
                    sock_online.sendall(ExiT(key, iv))
                    time.sleep(0.05)
                except: pass

            try:
                if sock_online: sock_online.close()
            except: pass
            try:
                if sock_chat: sock_chat.close()
            except: pass

            with lock:
                console.print(
                    f"[yellow]{bot_uid} LEFT cycle {cycle_num} "
                    f"(s1={s1_sent}, msg1={msg1_sent}, msg2={msg2_sent}, emoted={emoted}, stayed {STAY_TIME}s)[/yellow]"
                )

            time.sleep(0.05)

        except Exception as e:
            with lock:
                console.print(f"[red]{bot_uid} cycle err: {type(e).__name__}[/red]")
            try:
                if sock_online: sock_online.close()
            except: pass
            try:
                if sock_chat: sock_chat.close()
            except: pass
            time.sleep(0.05)

    zahid_remove_bot(bot_uid)


# ================== Account loading ==================
def zahid_load_file(fp):
    accs = []
    try:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        u = parts[0].strip()
                        p = ':'.join(parts[1:]).strip()
                        if u and p:
                            accs.append((u, p))
    except:
        pass
    return accs


def zahid_load_all():
    all_ = []
    for region, fp in RAF.items():
        for u, p in zahid_load_file(fp):
            all_.append((u, p, region))
    random.shuffle(all_)
    return all_


# ================== Session Prep Helper ==================
def zahid_prepare_sessions(accs, use_saved=True):
    saved_tokens = zahid_load_saved_tokens(TOKEN_FILE) if use_saved else {}

    if use_saved and saved_tokens:
        console.print(f"[bold cyan]Found existing {TOKEN_FILE} ({len(saved_tokens)} saved tokens) — Testing saved tokens first...[/bold cyan]\n")
    else:
        console.print(f"[bold cyan]Building fresh tokens for {len(accs)} account(s) with {TOKEN_WORKERS} threads...[/bold cyan]\n")

    acc_queue = queue.Queue()
    for a in accs:
        acc_queue.put(a)

    stats = {'reused': 0, 'built': 0, 'failed': 0}
    stats_lock = threading.Lock()
    ready_sessions = []
    ready_lock = threading.Lock()

    def _prepare_worker():
        while not RF:
            try:
                uid, pwd, region = acc_queue.get_nowait()
            except queue.Empty:
                return

            try:
                uid_str = str(uid)
                if use_saved and uid_str in saved_tokens:
                    cand = saved_tokens[uid_str]
                    cand['password'] = pwd
                    if zahid_test_session_online(cand):
                        with ready_lock:
                            ready_sessions.append(cand)
                        with stats_lock:
                            stats['reused'] += 1
                        console.print(f"[green][REUSED] {uid_str} ({region}) token.json VALID -> bot={cand['bot_uid']}[/green]")
                        continue
                    else:
                        console.print(f"[yellow][EXPIRED] {uid_str} ({region}) saved token invalid — rebuilding...[/yellow]")

                if not pwd:
                    with stats_lock:
                        stats['failed'] += 1
                    console.print(f"[red]{uid_str} ({region}) NO PASSWORD to rebuild[/red]")
                    continue

                sess = zahid_build_session(uid_str, pwd, region)
                if sess:
                    zahid_upsert_single_token(sess)
                    with ready_lock:
                        ready_sessions.append(sess)
                    with stats_lock:
                        stats['built'] += 1
                    console.print(f"[green][NEW] {uid_str} ({region}) token SAVED -> bot={sess['bot_uid']}[/green]")
                else:
                    with stats_lock:
                        stats['failed'] += 1
                    console.print(f"[red]{uid_str} ({region}) FAILED[/red]")
            except Exception as e:
                with stats_lock:
                    stats['failed'] += 1
                console.print(f"[red]{uid} worker err: {type(e).__name__}: {e}[/red]")
            finally:
                acc_queue.task_done()

    workers = []
    for _ in range(TOKEN_WORKERS):
        t = threading.Thread(target=_prepare_worker, daemon=True)
        t.start()
        workers.append(t)

    for t in workers:
        t.join()

    console.print(f"\n[bold green]=== SESSION PREP DONE ===[/bold green]")
    console.print(f"  Reused from token.json : {stats['reused']}")
    console.print(f"  Newly Built & Saved    : {stats['built']}")
    console.print(f"  Failed                 : {stats['failed']}")
    return ready_sessions


# ================== MAIN (with 3-hour token refresh) ==================
def zahid_main():
    global RF
    first_run = True

    while not RF:
        accs = zahid_load_all()
        saved_tokens = zahid_load_saved_tokens(TOKEN_FILE) if first_run else {}

        if not accs and not saved_tokens:
            console.print("[red]No accounts found in accounts.txt or token.json[/red]")
            return

        if not accs and saved_tokens:
            accs = [(u, None, s.get('region', 'BD')) for u, s in saved_tokens.items()]

        console.print(f"[bold green]Total Accounts Loaded: {len(accs)}[/bold green]")

        ready_sessions = zahid_prepare_sessions(accs, use_saved=first_run)
        first_run = False

        if not ready_sessions:
            console.print("[red]No valid tokens available — retrying in 30s...[/red]")
            time.sleep(30)
            continue

        console.print(f"[bold cyan]Launching {len(ready_sessions)} bot(s) online together...[/bold cyan]\n")

        gen_stop_event = threading.Event()
        bot_threads = []
        launched = 0

        for sess in ready_sessions:
            try:
                t = threading.Thread(
                    target=zahid_run_session,
                    args=(sess, gen_stop_event),
                    daemon=True,
                )
                t.start()
                bot_threads.append(t)
                launched += 1
            except Exception as e:
                console.print(f"[red]launch err {sess.get('uid')}: {type(e).__name__}[/red]")

        console.print(f"[bold green]=== ALL {launched} BOT(S) NOW ONLINE (Auto token refresh every 3 hours) ===[/bold green]")
        console.print(f"[bold cyan]=== (Ctrl+C to stop) ===[/bold cyan]")

        # ৩ ঘণ্টা অপেক্ষা
        refresh_at = time.time() + TOKEN_REFRESH_INTERVAL
        while time.time() < refresh_at and not RF:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                console.print("[yellow]Stopped by user.[/yellow]")
                RF = True
                gen_stop_event.set()
                os._exit(0)

        if RF:
            break

        # ৩ ঘণ্টা পূর্ণ হলে পুরোনো সেশন থামিয়ে token.json ডিলিট ও নতুন করে তৈরি
        console.print(f"\n[bold yellow]=== 3 HOURS COMPLETED: Stopping old sessions & deleting {TOKEN_FILE} ===[/bold yellow]")
        gen_stop_event.set()
        for t in bot_threads:
            t.join(timeout=3.0)

        with connected_lock:
            connected_bots.clear()

        # পাসওয়ার্ডযুক্ত অ্যাকাউন্ট থাকলেই কেবল token.json ডিলিট করে নতুন বানাবে
        has_passwords = any(p for _, p, _ in zahid_load_all())
        if has_passwords:
            try:
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                    console.print(f"[yellow]Deleted old {TOKEN_FILE} — building brand new tokens...[/yellow]\n")
            except Exception as ex:
                console.print(f"[red]Could not delete {TOKEN_FILE}: {ex}[/red]")
        else:
            console.print("[yellow]accounts.txt has no passwords — keeping existing token.json[/yellow]")


if __name__ == "__main__":
    try:
        zahid_main()
    except KeyboardInterrupt:
        console.print("[yellow]Stopped by user.[/yellow]")
        os._exit(0)
    except Exception:
        traceback.print_exc()