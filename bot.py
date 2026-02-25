import asyncio, json, random, time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import *

bot = Bot(TOKEN)
dp = Dispatcher()
DB = "users.json"

START_BALANCE = 500
DAILY_REWARD = 200
BET_OPTIONS = [50, 100, 200, 500]

TITLES = {
    "лудік": 250,
    "додеп": 500,
    "ластдеп": 1000
}

# ---------- DB ----------
def load():
    try:
        with open(DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save(d):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ---------- KEYBOARDS ----------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профіль"), KeyboardButton(text="🎁 Daily")],
        [KeyboardButton(text="🎲 Кості"), KeyboardButton(text="🎰 777")],
        [KeyboardButton(text="💣 ALL IN")],
        [KeyboardButton(text="🏪 Магазин"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="➕ Видати гроші")]
    ],
    resize_keyboard=True
)

def bets_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(b))] for b in BET_OPTIONS] +
                 [[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )

dice_nums_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
        [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="6")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

# ---------- TEMP STATE ----------
wait = {}

# ---------- START ----------
@dp.message(CommandStart())
async def start(msg: types.Message):
    users = load()
    uid = str(msg.from_user.id)

    if uid in users:
        await msg.answer("Меню 👇", reply_markup=main_kb)
        return

    await msg.answer("✏️ Напиши свій нік:")
    wait[uid] = {"step": "reg"}

# ---------- TEXT ----------
@dp.message()
async def text(msg: types.Message):
    users = load()
    uid = str(msg.from_user.id)
    text = msg.text

    # ----- REG -----
    if uid in wait and wait[uid]["step"] == "reg":
        if len(text) < 3:
            await msg.answer("Нік мінімум 3 символи")
            return
        users[uid] = {
            "nick": text,
            "balance": START_BALANCE,
            "daily": 0
        }
        save(users)
        wait.pop(uid)
        await msg.answer(
            f"✅ Реєстрація ок\n👤 {text}\n💰 {START_BALANCE} грн",
            reply_markup=main_kb
        )
        return

    if uid not in users:
        await start(msg)
        return

    u = users[uid]

    # ----- BACK -----
    if text == "⬅️ Назад":
        wait.pop(uid, None)
        await msg.answer("Меню 👇", reply_markup=main_kb)
        return

    # ----- PROFILE -----
    if text == "👤 Профіль":
        title = u.get("title", "—")
        await msg.answer(
            f"👤 {u['nick']}\n🎖 {title}\n💰 {u['balance']} грн"
        )
        return

    # ----- DAILY -----
    if text == "🎁 Daily":
        now = time.time()
        if now - u["daily"] < 86400:
            await msg.answer("⏳ Ще рано")
            return
        u["daily"] = now
        u["balance"] += DAILY_REWARD
        save(users)
        await msg.answer(f"+{DAILY_REWARD} грн 🎁")
        return

    # ----- CHECK BALANCE -----
    if text in ["🎲 Кості", "🎰 777", "💣 ALL IN"] and u["balance"] <= 0:
        await msg.answer("❌ У тебе 0 грн, гра недоступна")
        return

    # ----- DICE -----
    if text == "🎲 Кості":
        wait[uid] = {"step": "dice_bet"}
        await msg.answer("Обери ставку:", reply_markup=bets_kb())
        return

    if uid in wait and wait[uid]["step"] == "dice_bet":
        if not text.isdigit():
            await msg.answer("Обери ставку кнопкою")
            return
        bet = int(text)
        if bet > u["balance"]:
            await msg.answer("💸 Мало грошей")
            return
        wait[uid] = {"step": "dice_num", "bet": bet}
        await msg.answer("Обери число:", reply_markup=dice_nums_kb)
        return

    if uid in wait and wait[uid]["step"] == "dice_num":
        if not text.isdigit():
            return
        num = int(text)
        bet = wait[uid]["bet"]
        roll = random.randint(1, 6)

        if roll == num:
            win = bet * 5
            u["balance"] += win
            res = f"🎲 {roll}\n🎉 +{win}"
        else:
            u["balance"] -= bet
            res = f"🎲 {roll}\n❌ -{bet}"

        save(users)
        wait.pop(uid)
        await msg.answer(res, reply_markup=main_kb)
        return

    # ----- SLOT -----
    if text == "🎰 777":
        wait[uid] = {"step": "slot"}
        await msg.answer("Обери ставку:", reply_markup=bets_kb())
        return

    if uid in wait and wait[uid]["step"] == "slot":
        if not text.isdigit():
            await msg.answer("Обери ставку кнопкою")
            return
        bet = int(text)
        if bet > u["balance"]:
            await msg.answer("💸 Мало грошей")
            return

        u["balance"] -= bet
        res = [random.choice(["7️⃣", "🍒", "💎"]) for _ in range(3)]
        if res.count("7️⃣") == 3:
            u["balance"] += bet * 10
            out = " ".join(res) + "\n🎉 JACKPOT x10"
        else:
            out = " ".join(res)

        save(users)
        wait.pop(uid)
        await msg.answer(out, reply_markup=main_kb)
        return

    # ----- ALL IN -----
    if text == "💣 ALL IN":
        if random.choice([True, False]):
            u["balance"] *= 2
            out = "💣 WIN x2"
        else:
            u["balance"] = 0
            out = "💀 LOSE"
        save(users)
        await msg.answer(out)
        return

    # ----- SHOP -----
    if text == "🏪 Магазин":
        out = "🏪 Магазин титулів:\n"
        for t, p in TITLES.items():
            out += f"{t} — {p} грн\n"
        out += "\nНапиши: купити <назва>"
        await msg.answer(out)
        return

    if text.lower().startswith("купити "):
        title = text.lower().replace("купити ", "").strip()
        if title not in TITLES:
            await msg.answer("❌ Нема такого титулу")
            return
        price = TITLES[title]
        if u["balance"] < price:
            await msg.answer("💸 Мало грошей")
            return
        u["balance"] -= price
        u["title"] = title
        save(users)
        await msg.answer(f"🎖 Титул «{title}» куплено")
        return

    # ----- TOP -----
    if text == "🏆 Топ":
        top = sorted(users.values(), key=lambda x: x["balance"], reverse=True)[:5]
        out = "🏆 ТОП:\n"
        for i, p in enumerate(top, 1):
            out += f"{i}. {p['nick']} — {p['balance']} грн\n"
        await msg.answer(out)
        return

    # ----- ADMIN GIVE -----
    if text == "➕ Видати гроші":
        if msg.from_user.id != ADMIN_ID:
            await msg.answer("❌ Не адмін")
            return
        wait[uid] = {"step": "give"}
        await msg.answer("Введи суму:")
        return

    if uid in wait and wait[uid]["step"] == "give":
        if not text.isdigit():
            await msg.answer("Введи число")
            return
        u["balance"] += int(text)
        save(users)
        wait.pop(uid)
        await msg.answer("✅ Гроші видано", reply_markup=main_kb)
        return

# ---------- RUN ----------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())