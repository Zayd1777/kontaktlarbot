import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import sqlite3
import os
from dotenv import load_dotenv

# .env fayldan tokenni yuklash
load_dotenv()

# Loglama sozlash
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation holatlari
ADD_NAME, ADD_PHONE, ADD_PROFESSION, ADD_REGION = range(4)

# Ma'lumotlar bazasini yaratish
def init_db():
    conn = sqlite3.connect('contacts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contacts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  profession TEXT,
                  region TEXT)''')
    conn.commit()
    conn.close()

def add_contact(name, phone, profession, region):
    conn = sqlite3.connect('contacts.db')
    c = conn.cursor()
    c.execute("INSERT INTO contacts (name, phone, profession, region) VALUES (?, ?, ?, ?)",
              (name, phone, profession, region))
    conn.commit()
    conn.close()

def search_contacts(region=None, profession=None):
    conn = sqlite3.connect('contacts.db')
    c = conn.cursor()
    if region and profession:
        c.execute("SELECT * FROM contacts WHERE region=? AND profession=?", (region, profession))
    elif region:
        c.execute("SELECT * FROM contacts WHERE region=?", (region,))
    elif profession:
        c.execute("SELECT * FROM contacts WHERE profession=?", (profession,))
    else:
        c.execute("SELECT * FROM contacts")
    results = c.fetchall()
    conn.close()
    return results

def get_regions():
    conn = sqlite3.connect('contacts.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT region FROM contacts WHERE region IS NOT NULL")
    regions = [row[0] for row in c.fetchall()]
    conn.close()
    return regions

def get_professions():
    conn = sqlite3.connect('contacts.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT profession FROM contacts WHERE profession IS NOT NULL")
    professions = [row[0] for row in c.fetchall()]
    conn.close()
    return professions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        rf"Salom {user.mention_html()}! Men kontaktlarni boshqaruvchi botman.",
        reply_markup=main_menu_keyboard()
    )

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("\u2795 Kontakt qo'shish", callback_data='add_contact')],
        [InlineKeyboardButton("\ud83d\udd0d Kontakt qidirish", callback_data='search_contacts')],
        [InlineKeyboardButton("\ud83d\udccd Hudud bo'yicha qidirish", callback_data='search_by_region')],
        [InlineKeyboardButton("\ud83d\udc68\u200d\u2695\ufe0f Kasb bo'yicha qidirish", callback_data='search_by_profession')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Bosh menyu:", reply_markup=main_menu_keyboard())

async def add_contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Kontakt ismini kiriting:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Telefon raqamini kiriting:")
    return ADD_PHONE

async def add_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Kasbini kiriting:")
    return ADD_PROFESSION

async def add_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['profession'] = update.message.text
    await update.message.reply_text("Hududni (shahar/tuman) kiriting:")
    return ADD_REGION

async def add_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['region'] = update.message.text
    add_contact(
        context.user_data['name'],
        context.user_data['phone'],
        context.user_data['profession'],
        context.user_data['region']
    )
    await update.message.reply_text("\u2705 Kontakt muvaffaqiyatli qo'shildi!", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Amal bekor qilindi.', reply_markup=main_menu_keyboard())
    return ConversationHandler.END

def main():
    init_db()
    TOKEN = os.getenv("BOT_TOKEN")
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_contact_start, pattern='^add_contact$')],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_phone)],
            ADD_PROFESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_profession)],
            ADD_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_region)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))

    application.run_polling()

if __name__ == '__main__':
    main()
