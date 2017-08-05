import sys
import time
import threading
import telepot
from telepot.loop import MessageLoop

bot = telepot.Bot('438370426:AAG3pe5fwtKN42TqnTel3WZ-QU4LqDP0Wos')

def on_chat_message(msg):
	contentType, chatType, chatId = telepot.glance(msg)
	
	if contentType != 'text':
		return
	
	if contentType == 'text':
		textFromUser = msg['text']
			
		if textFromUser == '/start':
			bot.sendMessage(chatId, 'hello')
				

MessageLoop(bot, {'chat': on_chat_message}).run_as_thread()
print('Listening ...')

#Keep the program running
while 1:
	time.sleep(10)