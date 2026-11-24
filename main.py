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
RAF = {
    "BD": "accounts.txt",
    "IND": "accounts_ind.txt",
}
TOKEN_FILES = {
    "BD": "token.json",
    "IND": "token_ind.json",
}
ADMIN_UID = "622534362"

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

GRANT_URL = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

# ================== Timing ==================
STAY_TIME = 15.0               # সেকেন্ড: মোট ১৫ সেকেন্ড গ্রুপে থাকবে
CHAT_AUTH_WAIT   = 0.25
CHAT_JOIN_WAIT   = 0.25
CHAT_RETRY_DELAY = 0.15
SECOND_MSG_DELAY = 1.0         # ১ম মেসেজের ১ সেকেন্ড পর ২য় মেসেজ পাঠাবে
BUNDLE_AFTER_MSG_WAIT   = 0.20 # ২য় মেসেজের পর বান্ডিল চেঞ্জ করার বিরতি
EMOTE_AFTER_BUNDLE_WAIT = 0.30 # বান্ডিল চেঞ্জের পর ইমোট মারার বিরতি
EXIT_BEFORE_INV_WAIT = 0.35    # ExiT করার পর সোলো হতে ০.৩৫s অপেক্ষা
INV_AFTER_WAIT = 0.25          # ইনভাইট পাঠানোর পর বিরতি
JOIN_TIMEOUT = 2.5
JOIN_REFRESH = 0.5
CYCLE_RETRY_DELAY = 0.2
AUTH_RETRY_DELAY = 3.0
BOT_CRASH_RESTART_DELAY = 2.0

# ================== Invite Badge, Greeting & 10 Evo Emotes ==================
INVITE_BADGE_VALUE = 32768     # 32768 = আসল V-Badge (চাইলে 1048576 দিতে পারেন)

GREETING_1 = "FREE GLORY BOT"

GREETING_2 = (
    "[B][00BFFF]■ ARIYAN STORE ■\n"
    "[B][00BFFF]────────────────\n"
    "[B][FFD700] search telegram channel\n"
    "[B][00BFFF]└─[00FF00]JOIN CHANNEL \n"
    "[B][00BFFF]────────────────\n"
    "[B][FFD700]Fast join telegram\n"
    "[B][00BFFF]├─[00FF00]Telegram [FFFFFF]@Ariyan_world_A9x\n"
    "[B][00BFFF]└─[00FF00]Telegram [FFFFFF]https://t'me/Ariyan_world_A9x\n"
    "[B][00BFFF]────────────────"
)

# শুধু সেরা ১০টি Evo ইমোট ম্যাপ
BASE_EMOTE_MAP = {
    "ak_evo":     909000063,  # AK Evo
    "scar_evo":   909000068,  # SCAR Evo
    "mp40_evo":   909000075,  # MP40 Evo (Predatory Cobra)
    "mp40_2":     909040010,  # MP40 Evo (Chromasonic)
    "m1014_evo":  909000081,  # M1014 Evo
    "xm8_evo":    909000085,  # XM8 Evo
    "famas_evo":  909000090,  # Famas Evo
    "ump_evo":    909000098,  # UMP Evo
    "m1887_evo":  909035007,  # M1887 Evo
    "groza_evo":  909041005,  # Groza Evo
}

EMOTE_MAP = dict(BASE_EMOTE_MAP)
EMOTE_IDS = list(BASE_EMOTE_MAP.values())

# ১২টি বান্ডিল আইডি (প্রতিটি বট গ্রুপে ঢুকে মেসেজের পর আলাদা আলাদা বান্ডিল পরবে)
BUNDLE_IDS = [
    914000002,  # Rampage
    914000003,  # Cannibal
    914042001,  # Frostfire
    914051001,  # Dreamspace
    914053001,  # Special
]

_bundle_lock = threading.Lock()
_active_group_bundles = {}   # {str(target_uid): {bundle_id: count}}

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


def pick_unique_bundle(target_uid, prev_bundle=None):
    """একই গ্রুপে থাকা প্রত্যেক বটকে আলাদা আলাদা বান্ডিল দেয় এবং পরের গ্রুপে নতুন বান্ডিল নেয়"""
    key_uid = str(target_uid)
    with _bundle_lock:
        if len(_active_group_bundles) > 2000:
            _active_group_bundles.clear()
        used_counts = _active_group_bundles.setdefault(key_uid, {})

        # প্রথম পছন্দ: এই গ্রুপে এখন কেউ পরেনি এবং এই বট আগের গ্রুপেও পরেনি
        candidates = [b for b in BUNDLE_IDS if b not in used_counts and b != prev_bundle]
        if not candidates:
            # দ্বিতীয় পছন্দ: এই গ্রুপে এখন কেউ পরেনি
            candidates = [b for b in BUNDLE_IDS if b not in used_counts]
        if not candidates:
            # তৃতীয় পছন্দ: গ্রুপে ১২+ বট থাকলে আগেরটা বাদে যেকোনোটা
            candidates = [b for b in BUNDLE_IDS if b != prev_bundle] or list(BUNDLE_IDS)

        chosen = random.choice(candidates)
        used_counts[chosen] = used_counts.get(chosen, 0) + 1

    mode = random.choice([1, 2]) if chosen in (914047001, 914051001) else 1
    return chosen, mode


def release_group_bundle(target_uid, bundle_id):
    """বট গ্রুপ থেকে লিভ করলে ওই গ্রুপের বান্ডিল ট্র্যাকিং পরিষ্কার করে"""
    if not target_uid or not bundle_id:
        return
    key_uid = str(target_uid)
    with _bundle_lock:
        used_counts = _active_group_bundles.get(key_uid)
        if not used_counts:
            return
        cnt = used_counts.get(bundle_id, 0)
        if cnt <= 1:
            used_counts.pop(bundle_id, None)
        else:
            used_counts[bundle_id] = cnt - 1
        if not used_counts:
            _active_group_bundles.pop(key_uid, None)


def region_pkt(pkt, region):
    """xP.py এর 0519 প্যাকেটকে রিজিয়ন অনুযায়ী 0514 (IND), 0519 (BD), বা 0515 (Others) করে"""
    if pkt and len(pkt) >= 2 and pkt[:2] == b'\x05\x19':
        reg_l = str(region).lower()
        if reg_l == "ind":
            return b'\x05\x14' + pkt[2:]
        elif reg_l != "bd":
            return b'\x05\x15' + pkt[2:]
    return pkt


def pop_tcp_frames(buf):
    """TCP বাফার থেকে একসাথে আসা সবগুলো প্যাকেট আলাদা করে বের করে"""
    frames = []
    while len(buf) >= 5:
        pkt_type = buf[0]
        pkt_len = struct.unpack(">I", buf[1:5])[0]
        if pkt_len <= 0 or pkt_len > 200000:
            del buf[0]
            continue
        if len(buf) < 5 + pkt_len:
            break
        payload = bytes(buf[5 : 5 + pkt_len])
        del buf[: 5 + pkt_len]
        frames.append((pkt_type, payload))
    return frames


# ================== Proto helpers ==================
def _extract_raw_pb(data: bytes) -> dict:
    """কাজ করা মেজর-লগইন ও গেট-লগইন প্রোটোবাফ পার্সার"""
    res, off, n = {}, 0, len(data)
    while off < n:
        hdr, sh = 0, 0
        while off < n:
            b = data[off]; off += 1; hdr |= (b & 0x7F) << sh
            if not (b & 0x80): break
            sh += 7
        fn, wt = hdr >> 3, hdr & 0x7
        if wt == 0:
            v, sh = 0, 0
            while off < n:
                b = data[off]; off += 1; v |= (b & 0x7F) << sh
                if not (b & 0x80): break
                sh += 7
            res[fn] = v
        elif wt == 2:
            ln, sh = 0, 0
            while off < n:
                b = data[off]; off += 1; ln |= (b & 0x7F) << sh
                if not (b & 0x80): break
                sh += 7
            if off + ln > n: break
            res[fn] = data[off:off + ln]; off += ln
        elif wt == 1:
            off += 8
        elif wt == 5:
            off += 4
        else:
            break
    return res


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
    enc = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(pk_bytes, 16))
    length_hex = len(enc).to_bytes(4, "big").hex()
    return bytes.fromhex(header_hex + length_hex) + enc


def xc4_auth_chat(owner_uid, chat_code, key, iv):
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


def xc4_bundle_pkt(bundle_id, key, iv, region="BD", mode=1):
    fields = {
        1: 88,
        2: {
            1: {
                1: int(bundle_id),
                2: int(mode),
            },
            2: 2,
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


def xc4_emote_pkt(bot_uid, emote_id, key, iv, region="BD"):
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


def xc4_perfect_invite_pkt(bot_uid, target_uid, key, iv, region="BD", badge_value=INVITE_BADGE_VALUE):
    """xP.py (yasser_SendInv OB55) অনুযায়ী ১০০% পারফেক্ট V-Badge / Join Request প্যাকেট"""
    reg_up = str(region).upper()
    b_uid = int(bot_uid)
    t_uid = int(target_uid)
    fields = {
        1: 33,
        2: {
            1: t_uid,
            2: reg_up,
            3: 1,
            4: 1,
            6: "[C][B][FF0000]ARIYAN",
            7: 330,
            8: 1000,
            9: 100,
            10: reg_up,
            12: 1,
            13: t_uid,
            16: 1,
            17: {2: 159, 4: "y[WW", 6: 11, 8: "1.118.1", 9: 3, 10: 1},
            18: 306,
            19: 18,
            24: random.choice(AVATAR_LIST),
            26: {},
            27: {1: 11, 2: b_uid, 3: 999},
            28: {},
            31: {1: 1, 2: int(badge_value)},
            32: int(badge_value),
            34: {
                1: b_uid,
                2: 8,
                3: b"\x10\x15\x08\x0a\x0b\x13\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06",
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


# ================== Version ==================
def zahid_update_version():
    global login_url, ob, verr, host
    try:
        from google_play_scraper import app as gp
        d = gp("com.dts.freefireth", lang="hi", country="id")
        version = d["version"]
    except Exception:
        version = "1.132.9"
    try:
        x = requests.get(
            "https://version.ggwhitehawk.com/live/ver.php"
            f"?version={version}&lang=en&device=android&channel=android"
            f"&appstore=googleplay&region=BD&whitelist_version=1.3.0"
            f"&whitelist_sp_version=1.0.0",
            timeout=10,
        ).json()
        login_url = x["server_url"]
        ob = x.get("latest_release_version") or "OB55"
        verr = x.get("remote_version") or "1.134.14"
        host = login_url.split("https://", 1)[1].split("/", 1)[0]
    except Exception:
        login_url = LOGIN_SERVERS[0]
        ob = "OB55"
        verr = "1.134.14"
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

    reg = str(region or "BD").upper()
    c_ver = verr or "1.134.14"
    P = {}

    if reg in ("IND", "IN"):
        P[3]=server_time_str; P[4]="free fire"; P[5]=1; P[7]=c_ver
        P[8]="Android OS 14 / API-34 (UP1A.231005.007/E156BXXS6AYD4)"
        P[9]="Handheld"; P[10]="airtel"; P[11]="CarrierDataNetwork"
        P[12]=2340; P[13]=1080; P[14]="295"
        P[15]="ARM64 FP ASIMD AES | 2200 | 8"; P[16]=5586
        P[17]="Mali-G57 MC2"; P[18]="OpenGL ES 3.2 v1.r38p1"
        P[19]="Google|f4d8aefb-7549-4778-a92b-2ed885bf9ec4"
        P[20]="27.61.46.111"; P[21]="en"; P[22]=str(open_id); P[23]="4"
        P[24]="Handheld"; P[25]="samsung SM-A155F"; P[26]="IND"
        P[29]=str(access_token); P[30]=1; P[41]="airtel"; P[42]="4G"
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
    else:
        P[3]=server_time_str; P[4]="free fire"; P[5]=1; P[7]=c_ver
        P[8]="Android OS 14 / API-34 (UP1A.231005.007/V816.0.15.0.UNQMIXM)"
        P[9]="Handheld"; P[10]="Grameenphone"; P[11]="CarrierDataNetwork"
        P[12]=1666; P[13]=750; P[14]="352"
        P[15]="ARM64 FP ASIMD AES | 2400 | 8"; P[16]=5563
        P[17]="Mali-G57 MC2"
        P[18]="OpenGL ES 3.2 v1.r32p1-01eac0.0a0b917d9265b4c01be9925306306139"
        P[19]="Google|9cc73f7a-91f6-40f6-87ec-5b67e597eb8c"
        P[20]="59.152.5.188"; P[21]="en"; P[22]=str(open_id); P[23]="8"
        P[24]="Handheld"; P[25]="Xiaomi 2312DRAABI"; P[26]=reg
        P[29]=str(access_token); P[30]=1; P[41]="Grameenphone"; P[42]="Cellular"
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


# ================== ২ সার্ভারের সঠিক Auth Token (BD: 7319/6d19 | IND: 7314/6d14) ==================
def zahid_build_auth_token(uid, token, ts, key, iv, mode="online", region="BD"):
    reg = str(region or "BD").upper()
    if mode == "chat":
        pfx = "6d19" if reg == "BD" else ("6d14" if reg == "IND" else "6d15")
        ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(token.encode("utf-8"), AES.block_size))
        return (
            bytes.fromhex(pfx)
            + int(uid).to_bytes(8, "big")
            + int(ts).to_bytes(4, "big")
            + len(ct).to_bytes(4, "big")
            + ct
        ).hex()
    else:
        pfx = "7319" if reg == "BD" else ("7314" if reg == "IND" else "7315")
        ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(token.encode("utf-8"), AES.block_size))
        return (
            bytes.fromhex(pfx)
            + int(uid).to_bytes(8, "big")
            + int(ts).to_bytes(4, "big")
            + b"\x00\x00\x00\x00"
            + len(ct).to_bytes(4, "big")
            + ct
        ).hex()


def zahid_decrypt_major_login(raw):
    class A: pass
    if not raw or len(raw) <= 64:
        return None
    offs = ([64, 0] if raw[0] != 0x0a else [0, 64]) + [48, 32, 80, 16, 128, 8, 96]
    for off in offs:
        if off >= len(raw):
            continue
        rf = _extract_raw_pb(raw[off:])
        k_b = rf.get(22) or rf.get(24) or rf.get(6)
        v_b = rf.get(23) or rf.get(25) or rf.get(7)
        if 8 in rf and isinstance(k_b, bytes) and len(k_b) == 16 and isinstance(v_b, bytes) and len(v_b) == 16:
            tok = rf[8].decode("utf-8", "ignore")
            if not tok.startswith("eyJ"):
                continue
            au = rf.get(1)
            if not isinstance(au, int) or au < 1000000:
                continue
            a = A()
            a.token = tok
            a.account_uid = au
            a.region = rf.get(2, b"BD").decode("utf-8", "ignore")
            a.url = rf.get(10, b"").decode("utf-8", "ignore")
            a.timestamp = rf.get(21, int(time.time()))
            a.key = k_b
            a.iv = v_b
            return a
    return None


def zahid_decrypt_login_data(raw):
    class P: pass
    if not raw:
        return None
    for off in [0, 64, 48, 32, 80, 16, 128, 8, 96]:
        if off >= len(raw):
            continue
        try:
            parsed = Parser().parse(raw[off:])
            d = {}
            for res in parsed:
                if res.wire_type in ("varint", "string", "bytes"):
                    d[res.field] = res.data
            if 14 in d and isinstance(d[14], str) and ":" in d[14] and 32 in d and isinstance(d[32], str) and ":" in d[32]:
                p = P()
                p.Online_IP_Port = d[14]
                p.AccountIP_Port = d[32]
                return p
        except Exception:
            pass
        rf = _extract_raw_pb(raw[off:])
        if 14 in rf and isinstance(rf[14], bytes) and 32 in rf and isinstance(rf[32], bytes):
            op = rf[14].decode("utf-8", "ignore")
            cp_ = rf[32].decode("utf-8", "ignore")
            if ":" in op and ":" in cp_:
                p = P()
                p.Online_IP_Port = op
                p.AccountIP_Port = cp_
                return p
    return None


api_sem = threading.Semaphore(10)


def zahid_guest_access(uid, pw):
    with api_sem:
        headers = {
            "Host": "100067.connect.garena.com",
            "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 13;en;IN;)",
            "Content-Type": "application/json",
        }
        data = {
            "client_id": 100067,
            "client_secret": HEX_KEY,
            "client_type": 2,
            "password": str(pw).strip(),
            "response_type": "token",
            "uid": int(str(uid).strip()),
        }
        try:
            r = requests.post(GRANT_URL, json=data, headers=headers, timeout=20, verify=False)
            if r.status_code != 200:
                return None, None
            result = r.json().get("data", {})
            oid = result.get("open_id")
            atk = result.get("access_token")
            if not oid or not atk:
                return None, None
            return oid, atk
        except Exception:
            return None, None


def zahid_major_login(payload):
    global login_url
    ut = [login_url] + [s for s in LOGIN_SERVERS if s != login_url]
    seen = set()
    ut = [x for x in ut if not (x in seen or seen.add(x))]
    req_h = {
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": str(int(time.time())),
        "Authorization": "Bearer ",
        "X-GA": "v1 1",
        "ReleaseVersion": str(ob or "OB55"),
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
    }
    for base in ut:
        try:
            u = f"{base.rstrip('/')}/MajorLogin"
            r = requests.post(u, data=payload, headers=req_h, timeout=20, verify=False)
            if r.status_code in (200, 201) and len(r.content) > 64:
                login_url = base
                return r.content
        except Exception:
            continue
    return None


def zahid_get_login_data(url, payload, token):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    headers = {
        "Accept": "*/*",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": str(ob or "OB55"),
        "User-Agent": "UnityPlayer/2018.4.12f1",
        "X-GA": "v1 1",
        "X-GA-SV": str(int(time.time())),
        "X-Unity-Version": "2018.4.12f1",
    }
    try:
        u = f"{url.rstrip('/')}/GetLoginData"
        r = requests.post(u, data=payload, headers=headers, timeout=20, verify=False)
        if r.status_code in (200, 201) and r.content:
            return r.content
    except Exception:
        pass
    return None


# ================== Token.json / Token_ind.json I/O & Validation ==================
def get_token_file(region):
    return TOKEN_FILES.get(str(region).upper(), "token.json")


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


def zahid_load_saved_tokens(region):
    path = get_token_file(region)
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


def zahid_upsert_single_token(sess):
    path = get_token_file(sess.get('region', 'BD'))
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
    reg = str(sess.get('region', 'BD')).upper()
    expected_pfx = "7319" if reg == "BD" else ("7314" if reg == "IND" else "7315")
    if not str(sess.get('auth_online', '')).startswith(expected_pfx):
        return False
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
        s.sendall(region_pkt(send_keep_alive(sess['key'], sess['iv']), reg))
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
    reg_hint = str(region or "BD").upper()
    for attempt in range(TOKEN_MAX_RETRY):
        try:
            oid, atk = zahid_guest_access(uid, password)
            if not atk or not oid:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            pyl = zahid_build_login_payload(oid, atk, region=reg_hint)
            resp = zahid_major_login(pyl)
            if not resp:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            ad = zahid_decrypt_major_login(resp)
            if not ad:
                time.sleep(TOKEN_RETRY_DELAY)
                continue

            real_reg = (ad.region or reg_hint).upper()
            target_url = ad.url or (
                "https://client.ind.freefiremobile.com" if real_reg == "IND"
                else "https://clientbp.ppmainecoonghj.com"
            )
            ld = zahid_get_login_data(target_url, pyl, ad.token)
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

            ac = zahid_build_auth_token(int(ad.account_uid), ad.token, int(ad.timestamp), ad.key, ad.iv, mode="chat", region=real_reg)
            ao = zahid_build_auth_token(int(ad.account_uid), ad.token, int(ad.timestamp), ad.key, ad.iv, mode="online", region=real_reg)

            return {
                'uid': str(uid),
                'password': password,
                'region': real_reg,
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
                console.print(f"[dim red][{reg_hint}] {uid} err:{type(e).__name__}[/dim red]")
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
            raise ConnectionError("chat_closed")
    except socket.timeout:
        pass


# ================== PHASE 2: Persistent Online Session ==================
def _open_persistent_online(ip, port, auth_online, key, iv, region):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 524288)
    s.settimeout(4.0)
    s.connect((ip, int(port)))
    s.sendall(bytes.fromhex(auth_online))
    time.sleep(0.15)
    s.sendall(region_pkt(send_keep_alive(key, iv), region))
    return s


def zahid_run_session(sess, gen_stop_event):
    bot_uid = sess['bot_uid']
    region = sess['region']
    auth = sess['auth']
    auth_online = sess['auth_online']
    ip = sess['ip']; port = sess['port']
    ip2 = sess['ip2']; port2 = sess['port2']
    key = sess['key']; iv = sess['iv']
    tag = f"{region}|{bot_uid}"

    zahid_add_bot(bot_uid, str(sess['uid']), region)

    sock_online = None
    rx_buf = bytearray()
    cycle_num = 0
    consecutive_join_fails = 0
    last_bundle_id = None

    try:
        while not RF and not gen_stop_event.is_set():
            # ০) পারসিস্টেন্ট অনলাইন সকেট না থাকলে কানেক্ট করে নেবে (BD=7319, IND=7314)
            if sock_online is None:
                try:
                    sock_online = _open_persistent_online(ip, port, auth_online, key, iv, region)
                    rx_buf.clear()
                    with lock:
                        console.print(f"[green][{tag}] ON ({ip}:{port})[/green]")
                except Exception:
                    sock_online = None
                    consecutive_join_fails += 1
                    if consecutive_join_fails >= 3 and sess.get('password'):
                        with lock:
                            console.print(f"[yellow][{tag}] token expired, rebuilding...[/yellow]")
                        new_sess = zahid_build_session(sess['uid'], sess['password'], region)
                        if new_sess:
                            zahid_upsert_single_token(new_sess)
                            sess = new_sess
                            bot_uid = sess['bot_uid']
                            region = sess['region']
                            tag = f"{region}|{bot_uid}"
                            auth = sess['auth']
                            auth_online = sess['auth_online']
                            ip = sess['ip']; port = sess['port']
                            ip2 = sess['ip2']; port2 = sess['port2']
                            key = sess['key']; iv = sess['iv']
                            consecutive_join_fails = 0
                    time.sleep(1.5)
                    continue

            cycle_num += 1
            sock_chat = None
            target_uid = None
            squad_code = None
            chat_code = None
            chosen_bundle = None

            try:
                # ১) একই পারসিস্টেন্ট sock_online দিয়ে গ্রুপ খোঁজা (BD=0519, IND=0514)
                rx_buf.clear()
                deadline = time.time() + JOIN_TIMEOUT
                last_send = 0
                last_ka = time.time()

                while time.time() < deadline and not RF and not gen_stop_event.is_set():
                    if time.time() - last_send > JOIN_REFRESH:
                        try:
                            sock_online.sendall(region_pkt(Join_Sq(key, iv), region))
                            last_send = time.time()
                        except Exception:
                            try: sock_online.close()
                            except: pass
                            sock_online = None
                            break

                    if time.time() - last_ka >= 10.0:
                        try:
                            sock_online.sendall(region_pkt(send_keep_alive(key, iv), region))
                            last_ka = time.time()
                        except Exception:
                            try: sock_online.close()
                            except: pass
                            sock_online = None
                            break

                    try:
                        sock_online.settimeout(0.15)
                        data = sock_online.recv(65536)
                        if not data:
                            try: sock_online.close()
                            except: pass
                            sock_online = None
                            break
                        rx_buf.extend(data)
                        for ptype, payload in pop_tcp_frames(rx_buf):
                            if ptype == 0x05 and len(payload) > 45:
                                try:
                                    js = DeCode_PackEt(payload.hex())
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
                                except Exception:
                                    pass
                        if target_uid:
                            break
                    except socket.timeout:
                        continue
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        try: sock_online.close()
                        except: pass
                        sock_online = None
                        break

                if RF or gen_stop_event.is_set():
                    break

                if not sock_online or not target_uid:
                    time.sleep(CYCLE_RETRY_DELAY)
                    continue

                consecutive_join_fails = 0
                stay_end = time.time() + STAY_TIME

                with lock:
                    console.print(f"[cyan][{tag}] C{cycle_num} JOIN->{target_uid}[/cyan]")

                # ২) ১ম মেসেজ পাঠানো (GREETING_1)
                msg1_sent = False
                msg1_err = ""
                msg1_text = f"[c][b][{ArA_CoLor()}]{GREETING_1}"

                for _ in range(3):
                    if RF or gen_stop_event.is_set(): break
                    try:
                        sock_chat = _connect_and_auth_chat(ip2, port2, auth, target_uid, chat_code, key, iv)
                        pkt1 = xc4_send_squad_msg(msg1_text, target_uid, key, iv, region=region)
                        _send_chat_and_check(sock_chat, pkt1)
                        msg1_sent = True
                        msg1_err = ""
                        break
                    except Exception as ex:
                        msg1_err = type(ex).__name__
                        try:
                            if sock_chat: sock_chat.close()
                        except: pass
                        sock_chat = None
                        time.sleep(CHAT_RETRY_DELAY)

                try:
                    if sock_chat: sock_chat.close()
                except: pass
                sock_chat = None

                # ৩) ১ সেকেন্ড বিরতি দিয়ে ২য় মেসেজ বক্স পাঠানো (GREETING_2)
                msg2_sent = False
                msg2_err = ""
                if not RF and not gen_stop_event.is_set():
                    time.sleep(SECOND_MSG_DELAY)
                    for _ in range(3):
                        if RF or gen_stop_event.is_set(): break
                        try:
                            sock_chat = _connect_and_auth_chat(ip2, port2, auth, target_uid, chat_code, key, iv)
                            pkt2 = xc4_send_squad_msg(GREETING_2, target_uid, key, iv, region=region)
                            _send_chat_and_check(sock_chat, pkt2)
                            msg2_sent = True
                            msg2_err = ""
                            break
                        except Exception as ex:
                            msg2_err = type(ex).__name__
                            try:
                                if sock_chat: sock_chat.close()
                            except: pass
                            sock_chat = None
                            time.sleep(CHAT_RETRY_DELAY)

                try:
                    if sock_chat: sock_chat.close()
                except: pass
                sock_chat = None

                # ৪) মেসেজগুলোর পর ইমোট দেওয়ার আগে একবার বান্ডিল চেঞ্জ করা (প্রত্যেক বট আলাদা আলাদা)
                bundled = False
                chosen_bundle, bundle_mode = pick_unique_bundle(target_uid, prev_bundle=last_bundle_id)
                if not RF and not gen_stop_event.is_set() and chosen_bundle and sock_online:
                    time.sleep(BUNDLE_AFTER_MSG_WAIT)
                    try:
                        bundle_pkt = xc4_bundle_pkt(
                            int(chosen_bundle), key, iv, region=region, mode=bundle_mode
                        )
                        sock_online.sendall(bundle_pkt)
                        bundled = True
                        last_bundle_id = chosen_bundle
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        bundled = False
                        try: sock_online.close()
                        except: pass
                        sock_online = None
                    except Exception:
                        bundled = False

                # ৫) বান্ডিল চেঞ্জের পর ১০টি Evo ইমোট থেকে র‍্যান্ডম ইমোট মারা
                emoted = False
                chosen_emote = random.choice(EMOTE_IDS) if EMOTE_IDS else 0
                if not RF and not gen_stop_event.is_set() and chosen_emote and sock_online:
                    time.sleep(EMOTE_AFTER_BUNDLE_WAIT)
                    try:
                        emote_pkt = xc4_emote_pkt(bot_uid, int(chosen_emote), key, iv, region=region)
                        sock_online.sendall(emote_pkt)
                        emoted = True
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        emoted = False
                        try: sock_online.close()
                        except: pass
                        sock_online = None
                    except Exception:
                        emoted = False

                with lock:
                    m1_ic = "✔" if msg1_sent else f"✘({msg1_err})"
                    m2_ic = "✔" if msg2_sent else f"✘({msg2_err})"
                    b_ic = f"{chosen_bundle}(✔)" if bundled else f"{chosen_bundle}(✘)"
                    em_ic = f"{chosen_emote}(✔)" if emoted else f"{chosen_emote}(✘)"
                    col = "green" if (msg1_sent and msg2_sent) else "red"
                    console.print(f"[{col}][{tag}] C{cycle_num} M1:{m1_ic} M2:{m2_ic} B:{b_ic} E:{em_ic}[/{col}]")

                # ৬) বাকি সময়সহ মোট ১৫ সেকেন্ড গ্রুপে দাঁড়িয়ে থাকা (এই সময়ে আর বান্ডিল চেঞ্জ হবে না)
                while time.time() < stay_end and not RF and not gen_stop_event.is_set():
                    if not sock_online:
                        break
                    try:
                        sock_online.settimeout(0.5)
                        chunk = sock_online.recv(4096)
                        if chunk == b'':
                            try: sock_online.close()
                            except: pass
                            sock_online = None
                            break
                        rx_buf.extend(chunk)
                        pop_tcp_frames(rx_buf)
                    except socket.timeout:
                        pass
                    except Exception:
                        try: sock_online.close()
                        except: pass
                        sock_online = None
                        break

                    if sock_online and time.time() - last_ka >= 5.0:
                        try:
                            sock_online.sendall(region_pkt(send_keep_alive(key, iv), region))
                            last_ka = time.time()
                        except Exception:
                            try: sock_online.close()
                            except: pass
                            sock_online = None
                            break

                # ৭) ১৫ সেকেন্ড পর ExiT (অনলাইন রেখেই সোলো হওয়া) -> একবার পারফেক্ট ইনভাইট পাঠানো
                inv_sent = False
                if sock_online and not RF and not gen_stop_event.is_set():
                    try:
                        sock_online.sendall(region_pkt(ExiT(key, iv), region))
                        drain_end = time.time() + EXIT_BEFORE_INV_WAIT
                        while time.time() < drain_end:
                            try:
                                sock_online.settimeout(0.1)
                                d_left = sock_online.recv(4096)
                                if not d_left:
                                    try: sock_online.close()
                                    except: pass
                                    sock_online = None
                                    break
                                rx_buf.extend(d_left)
                                pop_tcp_frames(rx_buf)
                            except socket.timeout:
                                continue
                            except Exception:
                                break

                        if sock_online:
                            inv_pkt = xc4_perfect_invite_pkt(
                                bot_uid, target_uid, key, iv,
                                region=region, badge_value=INVITE_BADGE_VALUE,
                            )
                            sock_online.sendall(inv_pkt)
                            time.sleep(INV_AFTER_WAIT)
                            try:
                                sock_online.settimeout(0.15)
                                d_inv = sock_online.recv(4096)
                                if d_inv:
                                    rx_buf.extend(d_inv)
                                    pop_tcp_frames(rx_buf)
                            except socket.timeout:
                                pass
                            inv_sent = True
                    except Exception:
                        inv_sent = False

                with lock:
                    inv_ic = "✔" if inv_sent else "✘"
                    console.print(f"[yellow][{tag}] C{cycle_num} LEFT ({STAY_TIME:.0f}s) | INV:{inv_ic}[/yellow]")

                time.sleep(0.1)

            except Exception as e:
                with lock:
                    console.print(f"[red][{tag}] err:{type(e).__name__}[/red]")
                try:
                    if sock_chat: sock_chat.close()
                except: pass
                try:
                    if sock_online: sock_online.close()
                except: pass
                sock_online = None
                time.sleep(0.5)
            finally:
                # লিভ নেওয়ার সাথে সাথে গ্রুপের বান্ডিল স্টেট রিসেট করা যাতে নতুন গ্রুপে আবার নতুন বান্ডিল নেয়
                if target_uid and chosen_bundle:
                    release_group_bundle(target_uid, chosen_bundle)
    finally:
        try:
            if sock_online:
                sock_online.sendall(region_pkt(ExiT(key, iv), region))
                sock_online.close()
        except Exception:
            pass
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


# ================== Session Prep Helper (BD -> token.json, IND -> token_ind.json) ==================
def zahid_prepare_sessions(accs, use_saved=True):
    saved_by_region = {
        reg: (zahid_load_saved_tokens(reg) if use_saved else {})
        for reg in RAF.keys()
    }

    if use_saved:
        info = " | ".join(f"{r}:{len(saved_by_region[r])}" for r in RAF)
        console.print(f"[cyan]Saved tokens -> {info}[/cyan]")
    else:
        console.print(f"[cyan]Rebuilding {len(accs)} tokens...[/cyan]")

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
                reg_saved = saved_by_region.get(region, {})

                if use_saved and uid_str in reg_saved:
                    cand = reg_saved[uid_str]
                    cand['password'] = pwd
                    if zahid_test_session_online(cand):
                        with ready_lock:
                            ready_sessions.append(cand)
                        with stats_lock:
                            stats['reused'] += 1
                        console.print(f"[green][{region}] {uid_str} REUSED -> {cand['bot_uid']}[/green]")
                        continue
                    else:
                        console.print(f"[yellow][{region}] {uid_str} EXPIRED -> rebuild[/yellow]")

                if not pwd:
                    with stats_lock:
                        stats['failed'] += 1
                    console.print(f"[red][{region}] {uid_str} NO_PASS[/red]")
                    continue

                sess = zahid_build_session(uid_str, pwd, region)
                if sess:
                    zahid_upsert_single_token(sess)
                    with ready_lock:
                        ready_sessions.append(sess)
                    with stats_lock:
                        stats['built'] += 1
                    console.print(f"[green][{region}] {uid_str} NEW -> {sess['bot_uid']}[/green]")
                else:
                    with stats_lock:
                        stats['failed'] += 1
                    console.print(f"[red][{region}] {uid_str} FAIL[/red]")
            except Exception as e:
                with stats_lock:
                    stats['failed'] += 1
                console.print(f"[red][{region}] {uid} err:{type(e).__name__}[/red]")
            finally:
                acc_queue.task_done()

    workers = []
    for _ in range(TOKEN_WORKERS):
        t = threading.Thread(target=_prepare_worker, daemon=True)
        t.start()
        workers.append(t)

    for t in workers:
        t.join()

    console.print(f"[green]Prep Done -> Reused:{stats['reused']} | New:{stats['built']} | Fail:{stats['failed']}[/green]")
    return ready_sessions


# ================== MAIN (with 3-hour token refresh) ==================
def zahid_main():
    global RF
    first_run = True

    while not RF:
        accs = zahid_load_all()
        if not accs:
            for reg in RAF.keys():
                for u, s in zahid_load_saved_tokens(reg).items():
                    accs.append((u, None, s.get('region', reg)))

        if not accs:
            console.print("[red]No accounts in accounts.txt / accounts_ind.txt[/red]")
            return

        bd_cnt = sum(1 for _, _, r in accs if r == "BD")
        ind_cnt = sum(1 for _, _, r in accs if r == "IND")
        console.print(f"[green]Loaded -> BD:{bd_cnt} | IND:{ind_cnt} | Bundles:{len(BUNDLE_IDS)} | Emotes:{len(EMOTE_IDS)}[/green]")

        ready_sessions = zahid_prepare_sessions(accs, use_saved=first_run)
        first_run = False

        if not ready_sessions:
            console.print("[red]No valid tokens — retry 30s[/red]")
            time.sleep(30)
            continue

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

        console.print(f"[bold green]ONLINE: {launched} bots (BD+IND | 3h Refresh)[/bold green]")

        refresh_at = time.time() + TOKEN_REFRESH_INTERVAL
        while time.time() < refresh_at and not RF:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                console.print("[yellow]Stopped.[/yellow]")
                RF = True
                gen_stop_event.set()
                os._exit(0)

        if RF:
            break

        console.print(f"\n[yellow]3h Refresh: resetting token files...[/yellow]")
        gen_stop_event.set()
        for t in bot_threads:
            t.join(timeout=3.0)

        with connected_lock:
            connected_bots.clear()
        with _bundle_lock:
            _active_group_bundles.clear()

        for reg, acc_fp in RAF.items():
            tok_fp = get_token_file(reg)
            has_pw = bool(zahid_load_file(acc_fp))
            if has_pw and os.path.exists(tok_fp):
                try:
                    os.remove(tok_fp)
                    console.print(f"[yellow][{reg}] Deleted {tok_fp}[/yellow]")
                except Exception as ex:
                    console.print(f"[red][{reg}] Del err {tok_fp}: {ex}[/red]")


if __name__ == "__main__":
    try:
        zahid_main()
    except KeyboardInterrupt:
        console.print("[yellow]Stopped.[/yellow]")
        os._exit(0)
    except Exception:
        traceback.print_exc()