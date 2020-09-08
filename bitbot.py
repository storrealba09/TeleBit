from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from lbc import get_balance, get_deposit, get_listings, auto_pick, is_trade, read_messages, open_trade, get_contact_id, send_message, payment_completed, release_bitcoins, cost_aprox
import logging, threading, time


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

updater = Updater(token='BOT_KEY:BOT_SECRET')
dispatcher = updater.dispatcher
qty = 0


def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Presione /start para empezar")

def release(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Liberando! esta transaccion ha sido finalizada. Presione /start para comenzar")
    contact_id = get_contact_id()
    contact_id = str(contact_id)
    a= send_message("Liberando! muchas gracias!", contact_id)
    r = release_bitcoins(contact_id)
    dispatcher.add_handler(echa_handler)
    dispatcher.remove_handler(chat_handler)
    dispatcher.remove_handler(release_handler)

def chat(bot, update):
    text= update.message.text
    contact_id = get_contact_id()
    contact_id = str(contact_id)
    b= send_message(text, contact_id) #send_msg
    bot.send_message(chat_id=update.message.chat_id, text="mensaje enviado al comprador")
    global updates
    updates += 1

def echo2(bot, update):
    global qty
    text= update.message.text
    if (text.isdigit()):
        qty=int(text)
        costo = cost_aprox(qty)
        bot.send_message(chat_id=update.message.chat_id, text="ATENCION! costo deberia ser alredor de: "+ costo)
        list= get_listings(qty)
        n = len(list)
        button_list= []
        for s in list:
            ad_id = s
            ad_id = ad_id[-6:]
            button_list.append(InlineKeyboardButton(s, callback_data= "Iniciando contacto #"+ad_id) )
        reply= InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        bot.send_message(chat_id=update.message.chat_id, text="Seleccione un comprador, sus datos seran enviados automaticamente", reply_markup=reply)
    else :
        bot.send_message(chat_id=update.message.chat_id, text="Por favor ingrese solo numeros")


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

def listings(bot, update):
    list= get_listings()
    n = len(list)
    button_list= []
    for s in list:
        button_list .append(InlineKeyboardButton(s, callback_data= "NOJODAA") )
    reply= InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    bot.send_message(chat_id=update.message.chat_id, text="Seleccione un comprador", reply_markup=reply)
#38bf73ad-bd64-4cc8-9ec6-b97fcadf2740

button_list = [
    InlineKeyboardButton("Ver balance", callback_data="Para ver balance presione /balance"),
    InlineKeyboardButton("Ver direccion de Deposito", callback_data='No address por ahora'),
    InlineKeyboardButton("Cambiar de BTC a Bolivares", callback_data= "Que cantidad? \nEn Bolivares")
]

reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))


def chat_update(bot,update): #cerrar chat
    suffix_list = ['jpg', 'gif', 'png', 'tif', 'svg',]
    while True:
        time.sleep(5)
        global updates
        is_contact = is_trade()
        if is_contact != 0:
            a = read_messages()
            b = len(a)
            diff = b - updates
            if (diff>0):
                for i in range(diff):
                    if a[updates+i][-3:]  in suffix_list:
                        bot.send_photo(chat_id=update.message.chat_id, photo='http://yoursite.com/images/'+a[updates+i])
                    else:
                        bot.send_message(chat_id=update.message.chat_id, text=a[updates+i])
                updates = b
            contact_id = get_contact_id()
            contact_id = str(contact_id)
            payment = payment_completed(contact_id)
            print(payment)
            if payment != None:
                print(contact_id +' realizo pago')
                bot.send_message(chat_id=update.message.chat_id, text="El comprador ha marcado su pago como realizado, por favor revise su cuenta O ESPERE EL COMPROBANTE EN UNA IMAGEN y libere los fondos a traves de /release.")
                global release_handler
                release_handler = CommandHandler('release', release)
                dispatcher.add_handler(release_handler)

            #Wallet Balance
def send_balance(bot, update):
    send = get_balance()
    bot.send_message(chat_id=update.message.chat_id, text=send)

def button(bot, update):
    query = update.callback_query

    bot.edit_message_text(text="{}".format(query.data),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
    if query.data == "Que cantidad? \nEn Bolivares":
        dispatcher.remove_handler(echa_handler)
        global echo_handler
        echo_handler = MessageHandler(Filters.text, echo2)
        dispatcher.add_handler(echo_handler)

    if query.data[:3] == "Ini":
        ad_id = query.data[-6:]
        bot.send_message(chat_id=query.message.chat_id, text="ATENCION: \na partir de este momento sus mensajes seran enviados al comprador")
        trade = open_trade(ad_id,qty)
        print(trade)
        dispatcher.remove_handler(echo_handler)
        global chat_handler
        chat_handler = MessageHandler(Filters.text, chat)
        dispatcher.add_handler(chat_handler)
        global updates
        updates = 1


def keyboard(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hola! \nQue desea realizar? ", reply_markup=reply_markup)
    global thread
    thread = threading.Thread(target=chat_update, args=(bot,update))
    thread.start()

start_handler = CommandHandler('start', keyboard)
dispatcher.add_handler(start_handler)
balance_handler = CommandHandler('balance', send_balance)
dispatcher.add_handler(balance_handler)
dispatcher.add_handler(CallbackQueryHandler(button))
keyboard_handler = CommandHandler('empezar', keyboard)
dispatcher.add_handler(keyboard_handler)
echa_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echa_handler)


updater.start_polling()
updater.idle()
