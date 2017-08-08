import sys
import time
import threading
import math
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InputTextMessageContent
from telepot.namedtuple import ForceReply

iouUsageMap = {}	#Map user to currently using iou (userId:msgIdf)
iouMap = {}			#Map iou to respective message_identifier (msgIdf:iou)
userMap = {}		#Map user to userid (userId:person)


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
			
			owner = Person(userId, msg['from']['first_name'])
			owner.addNewIou(iou.iouMsgIdf, iou)
			userMap.update({userId:owner})
									
		if userId in iouUsageMap:
			iouMsgIdf = iouUsageMap[userId]
			iou = iouMap[iouMsgIdf]
			
			if not isFloat(textFromUser):
				bot.sendMessage(userId, 'Please enter a valid amount')
			else:
				iou.getSpender(userId).increaseAmtSpent(float(textFromUser))
				iou.updateDisplay()
				iouUsageMap.pop(userId)
  

def on_callback_query(msg):
	queryId, fromId, queryData = telepot.glance(msg, flavor='callback_query')
	print('Callback Query:', queryId, fromId, queryData)
	
	fromFirstName = msg['from']['first_name']
	iouMsgIdf = telepot.message_identifier(msg['message'])
	
	print('From: ', fromFirstName, ' (', fromId, ')')
	print('Query ID: ', queryId)
	print('MsgIdf: ', iouMsgIdf, '\n')
	
	
	#Switch to PM, reply bot with amount spent
	if queryData == 'addExpense':
		iouUsageMap.update({fromId:iouMsgIdf})
		iou = iouMap[iouMsgIdf]
		
		if fromId not in iou.spenderList:
			person = Person(fromId, msg['from']['first_name'])
			iouMap[iouMsgIdf].addSpender(person)
		
		bot.sendMessage(fromId, 'Send me the amount you spent')	#Need to explore switch inline pm
	

def on_inline_query(msg):
	def compute():
		queryId, fromId, queryData = telepot.glance(msg, flavor='inline_query')
		print('Query ID: ', queryId)
		print('From Id: ', fromId)
		print('QueryString: ', queryData)
		return 
		
	answerer.answer(msg, compute)


def getPublicKeyboard():
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
					[InlineKeyboardButton(text='Share IOU', callback_data='share')],
					[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
				])
	return keyboard
			
			
def isFloat(string):
	try:
		float(string)
		return True
	except ValueError:
		return False
			
			
class Iou:
	def __init__(self, ownerId, chatId):
		self.ownerId = ownerId
		self.chatId = chatId
		
		self.spenderList = {}	#(userId:person)
		
		self.displayText = ''
		
	def createNewIou(self):
		self.displayText = ("A new IOU has been created\n"
							"Click 'Add Expense' to add an amout you spent\n"
							"Kindly speak to @ExpenseSplitterBot to activate this service")
		self.keyboard = InlineKeyboardMarkup(inline_keyboard=[
						[InlineKeyboardButton(text='Share IOU', callback_data='share')],
						[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
					])
		self.iouMsg = bot.sendMessage(self.chatId, self.displayText, reply_markup=self.keyboard)
		self.iouMsgIdf = telepot.message_identifier(self.iouMsg)
		
	def addSpender(self, person):
		self.spenderList.update({person.userId:person})
		
	def getSpender(self, userId):
		return self.spenderList[userId]
		
	def getDisplaySpender(self):
		display = ''
		for userId, person in self.spenderList.items():
			name = person.first_name
			amtSpent = person.amtSpent
			display += name + ' spent $' + str(amtSpent) + '\n'
		display += ("\n\n\nClick 'Add Expense' to add an amout you spent\n"
					"Kindly speak to @ExpenseSplitterBot to activate this service")
		return display
		
	def updateDisplay(self):
		self.displayText = self.getDisplaySpender()
		bot.editMessageText(self.iouMsgIdf, self.displayText, reply_markup=self.keyboard)
	
	
class Person:
	def __init__(self, userId, first_name):
		self.userId = userId
		self.first_name = first_name
		
		self.amtSpent = 0
		self.amtPaid = 0
		self.amtToPay = 0
		self.amtToReceive = 0
		
		self.iouListOwned = {}
	
	def addNewIou(self, iouMsgIdf, iou):
		self.iouListOwned.update({iouMsgIdf:iou})
		
	def increaseAmtSpent(self, amount):
		self.amtSpent += amount
	
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