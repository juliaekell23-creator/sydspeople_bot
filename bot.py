from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from config import Config
from keyboards import main_menu, shop_kb, product_kb
from states import LeadForm, OrderForm, FaqForm
import db
from services.price import fetch_price_text

# ——— ТЕКСТЫ ——————————————————————————————————————————

ABOUT_TEXT = """syd’s — ну да, это мы. Те самые одержимые, что добровольно таскают зелёный кофе через полмира. Зачем-то постоянно куда-то едем, лезем в горы, пьём тонны образцов и делаем вид, что различаем 12 оттенков черники. Африка, Латинская Америка, Азия — мы вечно в дороге. Местные фермеры нас уже узнают по голосу (и, кажется, иногда даже скрываются в горах). Уважаем их труд и честно стараемся не испортить ни логистикой, ни нашими экспериментами. Любим прозрачность, порядок в бумагах и лёгкий творческий хаос во всём остальном. В общем, мы — те, с кем можно поговорить о ферментации, и часами спорить, какой кофе лучше в аэропорте пить, если отменили рейс.

syd's - это прямое партнерство с фермерами и станциями обработки кофе во всех ключевых регионах произрастания. Каждая отправка партии сопровождается обязательным тестированием образцов кофе в нашей лаборатории, а каждую позицию в наш ассортимент команда отбирает находясь в странах произрастания во время урожая. За счет долгосрочных контрактов с производителями мы даем нашим оптовым клиентам конкурентоспособную цену и подходящие условия оплаты. Это позволяет сделать бизнес не только качественным с точки зрения продукта, но и обеспечить его необходимой рентабельностью.
"""

TELEGRAM_PRICE_TEXT = """Привет, друзья!

Сегодня в «Онлайн-складе» 👇🏼

МИКРОЛОТЫ:

Ss-GUA-24-104
Гватемала Лас Мерседес Пакамара | 5х69 кг | washed | джут

Ss-GUA-24-105
Гватемала Лас Мерседес Гейша | 3х69 кг | washed | джут

Ss-0238
Колумбия Вилла Бетулия Примитиво | 3×35 кг | natural/anaerobic | джут+grainpro   

Ss-0204
Бразилия Эльдорадо Лот 3 | 97 кг | natural | джут+grainpro  

РЕГИОНАЛЬНЫЙ КОФЕ

Sr-ЕТH-25-010
Эфиопия Сидамо Грейд 2 | 339х60 кг | washed | джут+grainpro | ожидаем 21 декабря

Sr-PER-25-078
Перу Пальма Реаль | 16х69 кг | washed | джут+grainpro | ожидаем 20 декабря

Sr-PER-25-072
Перу Санта Роса | 51х69 кг | washed | джут+grainpro 

Ss-IND-24-090
Индонезия Мандхелинг Грейд 1 | 106х60 кг | wet-hull | джут+grainpro

БАЗОВЫЙ КОФЕ

Sc-COL-24-048
Колумбия Эксельсо | 99х70 кг | washed | джут

Sc-BRA-25-002
Бразилия Сантос 14/16 | 75х59 кг | джут

Sc-BRA-25-004
Бразилия Моджиана 17/18 | 160х59 кг | джут
"""

CONTACTS_TEXT = """Наш офис находится в самом центре Петербурга. Мы работаем с 10:00 до 18:30, но часто отвечаем на сообщения чуть раньше или после окончания рабочего дня. Пиши нам на почту hi@sydspeople.com в любое время, мы всегда на связи!

inst: https://www.instagram.com/sydspeople?igsh=MWw1OXphYWVzbG53eA==
tg: https://t.me/syds_hunters
"""

FAQ_PROMPT = "Задай мне любой вопрос, и либо я сам, либо мои коллеги из syd's ответят на него в ближайшее время!"

# ——— DISPATCHER ———————————————————————————————————

def build_dispatcher(cfg: Config) -> Dispatcher:
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(m: Message):
        await m.answer("Привет! Чем помочь?", reply_markup=main_menu())

    # — about —
    @dp.message(Command("about"))
    async def about_cmd(m: Message):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📚 Библиотека лотов",
                url=f"{cfg.site_base_url.rstrip('/')}/library"
            )],
            [InlineKeyboardButton(
                text="ℹ️ Подробнее о компании",
                url=cfg.site_base_url
            )],
        ])
        await m.answer(ABOUT_TEXT, reply_markup=kb)

    # — price —
    def build_price_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Онлайн-прайс",
                url=f"{cfg.site_base_url.rstrip('/')}/price"
            )],
            [InlineKeyboardButton(
                text="Telegram-прайс",
                callback_data="price:telegram"
            )],
        ])

    @dp.message(Command("price"))
    async def price_cmd(m: Message):
        await m.answer("Выбери формат прайса:", reply_markup=build_price_keyboard())

    @dp.callback_query(F.data == "price")
    async def price_cb(c: CallbackQuery):
        await c.message.edit_text("Выбери формат прайса:", reply_markup=build_price_keyboard())
        await c.answer()

    @dp.callback_query(F.data == "price:telegram")
    async def price_telegram(c: CallbackQuery):
        await c.message.answer(TELEGRAM_PRICE_TEXT, reply_markup=main_menu())
        await c.answer()

    # — lots —
    @dp.message(Command("lots"))
    async def lots_cmd(m: Message):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📚 Открыть библиотеку лотов",
                url=f"{cfg.site_base_url.rstrip('/')}/library"
            )],
        ])
        await m.answer(
            "«Библиотека лотов» — это карточки по регионам: Кения, Руанда, Бурунди, Эфиопия, Уганда, Индонезия, Перу, Бразилия, Колумбия, Гватемала. "
            "Внутри каждой карточки — список лотов из этой страны, а названия лотов кликабельные и ведут на сайт.",
            reply_markup=kb,
        )

    # — contacts —
    @dp.message(Command("contacts"))
    async def contacts_cmd(m: Message):
        await m.answer(CONTACTS_TEXT, reply_markup=main_menu())

    @dp.callback_query(F.data == "contacts")
    async def contacts_cb(c: CallbackQuery):
        await c.message.edit_text(CONTACTS_TEXT, reply_markup=main_menu())
        await c.answer()

    # — faq (вопросы) —
    @dp.message(Command("faq"))
    async def faq_cmd(m: Message, state: FSMContext):
        await state.set_state(FaqForm.question)
        await m.answer(FAQ_PROMPT)

    @dp.callback_query(F.data == "faq")
    async def faq_cb(c: CallbackQuery, state: FSMContext):
        await state.set_state(FaqForm.question)
        await c.message.edit_text(FAQ_PROMPT, reply_markup=main_menu())
        await c.answer()

    @dp.message(FaqForm.question)
    async def faq_question(m: Message, state: FSMContext, bot: Bot):
        await state.clear()
        await m.answer("Спасибо! Передали вопрос команде syd's. Ответим в ближайшее время 🙂", reply_markup=main_menu())

        username = f"@{m.from_user.username}" if m.from_user.username else f"id {m.from_user.id}"
        admin_text = (
            "❓ Новый вопрос из /faq\n"
            f"От: {username}\n"
            f"user_id: {m.from_user.id}\n"
            f"chat_id: {m.chat.id}\n"
            f"Вопрос:\n{m.text}"
        )
        for admin_id in cfg.admin_ids:
            await bot.send_message(admin_id, admin_text)

    # — остальные хендлеры (товары, заказы, заявки) —

    @dp.callback_query(F.data == "menu")
    async def menu(c: CallbackQuery):
        await c.message.edit_text("Меню:", reply_markup=main_menu())
        await c.answer()

    # … здесь остаются все прежние хендлеры shop / lead / order …

    return dp