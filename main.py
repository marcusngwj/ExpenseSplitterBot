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
	
	if userId not in userMap:
		person = Person(userId, msg['from']['first_name'])
		userMap.update({userId:person})
	else:
		person = userMap[userId]
		
	if contentType != 'text':
		return
	
	if contentType == 'text':
		textFromUser = msg['text']
		
		executeTextCommand(person, chatId, textFromUser)		
			
		if userId in iouUsageMap:
			responseToCallback(userId, textFromUser)
			

def on_callback_query(msg):
	queryId, fromId, queryData = telepot.glance(msg, flavor='callback_query')
	fromFirstName = msg['from']['first_name']
	iouMsgIdf = telepot.message_identifier(msg['message'])
	
	print('From: ', fromFirstName, ' (', fromId, ')')
	print('Query ID: ', queryId)
	print('MsgIdf: ', iouMsgIdf, '\n')
	
	if fromId not in userMap:
		person = Person(fromId, msg['from']['first_name'])
		userMap.update({fromId:person})
	else:
		person = userMap[fromId]
	
	#Switch to PM, reply bot with amount spent
	if queryData == 'addExpense':
		signalCallback_addResponse(person, queryData, iouMsgIdf)
		
	if queryData == 'editExpense':
		signalCallback_editResponse(person, queryData, iouMsgIdf)								
		
	if queryData == 'viewTransactions':
		serviceType = queryData
		idfAndService = [iouMsgIdf, serviceType]
		iouUsageMap.update({fromId:idfAndService})
		iou = iouMap[iouMsgIdf]
		
		viewTransactions(person, iou)
	
	if queryData == 'viewSpenders':	
		idfAndService = iouUsageMap[fromId]
		iouMsgIdf = idfAndService[IOU_MSG_IDF]
		iou = iouMap[iouMsgIdf]
		
		viewSpenders(person, iou)


def executeTextCommand(person, chatId, textFromUser):
	if textFromUser == '/start':
		command_start(chatId)
	
	elif textFromUser == '/newIOU':	
		command_newIOU(person, chatId)	
		
def command_start(chatId):
	startMessage = "To create a new IOU, enter '/newIOU'"
	bot.sendMessage(chatId, startMessage)

def command_newIOU(person, chatId):
	iou = Iou(person.getUserId(), chatId)
	createNewIouMsg(iou)
	iouMap.update({iou.getIouMsgIdf():iou})
	
	owner = person
	owner.addNewIou(iou.getIouMsgIdf(), iou)
	print('YATTA!')

		
def createNewIouMsg(iou):
	newIouDisplayText = "A new IOU has been created\n" + iou.getInstructionalText()
	
	iouMsg = bot.sendMessage(iou.getChatId(), newIouDisplayText, reply_markup=getPublicKeyboard())
	iou.setIouMsgIdf(telepot.message_identifier(iouMsg))

		
def signalCallback_addResponse(person, queryData, iouMsgIdf):
	serviceType = queryData
	idfAndService = [iouMsgIdf, serviceType]
	iouUsageMap.update({person.getUserId():idfAndService})
	iou = iouMap[iouMsgIdf]
	
	if person.getUserId() not in iou.getSpenderList():
		iouMap[iouMsgIdf].addSpender(person)
	
	bot.sendMessage(person.getUserId(), 'Send me the amount you spent.')	#Need to explore switch inline pm
	
def signalCallback_editResponse(person, queryData, iouMsgIdf):
	serviceType = queryData
	idfAndService = [iouMsgIdf, serviceType]
	iouUsageMap.update({person.getUserId():idfAndService})
	iou = iouMap[iouMsgIdf]
	
	if person.getUserId() not in iou.getSpenderList():
		iouMap[iouMsgIdf].addSpender(person)
	
	if person.getAmtSpent() == 0:
		bot.sendMessage(person.getUserId(), 'You have not spend any money so far.\nSend me the amount you spent.')
	else:
		expenseEditionMsg = ('You previously declared that you spent $' + formatMoney(person.getAmtSpent()) + '.\n'
							'This amount will be deleted.\n'
							'Send me the new amount.')
		bot.sendMessage(person.getUserId(), expenseEditionMsg)

	
def responseToCallback(userId, textFromUser):
	idfAndService = iouUsageMap[userId]
	iouMsgIdf = idfAndService[IOU_MSG_IDF]
	iou = iouMap[iouMsgIdf]
	
	if idfAndService[SERVICE_TYPE] == 'addExpense':
		responseToCallback_addExpense(iou, userId, textFromUser)
	
	if idfAndService[SERVICE_TYPE] == 'editExpense':
		responseToCallback_editExpense(iou, userId, textFromUser)

def responseToCallback_addExpense(iou, userId, textFromUser):
	if not isNonNegativeFloat(textFromUser):
		bot.sendMessage(userId, 'Please enter a valid amount')
	else:
		iou.getSpender(userId).increaseAmtSpent(float(textFromUser))
		updateDisplay(iou)
		totalAmtSpentFeedback = 'You have spent a total of $' + formatMoney(iou.getSpender(userId).getAmtSpent())
		bot.sendMessage(userId, totalAmtSpentFeedback)
		iouUsageMap.pop(userId)

def responseToCallback_editExpense(iou, userId, textFromUser):
	if not isNonNegativeFloat(textFromUser):
		bot.sendMessage(userId, 'Please enter a valid amount')
	else:
		iou.getSpender(userId).editAmtSpent(float(textFromUser))
		updateDisplay(iou)
		totalAmtSpentFeedback = 'You have spent a total of $' + formatMoney(iou.getSpender(userId).getAmtSpent())
		bot.sendMessage(userId, totalAmtSpentFeedback)
		iouUsageMap.pop(userId)
		

def viewTransactions(person, iou):
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
					[InlineKeyboardButton(text='View list of spenders', callback_data='viewSpenders')],
					[InlineKeyboardButton(text='View list of payers', callback_data='viewPayers')],
				])
				
	if person.getUserId() == iou.getChatId():	#If user is already in private chat with bot
		bot.sendMessage(person.getUserId(), 'Kindly choose from the following services', reply_markup=keyboard)	
	else:
		transactionInitMsg = 'A list of transaction services have been sent to ' + person.getFirstName() + ' via PM'
		bot.sendMessage(iou.getChatId(), transactionInitMsg)
		bot.sendMessage(person.getUserId(), 'Kindly choose from the following services', reply_markup=keyboard)	
		

def viewSpenders(person, iou):
	bot.sendMessage(person.getUserId(), iou.getDisplaySpender())
	

def updateDisplay(iou):
		iouDisplayText = iou.getDisplayTotalExpenses() + iou.getDisplayReceivePay() + iou.getInstructionalText()
		bot.editMessageText(iou.getIouMsgIdf(), iouDisplayText, reply_markup=getPublicKeyboard())


def getPublicKeyboard():
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
					[InlineKeyboardButton(text='Share IOU', callback_data='share')],
					[InlineKeyboardButton(text='Add expense', callback_data='addExpense')],
					[InlineKeyboardButton(text='Edit expense', callback_data='editExpense')],
					[InlineKeyboardButton(text='View transactions', callback_data='viewTransactions')],
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
		
def formatMoney(amount):
	return '%.2f' % amount

		


		
class Iou:
	def __init__(self, ownerId, chatId):
		self.__ownerId = ownerId
		self.__chatId = chatId
		
		self.__iouMsgIdf = None
		
		self.__spenderList = {}	#(userId:person)
		
		self.__instructionalText = ("\n\n\nClick 'Add Expense' to add an amout you spent\n"
								  "Kindly speak to @ExpenseSplitterBot to activate this service")
		
	def addSpender(self, person):
		self.__spenderList.update({person.getUserId():person})
		
	def __computeTotalExpenses(self):
		total = 0
		for userId, person in self.__spenderList.items():
			total += person.getAmtSpent()
		return total
	
	#Compute amount a person supposed to pay
	def __computeExpectedAmtToPay(self):
		totalAmtSpent = self.__computeTotalExpenses()
		numSpender = self.__getNumSpenders()
		return totalAmtSpent/numSpender
		
	def __computeReceivePay(self):
		expectedAmtToPay = self.__computeExpectedAmtToPay()
		for userId, person in self.__spenderList.items():
			self.__resetAmtToReceivePay(person)
			shortfallAmt = expectedAmtToPay - person.getAmtSpent()
			if shortfallAmt > 0:
				person.setAmtToPay(shortfallAmt)
			else:
				person.setAmtToReceive((-1)*shortfallAmt)
				
	def __resetAmtToReceivePay(self, person):
		person.setAmtToReceive(0)
		person.setAmtToPay(0)
				
	def setIouMsgIdf(self, iouMsgIdf):
		self.__iouMsgIdf = iouMsgIdf
		
	def getChatId(self):
		return self.__chatId
		
	def getIouMsg(self):
		return self.__iouMsg
		
	def getIouMsgIdf(self):
		return self.__iouMsgIdf
		
	def getSpenderList(self):
		return self.__spenderList
		
	def getSpender(self, userId):
		return self.__spenderList[userId]
		
	def getInstructionalText(self):
		return self.__instructionalText
		
	def __getNumSpenders(self):
		return len(self.__spenderList.keys())
		
	def getDisplayTotalExpenses(self):
		return 'Total amount spent: $' + formatMoney(self.__computeTotalExpenses()) + '\n'
		
	def getDisplaySpender(self):
		if not self.__spenderList:
			return 'There are no spenders at this moment'
			
		display = ''
		for userId, person in self.__spenderList.items():
			name = person.getFirstName()
			amtSpent = person.getAmtSpent()
			display += name + ' spent $' + formatMoney(amtSpent) + '\n'
		
		return display
		
	def getDisplayReceivePay(self):
		self.__computeReceivePay()
		display = ''
		for userId, person in self.__spenderList.items():
			if person.getAmtToPay() != 0:
				display += person.getFirstName() + ' needs to pay $' + formatMoney(person.getAmtToPay()) + '\n'
			elif person.getAmtToReceive() != 0:
				display += person.getFirstName() + ' needs to receive $' + formatMoney(person.getAmtToReceive()) + '\n'
		return display
		
	
		
	
	
class Person:
	def __init__(self, userId, first_name):
		self.__userId = userId
		self.__firstName = first_name
		
		self.__amtSpent = 0
		self.__amtPaid = 0
		self.__amtToPay = 0
		self.__amtToReceive = 0
		
		self.__iouListOwned = {}
	
	def addNewIou(self, iouMsgIdf, iou):
		self.__iouListOwned.update({iouMsgIdf:iou})
		
	def increaseAmtSpent(self, amount):
		self.__amtSpent += amount
		
	def editAmtSpent(self, amount):
		self.__amtSpent = amount
		
	def setAmtToPay(self, amount):
		self.__amtToPay = amount
		
	def setAmtToReceive(self, amount):
		self.__amtToReceive = amount
		
	def getUserId(self):
		return self.__userId
		
	def getFirstName(self):
		return self.__firstName
		
	def getAmtSpent(self):
		return self.__amtSpent
		
	def getAmtPaid(self):
		return self.__amtPaid
		
	def getAmtToPay(self):
		return self.__amtToPay
		
	def getAmtToReceive(self):
		return self.__amtToReceive

	
bot = telepot.Bot('438370426:AAG3pe5fwtKN42TqnTel3WZ-QU4LqDP0Wos')

MessageLoop(bot, {'chat': on_chat_message,
				  'callback_query': on_callback_query}).run_as_thread()
print('Listening ...')

#Keep the program running
while 1:
	time.sleep(10)