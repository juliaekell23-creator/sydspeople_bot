from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import Config
from keyboards import main_menu, shop_kb, product_kb
from states import LeadForm, OrderForm
import db
from services.price import fetch_price_text

def build_dispatcher(cfg: Config) -> Dispatcher:
    dp = Dispatcher()

    @dp.message(F.text == "/start")
    async def start(m: Message):
        await m.answer("Привет! Чем помочь?", reply_markup=main_menu())

    @dp.callback_query(F.data == "menu")
    async def menu(c: CallbackQuery):
        await c.message.edit_text("Меню:", reply_markup=main_menu())
        await c.answer()

    @dp.callback_query(F.data == "contacts")
    async def contacts(c: CallbackQuery):
        await c.message.edit_text(
            "Контакты:\n• Напиши сюда в бот — мы ответим\n• Или смотри сайт/каталог",
            reply_markup=main_menu(),
        )
        await c.answer()

    @dp.callback_query(F.data == "faq")
    async def faq(c: CallbackQuery):
        await c.message.edit_text(
            "FAQ:\n• Как заказать? → нажми «Заказать кофе»\n• Нужен прайс? → «Прайс-лист»\n• Нужна консультация? → «Оставить заявку»",
            reply_markup=main_menu(),
        )
        await c.answer()

    # --- SHOP ---
    @dp.callback_query(F.data.startswith("shop:"))
    async def shop(c: CallbackQuery):
        offset = int(c.data.split(":")[1])
        items = db.list_products(offset=offset, limit=6)
        has_more = len(items) == 6

        if not items:
            await c.message.edit_text("Пока нет товаров в наличии.", reply_markup=main_menu())
            await c.answer()
            return

        text_lines = ["Товары в наличии (нажми номер, чтобы открыть карточку):\n"]
        for it in items:
            text_lines.append(f"{it['id']}. {it['title']} — {it['price_rub']} ₽")

        # сделаем “псевдо-кнопки” через инструкции + callback на product:<id>
        kb = shop_kb(offset, has_more)
        await c.message.edit_text("\n".join(text_lines) + "\n\nНапиши номер товара в чат.", reply_markup=kb)
        await c.answer()

    @dp.message(F.text.regexp(r"^\d+$"))
    async def open_product_by_number(m: Message):
        pid = int(m.text)
        p = db.get_product(pid)
        if not p:
            return

        lot_url = p["lot_url"]
        text = (
            f"**{p['title']}**\n"
            f"Цена: {p['price_rub']} ₽\n"
            f"{('Заметка: ' + p['note']) if p['note'] else ''}"
        )
        await m.answer(text, reply_markup=product_kb(pid, lot_url), parse_mode="Markdown")

    # --- PRICE ---
    @dp.callback_query(F.data == "price")
    async def price(c: CallbackQuery):
        if cfg.price_csv_url:
            try:
                text = await fetch_price_text(cfg.price_csv_url)
            except Exception:
                text = "Не получилось загрузить прайс. Напиши нам — пришлём актуальный."
        else:
            # fallback: из базы
            items = db.list_products(offset=0, limit=30)
            text = "Прайс:\n\n" + "\n".join(f"• {x['title']} — {x['price_rub']} ₽" for x in items)

        await c.message.edit_text(text, reply_markup=main_menu())
        await c.answer()

    # --- LEAD FORM ---
    @dp.callback_query(F.data == "lead:start")
    async def lead_start(c: CallbackQuery, state: FSMContext):
        await state.set_state(LeadForm.name)
        await c.message.edit_text("Как тебя зовут?")
        await c.answer()

    @dp.message(LeadForm.name)
    async def lead_name(m: Message, state: FSMContext):
        await state.update_data(name=m.text.strip())
        await state.set_state(LeadForm.contact)
        await m.answer("Оставь контакт (телефон / @username / email):")

    @dp.message(LeadForm.contact)
    async def lead_contact(m: Message, state: FSMContext):
        await state.update_data(contact=m.text.strip())
        await state.set_state(LeadForm.message)
        await m.answer("Опиши запрос одним сообщением:")

    @dp.message(LeadForm.message)
    async def lead_message(m: Message, state: FSMContext, bot: Bot):
        data = await state.get_data()
        lead_id = db.create_lead(
            user_id=m.from_user.id,
            username=m.from_user.username,
            name=data["name"],
            contact=data["contact"],
            message=m.text.strip(),
        )
        await state.clear()
        await m.answer("Спасибо! Приняли заявку, скоро ответим 🙂", reply_markup=main_menu())

        admin_text = (
            f"🆕 Заявка #{lead_id}\n"
            f"От: {data['name']} (@{m.from_user.username})\n"
            f"Контакт: {data['contact']}\n"
            f"Текст: {m.text.strip()}"
        )
        for admin_id in cfg.admin_ids:
            await bot.send_message(admin_id, admin_text)

    # --- ORDER FORM ---
    @dp.callback_query(F.data == "order:start")
    async def order_start(c: CallbackQuery, state: FSMContext):
        await state.set_state(OrderForm.product_id)
        await c.message.edit_text("Ок! Напиши номер товара (его видно в «Товары»).")
        await c.answer()

    @dp.callback_query(F.data.startswith("order:product:"))
    async def order_from_card(c: CallbackQuery, state: FSMContext):
        pid = int(c.data.split(":")[-1])
        await state.set_state(OrderForm.product_id)
        await state.update_data(product_id=pid)
        await state.set_state(OrderForm.qty)
        await c.message.edit_text("Сколько штук/пачек нужно? (например: 1)")
        await c.answer()

    @dp.message(OrderForm.product_id)
    async def order_product_id(m: Message, state: FSMContext):
        if not m.text.strip().isdigit():
            await m.answer("Нужен номер товара (цифрой).")
            return
        pid = int(m.text.strip())
        if not db.get_product(pid):
            await m.answer("Не нашла такой товар. Открой «Товары» и пришли номер оттуда.")
            return
        await state.update_data(product_id=pid)
        await state.set_state(OrderForm.qty)
        await m.answer("Сколько штук/пачек нужно? (например: 1)")

    @dp.message(OrderForm.qty)
    async def order_qty(m: Message, state: FSMContext):
        if not m.text.strip().isdigit():
            await m.answer("Количество — цифрой 🙂")
            return
        await state.update_data(qty=int(m.text.strip()))
        await state.set_state(OrderForm.grind)
        await m.answer("Помол: зерно / фильтр / эспрессо?")

    @dp.message(OrderForm.grind)
    async def order_grind(m: Message, state: FSMContext):
        await state.update_data(grind=m.text.strip())
        await state.set_state(OrderForm.city)
        await m.answer("Город/доставка (например: Москва):")

    @dp.message(OrderForm.city)
    async def order_city(m: Message, state: FSMContext):
        await state.update_data(city=m.text.strip())
        await state.set_state(OrderForm.comment)
        await m.answer("Комментарий к заказу (или напиши «-»):")

    @dp.message(OrderForm.comment)
    async def order_finish(m: Message, state: FSMContext, bot: Bot):
        data = await state.get_data()
        pid = int(data["product_id"])
        product = db.get_product(pid)
        comment = m.text.strip()
        order_id = db.create_order(
            user_id=m.from_user.id,
            username=m.from_user.username,
            product_id=pid,
            qty=int(data["qty"]),
            grind=data["grind"],
            city=data["city"],
            comment=comment,
        )
        await state.clear()
        await m.answer("Приняли заказ! Скоро свяжемся для подтверждения ☕️", reply_markup=main_menu())

        admin_text = (
            f"🧾 Заказ #{order_id}\n"
            f"От: @{m.from_user.username} (id {m.from_user.id})\n"
            f"Товар: {product['title']} (#{pid})\n"
            f"Кол-во: {data['qty']}\n"
            f"Помол: {data['grind']}\n"
            f"Город: {data['city']}\n"
            f"Комментарий: {comment}"
        )
        for admin_id in cfg.admin_ids:
            await bot.send_message(admin_id, admin_text)

    return dp
