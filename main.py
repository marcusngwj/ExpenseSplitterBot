import sys
import time
import threading
import math
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ForceReply

iouUsageMap = {}	#Map user to currently using iou (userId:(iouMsgIdf, serviceType))
iouMap = {}			#Map iou to respective message_identifier (msgIdf:iou)
userMap = {}		#Map user to userid (userId:person)

IOU_MSG_IDF = 0
SERVICE_TYPE = 1

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
			idfAndService = iouUsageMap[userId]
			iouMsgIdf = idfAndService[IOU_MSG_IDF]
			iou = iouMap[iouMsgIdf]
			
			if idfAndService[SERVICE_TYPE] == 'addExpense':
				if not isNonNegativeFloat(textFromUser):
					bot.sendMessage(userId, 'Please enter a valid amount')
				else:
					iou.getSpender(userId).increaseAmtSpent(float(textFromUser))
					iou.updateDisplay()
					iouUsageMap.pop(userId)
			
			if idfAndService[SERVICE_TYPE] == 'editExpense':
				if not isNonNegativeFloat(textFromUser):
					bot.sendMessage(userId, 'Please enter a valid amount')
				else:
					iou.getSpender(userId).editAmtSpent(float(textFromUser))
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
		serviceType = queryData
		idfAndService = [iouMsgIdf, serviceType]
		iouUsageMap.update({fromId:idfAndService})
		iou = iouMap[iouMsgIdf]
		
		if fromId not in iou.spenderList:
			person = Person(fromId, msg['from']['first_name'])
			iouMap[iouMsgIdf].addSpender(person)
		
		bot.sendMessage(fromId, 'Send me the amount you spent.')	#Need to explore switch inline pm
		
	if queryData == 'editExpense':
		serviceType = queryData
		idfAndService = [iouMsgIdf, serviceType]
		iouUsageMap.update({fromId:idfAndService})
		iou = iouMap[iouMsgIdf]
		
		if fromId not in iou.spenderList:
			person = Person(fromId, msg['from']['first_name'])
			iouMap[iouMsgIdf].addSpender(person)
		
		bot.sendMessage(fromId, 'Old record will be deleted.\nSend me the new amount.')	#Need to explore switch inline pm

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
		
def isNonNegativeFloat(string):
	return isFloat(string) and not float(string)<0
			
			
class Iou:
	def __init__(self, ownerId, chatId):
		self.ownerId = ownerId
		self.chatId = chatId
		
		self.spenderList = {}	#(userId:person)
		
		self.instructionalText = ("\n\n\nClick 'Add Expense' to add an amout you spent\n"
								  "Kindly speak to @ExpenseSplitterBot to activate this service")
		
	def createNewIou(self):
		displayText = "A new IOU has been created\n" + self.instructionalText
		
		self.keyboard = InlineKeyboardMarkup(inline_keyboard=[
						[InlineKeyboardButton(text='Share IOU', callback_data='share')],
						[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
						[InlineKeyboardButton(text='Edit expense', callback_data='editExpense')],
					])
		self.iouMsg = bot.sendMessage(self.chatId, displayText, reply_markup=self.keyboard)
		self.iouMsgIdf = telepot.message_identifier(self.iouMsg)
		
	def addSpender(self, person):
		self.spenderList.update({person.userId:person})
		
	def computeTotalExpenses(self):
		total = 0
		for userId, person in self.spenderList.items():
			total += person.amtSpent
		return total
	
	#Compute amount a person supposed to pay
	def computeExpectedAmtToPay(self):
		totalAmtSpent = self.computeTotalExpenses()
		numSpender = self.__getNumSpenders()
		return totalAmtSpent/numSpender
		
	def __computeReceivePay(self):
		expectedAmtToPay = self.computeExpectedAmtToPay()
		for userId, person in self.spenderList.items():
			shortfallAmt = expectedAmtToPay - person.amtSpent
			if shortfallAmt > 0:
				person.amtToPay = shortfallAmt
			else:
				person.amtToReceive = (-1)*shortfallAmt	
		
	def getSpender(self, userId):
		return self.spenderList[userId]
		
	def __getNumSpenders(self):
		return len(self.spenderList.keys())
		
	def getDisplayTotalExpenses(self):
		return 'Total amount spent: $' + str(self.computeTotalExpenses()) + '\n'
		
	def getDisplaySpender(self):
		display = ''
		for userId, person in self.spenderList.items():
			name = person.first_name
			amtSpent = person.amtSpent
			display += name + ' spent $' + str(amtSpent) + '\n'
		return display
		
	def getDisplayReceivePay(self):
		self.__computeReceivePay()
		display = ''
		for userId, person in self.spenderList.items():
			if person.amtToPay != 0:
				display += person.first_name + ' needs to pay $' + str(person.amtToPay) + '\n'
			elif person.amtToReceive != 0:
				display += person.first_name + ' needs to receive $' + str(person.amtToReceive) + '\n'
		return display
		
	def updateDisplay(self):
		self.displayText = self.getDisplayTotalExpenses() + self.getDisplayReceivePay() + self.instructionalText
		bot.editMessageText(self.iouMsgIdf, self.displayText, reply_markup=self.keyboard)
	#prog cant run. need debug
	
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
		
	def editAmtSpent(self, amount):
		self.amtSpent = amount
	
startMessage = "To create a new IOU, enter '/newIOU'"

bot = telepot.Bot('438370426:AAG3pe5fwtKN42TqnTel3WZ-QU4LqDP0Wos')

MessageLoop(bot, {'chat': on_chat_message,
				  'callback_query': on_callback_query}).run_as_thread()
print('Listening ...')

#Keep the program running
while 1:
	time.sleep(10)