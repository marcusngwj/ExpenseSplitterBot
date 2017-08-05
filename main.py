import sys
import time
import threading
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InputTextMessageContent

def on_chat_message(msg):
	contentType, chatType, chatId = telepot.glance(msg)
	
	if contentType != 'text':
		return
	
	if contentType == 'text':
		textFromUser = msg['text']
			
		if textFromUser == '/start':
			bot.sendMessage(chatId, startMessage)
		
		elif textFromUser == '/newIOU':
			keyboard = InlineKeyboardMarkup(inline_keyboard=[
							[dict(text='Share IOU', switch_inline_query='share')],
							[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
						])
			bot.sendMessage(chatId, 'Testing', reply_markup=keyboard)
			

def on_callback_query(msg):
	queryId, fromId, queryData = telepot.glance(msg, flavor='callback_query')
	print('Callback Query:', queryId, fromId, queryData)
	

def on_inline_query(msg):
	def compute():
		queryId, fromId, queryData = telepot.glance(msg, flavor='inline_query')
		print('Query ID: ', queryId)
		print('From Id: ', fromId)
		print('QueryString: ', queryData)
		return 
		
	answerer.answer(msg, compute)

	
startMessage = "To create a new IOU, enter '/newIOU'"

bot = telepot.Bot('438370426:AAG3pe5fwtKN42TqnTel3WZ-QU4LqDP0Wos')
answerer = telepot.helper.Answerer(bot)

MessageLoop(bot, {'chat': on_chat_message,
				  'callback_query': on_callback_query,
				  'inline_query': on_inline_query}).run_as_thread()
print('Listening ...')

#Keep the program running
while 1:
	time.sleep(10)