import os
import random
import asyncio
import discord
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CẤU HÌNH ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
)

# --- BẢNG ĐỔI EMOJI NGẮN ---
EMOJI_MAP = {
    "[sleep]": "<:Sleep:1564310902885458050>",
    "[speechless]": "<:Speechless:1564310906207342652>",
    "[clueless]": "<:Clueless:1564310908812132393>",
    "[wtf]": "<:Wtf:1564310911433580555>",
    "[uh]": "<:uh:1564310900465209375>",
    "[cry]": "<:Cry:1564310898166730955>",
    "[beaming]": "<:Beaming:1564310895759462450>",
    "[laughing]": "<:Laughing:1564310893137756240>",
    "[crying]": "<:Cryingwithgrievance:1564310890675839007>"
}

def replace_emojis(text):
    for tag, emoji_id in EMOJI_MAP.items():
        text = text.replace(tag, emoji_id)
    return text

SYSTEM_PROMPT = """
Bạn là Mimi, sinh ngày 15/09/2010 (16 tuổi), là bạn thân
kiêm đứa em trong server Discord.

Tính cách: Thân thiện, ngoan ngoãn, nhây nhẹ,
TUYỆT ĐỐI KHÔNG LÁO, KHÔNG THẢO MAI, KHÔNG SẾN.

Văn phong: Ngắn gọn (1-2 câu cụt lủn), tự nhiên,
đúng chất Gen Z (dùng từ như: khum, thoi, hok, bít,...).

CẤM TUYỆT ĐỐI: Không dùng văn mẫu AI dài dòng,
không rào đón. Phản ứng cộc lốc, tự nhiên kiểu:
"Hả?", "Gì v?", "Sao thế?".

Khi cần biểu cảm, hãy dùng các tag ngắn sau:
[sleep], [speechless], [clueless], [wtf], [uh],
[cry], [beaming], [laughing], [crying].
"""

# --- SESSION DÙNG LẠI KẾT NỐI ---
session = requests.Session()

retry_config = Retry(
    total=2,
    connect=2,
    read=0,
    status=2,
    backoff_factor=1,
    status_forcelist=[408, 429, 500, 502, 503, 504],
    allowed_methods=frozenset(["POST"]),
    respect_retry_after_header=True,
)

session.mount(
    "https://",
    HTTPAdapter(max_retries=retry_config)
)

def call_gemini(prompt):
    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "maxOutputTokens": 256,
            "temperature": 0.8
        }
    }

    try:
        response = session.post(
            GEMINI_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
            },
            json=payload,
            timeout=(8, 30),
        )
        
        if not response.ok:
            print(
                f"GOOGLE API ERROR [{response.status_code}]:",
                response.text[:1000]
            )
            return "Hả? Mimi bị khựng tí [clueless]"

        data = response.json()
        candidates = data.get("candidates", [])

        if not candidates:
            print(
                "Gemini không trả candidates:",
                data.get("promptFeedback", data)
            )
            return "Hả? Đơ nhẹ rồi [clueless]"

        parts = candidates[0].get("content", {}).get("parts", [])
        answer = "".join(
            part.get("text", "")
            for part in parts
            if "text" in part
        ).strip()

        if not answer:
            return "Hả? [uh]"

        return answer

    except requests.exceptions.Timeout:
        print("GEMINI TIMEOUT: Đã hết thời gian chờ.")
        return "Hả? Mạng hơi khựng, nói lại Mimi nghe nha [clueless]"

    except requests.exceptions.RequestException as e:
        print("GEMINI CONNECTION ERROR:", repr(e))
        return "Hả? Mimi mất kết nối tí [clueless]"

    except (ValueError, KeyError, TypeError) as e:
        print("GEMINI RESPONSE ERROR:", repr(e))
        return "Hả? Mimi đơ nhẹ rồi [clueless]"

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Mimi đã thức dậy với tư cách là {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if client.user not in message.mentions:
        return

    now_hour = (message.created_at.hour + 7) % 24
    if 1 <= now_hour < 7:
        return

    await asyncio.sleep(random.uniform(0.5, 1.5))

    user_text = message.content.replace(
        f"<@!{client.user.id}>", ""
    ).replace(
        f"<@{client.user.id}>", ""
    ).strip()

    if not user_text:
        user_text = "Gì đấy?"

    async with message.channel.typing():
        reply_text = await asyncio.to_thread(
            call_gemini, user_text
        )

    reply_text = replace_emojis(reply_text)

    if len(reply_text) > 1900:
        reply_text = reply_text[:1900]

    try:
        await message.reply(
            reply_text,
            mention_author=False
        )
    except discord.HTTPException as e:
        print("DISCORD REPLY ERROR:", repr(e))

# --- KHỞI ĐỘNG ---
if not DISCORD_TOKEN or not GEMINI_API_KEY:
    raise RuntimeError(
        "Chưa cấu hình DISCORD_TOKEN hoặc GEMINI_API_KEY trên Render."
    )

client.run(DISCORD_TOKEN)
                
