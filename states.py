from aiogram.fsm.state import State, StatesGroup

class LeadForm(StatesGroup):
    name = State()
    contact = State()
    message = State()

class OrderForm(StatesGroup):
    product_id = State()
    qty = State()
    grind = State()
    city = State()
    comment = State()
