import sys
import time
import threading
import math
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ForceReply

iouUsageMap = {}	#Map user to currently using iou
iouMap = {}			#Map iou to respective message_identifier
userMap = {}		#Map user to userid

def on_chat_message(msg):
	contentType, chatType, chatId = telepot.glance(msg)
	userId = msg['from']['id']
	print('User ID: ', userId)
	print('Chat ID: ', chatId)
	print('MESSAGE: ', msg, '\n')
	
	if contentType != 'text':
		return
	
	if contentType == 'text':
		textFromUser = msg['text']
			
		if textFromUser == '/start':
			bot.sendMessage(chatId, startMessage)
		
		elif textFromUser == '/newIOU':	
			iou = Iou(userId, chatId)
			iou.createNewIou()
			iouMap.update({iou.iouMsgIdf:iou})
			
			owner = Person(userId, msg['from']['first_name'], msg['from']['last_name'])
			userMap.update({userId:owner})
						
			
		if userId in iouUsageMap:
			iouMsgIdf = iouUsageMap[userId]
			iou = iouMap[iouMsgIdf]
			iou.displayText = userId
			iou.updateDisplay()
			iouUsageMap.pop(userId)
  

def on_callback_query(msg):
	queryId, fromId, queryData = telepot.glance(msg, flavor='callback_query')
	fromFirstName = msg['from']['first_name']
	iouMsgIdf = telepot.message_identifier(msg['message'])
	
	print('From: ', fromFirstName, ' (', fromId, ')')
	print('Query ID: ', queryId)
	print('MsgIdf: ', iouMsgIdf, '\n')
	
	
	#Switch to PM, reply bot with amount spent
	if queryData == 'addExpense':
		iouUsageMap.update({fromId:iouMsgIdf})
		
		bot.sendMessage(fromId, 'Send me the amount you spent')	#Need to explore switch inline pm
		

def getPublicKeyboard():
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
					[InlineKeyboardButton(text='Share IOU', callback_data='share')],
					[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
				])
	return keyboard
			
			
			
			
			
class Iou:
	def __init__(self, ownerId, chatId):
		self.ownerId = ownerId
		self.chatId = chatId
		
		self.spenderList = {}
		
		self.displayText = ''
		
	def createNewIou(self):
		self.displayText = ("A new IOU has been created\n"
							"Click 'Add Expense' to add an amout you spent")
		self.keyboard = InlineKeyboardMarkup(inline_keyboard=[
						[InlineKeyboardButton(text='Share IOU', callback_data='share')],
						[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
					])
		self.iouMsg = bot.sendMessage(self.chatId, self.displayText, reply_markup=self.keyboard)
		self.iouMsgIdf = telepot.message_identifier(self.iouMsg)
		
	def addSpender(self, person):
		spenderList.update({person.userId:person})
		
	def updateDisplay(self):
		bot.editMessageText(self.iouMsgIdf, self.displayText, reply_markup=self.keyboard)
	
	
class Person:
	def __init__(self, userId, first_name, last_name):
		self.userId = userId
		self.first_name = first_name
		self.last_name = last_name
		
		self.amtSpent = 0
		self.amtPaid = 0
		self.amtToPay = 0
		self.amtToReceive = 0
		
		self.iouListOwned = {}
		
		self.isAddingExpense = False
	
	def addNewIou(iouMsgIdf, iou):
		self.iouListOwned.update({iouMsgIdf:iou})
	
	
startMessage = "To create a new IOU, enter '/newIOU'"

bot = telepot.Bot('438370426:AAG3pe5fwtKN42TqnTel3WZ-QU4LqDP0Wos')

MessageLoop(bot, {'chat': on_chat_message,
				  'callback_query': on_callback_query}).run_as_thread()
print('Listening ...')

#Keep the program running
while 1:
	time.sleep(10)