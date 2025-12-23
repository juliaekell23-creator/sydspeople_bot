from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍 Товары", callback_data="shop:0")
    kb.button(text="📄 Прайс-лист", callback_data="price")
    kb.button(text="☕️ Заказать кофе", callback_data="order:start")
    kb.button(text="✉️ Оставить заявку", callback_data="lead:start")
    kb.button(text="❓ Вопросы", callback_data="faq")
    kb.button(text="📍 Контакты", callback_data="contacts")
    kb.adjust(2, 2, 2)
    return kb.as_markup()

def shop_kb(offset: int, has_more: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if offset > 0:
        kb.button(text="← Назад", callback_data=f"shop:{max(0, offset-6)}")
    if has_more:
        kb.button(text="Вперёд →", callback_data=f"shop:{offset+6}")
    kb.button(text="🏠 Меню", callback_data="menu")
    kb.adjust(2, 1)
    return kb.as_markup()

def product_kb(product_id: int, lot_url: str | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="☕️ Заказать этот лот", callback_data=f"order:product:{product_id}")
    if lot_url:
        kb.button(text="🔗 Описание на сайте", url=lot_url)
    kb.button(text="🛍 К товарам", callback_data="shop:0")
    kb.adjust(1, 1, 1)
    return kb.as_markup()
