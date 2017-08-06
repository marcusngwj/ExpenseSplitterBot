import sys
import time
import threading
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

iouMap = {}

def on_chat_message(msg):
	contentType, chatType, chatId = telepot.glance(msg)
	userId = msg['from']['id']
	print('User Id: ', userId)
	
	if contentType != 'text':
		return
	
	if contentType == 'text':
		textFromUser = msg['text']
			
		if textFromUser == '/start':
			bot.sendMessage(chatId, startMessage)
		
		elif textFromUser == '/newIOU':
			keyboard = InlineKeyboardMarkup(inline_keyboard=[
							[InlineKeyboardButton(text='Share IOU', callback_data='share')],
							[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
						])
			iouMsg = bot.sendMessage(chatId, 'Testing', reply_markup=keyboard)
			iouMsgId = iouMsg['message_id']

			#iouMap.update({userId:iouMsgId})
			

def on_callback_query(msg):
	queryId, fromId, queryData = telepot.glance(msg, flavor='callback_query')
	iouMsgIdf = telepot.message_identifier(msg['message'])

	fromFirstName = msg['from']['first_name']
	
	if queryData == 'addExpense':
		keyboard = InlineKeyboardMarkup(inline_keyboard=[
						[InlineKeyboardButton(text='Share IOU', callback_data='share')],
						[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
					])
		testMsg = bot.editMessageText(iouMsgIdf, fromFirstName, reply_markup=keyboard)
			

	
startMessage = "To create a new IOU, enter '/newIOU'"

bot = telepot.Bot('438370426:AAG3pe5fwtKN42TqnTel3WZ-QU4LqDP0Wos')

MessageLoop(bot, {'chat': on_chat_message,
				  'callback_query': on_callback_query}).run_as_thread()
print('Listening ...')

#Keep the program running
while 1:
	time.sleep(10)