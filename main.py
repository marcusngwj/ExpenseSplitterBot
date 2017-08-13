import sys
import time
import threading
import math
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ForceReply


iouMap = {}			#Map iou to respective message_identifier (iouMsgIdf:iou)
userMap = {}		#Map user to userid (userId:person)


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
			
		if person.getCurrentActionType() != None:
			responseToCallback(person, textFromUser)
			

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
		signalCallback_addExpense(person, queryData, iouMsgIdf)
		
	if queryData == 'editExpense':
		signalCallback_editExpense(person, queryData, iouMsgIdf)								
		
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
	iou = createNewIou(person, chatId)
	putIouInWallet(person, iou)
	
	
def createNewIou(person, chatId):
	iou = Iou(person.getUserId(), chatId)
	newIouDisplayText = "A new IOU has been created\n" + iou.getInstructionalText()
	iouMsg = bot.sendMessage(chatId, newIouDisplayText, reply_markup=getPublicKeyboard())
	iou.setIouMsgIdf(telepot.message_identifier(iouMsg))
	iouMap.update({iou.getIouMsgIdf():iou})
	return iou
	
def putIouInWallet(person, iou):
	wallet = Wallet(iou)
	person.addWallet(iou.getIouMsgIdf(), wallet)
	return wallet

		
def signalCallback_addExpense(person, queryData, iouMsgIdf):
	actionType = queryData
	walletIdf = iouMsgIdf
	
	if not person.hasWallet(walletIdf):
		wallet = Wallet(iouMap[iouMsgIdf])
		person.addWallet(walletIdf, wallet)
	
	walletInUse = person.getWallet(walletIdf)
		
	person.setWalletInUse(walletInUse)
	person.setCurrentActionType(actionType)
	
	iouInUse = walletInUse.getIou()
	
	if person.getUserId() not in iouInUse.getSpenderList():
		iouInUse.addSpender(person)
	
	bot.sendMessage(person.getUserId(), 'Send me the amount you spent.')
	
def signalCallback_editExpense(person, queryData, iouMsgIdf):
	actionType = queryData
	walletIdf = iouMsgIdf
	
	if not person.hasWallet(walletIdf):
		wallet = Wallet(iouMap[iouMsgIdf])
		person.addWallet(walletIdf, wallet)
	
	walletInUse = person.getWallet(walletIdf)
		
	person.setWalletInUse(walletInUse)
	person.setCurrentActionType(actionType)
	
	iouInUse = walletInUse.getIou()
	
	if person.getUserId() not in iouInUse.getSpenderList():
		iouInUse.addSpender(person)
	
	if walletInUse.getAmtSpent() == 0:
		bot.sendMessage(person.getUserId(), 'You have not spend any money so far.\nSend me the amount you spent.')
	else:
		expenseEditionMsg = ('You previously declared that you spent $' + formatMoney(walletInUse.getAmtSpent()) + '.\n'
							'This amount will be deleted.\n'
							'Send me the new amount.')
		bot.sendMessage(person.getUserId(), expenseEditionMsg)

	
def responseToCallback(person, textFromUser):
	actionType = person.getCurrentActionType()
	
	if actionType == 'addExpense':
		responseToCallback_addExpense(person, textFromUser)
	
	if actionType == 'editExpense':
		responseToCallback_editExpense(person, textFromUser)

def responseToCallback_addExpense(person, textFromUser):
	userId = person.getUserId()
	walletInUse = person.getWalletInUse()
	iou = walletInUse.getIou()
	
	if not isNonNegativeFloat(textFromUser):
		bot.sendMessage(userId, 'Please enter a valid amount')
	else:
		walletInUse.increaseAmtSpent(float(textFromUser))		
		updateDisplay(iou)
		totalAmtSpentFeedback = 'You have spent a total of $' + formatMoney(walletInUse.getAmtSpent())
		bot.sendMessage(userId, totalAmtSpentFeedback)
		killPersonCurrentAction(person)
		

def responseToCallback_editExpense(person, textFromUser):
	userId = person.getUserId()
	walletInUse = person.getWalletInUse()
	iou = walletInUse.getIou()
	
	if not isNonNegativeFloat(textFromUser):
		bot.sendMessage(userId, 'Please enter a valid amount')
	else:
		walletInUse.editAmtSpent(float(textFromUser))
		updateDisplay(iou)
		totalAmtSpentFeedback = 'You have spent a total of $' + formatMoney(walletInUse.getAmtSpent())
		bot.sendMessage(userId, totalAmtSpentFeedback)
		killPersonCurrentAction(person)
		

def killPersonCurrentAction(person):
	person.setWalletInUse(None)
	person.setCurrentActionType(None)
		

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
		totalExpenses = 0
		
		for userId, person in self.__spenderList.items():
			wallet = self.__getWalletFromPerson(person)
			totalExpenses += wallet.getAmtSpent()
		return totalExpenses
	
	#Compute amount a person supposed to pay
	def __computeExpectedAmtToPay(self):
		totalAmtSpent = self.__computeTotalExpenses()
		numSpender = self.__getNumSpenders()
		return totalAmtSpent/numSpender
		
	def __computeReceivePay(self):
		expectedAmtToPay = self.__computeExpectedAmtToPay()
		for userId, person in self.__spenderList.items():
			self.__resetAmtToReceivePay(person)
			wallet = self.__getWalletFromPerson(person)
			shortfallAmt = expectedAmtToPay - wallet.getAmtSpent()
			if shortfallAmt > 0:
				wallet.setAmtToPay(shortfallAmt)
			else:
				wallet.setAmtToReceive((-1)*shortfallAmt)
				
	def __resetAmtToReceivePay(self, person):
		wallet = self.__getWalletFromPerson(person)
		wallet.setAmtToReceive(0)
		wallet.setAmtToPay(0)
				
	def setIouMsgIdf(self, iouMsgIdf):
		self.__iouMsgIdf = iouMsgIdf
		
	def __getWalletFromPerson(self, person):
		walletIdf = self.__iouMsgIdf
		wallet = person.getWallet(walletIdf)
		return wallet
		
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
			wallet = self.__getWalletFromPerson(person)
			amtSpent = wallet.getAmtSpent()
			display += name + ' spent $' + formatMoney(amtSpent) + '\n'
		
		return display
		
	def getDisplayReceivePay(self):
		self.__computeReceivePay()
		display = ''
		for userId, person in self.__spenderList.items():
			wallet = self.__getWalletFromPerson(person)
			if wallet.getAmtToPay() != 0:
				display += person.getFirstName() + ' needs to pay $' + formatMoney(wallet.getAmtToPay()) + '\n'
			elif wallet.getAmtToReceive() != 0:
				display += person.getFirstName() + ' needs to receive $' + formatMoney(wallet.getAmtToReceive()) + '\n'
		return display
		
	
		
	
	
class Person:
	def __init__(self, userId, first_name):
		self.__userId = userId
		self.__firstName = first_name
		
		self.__currentWallet = None
		self.__currentActionType = None
		
		self.__walletList = {}	#(walletIdf: wallet), walletIdf == iouMsgIdf
	
	def addWallet(self, walletIdf, wallet):
		self.__walletList.update({walletIdf:wallet})
		
	def setWalletInUse(self, wallet):
		self.__currentWallet = wallet
		
	def setCurrentActionType(self, service):
		self.__currentActionType = service
		
	def getUserId(self):
		return self.__userId
		
	def getFirstName(self):
		return self.__firstName
		
	def getWallet(self, walletIdf):
		return self.__walletList[walletIdf]
		
	def getWalletInUse(self):
		return self.__currentWallet
	
	def getCurrentActionType(self):
		return self.__currentActionType
		
	def hasWallet(self, walletIdf):
		return walletIdf in self.__walletList





class Wallet:
	def __init__(self, iou):
		self.__iou = iou
		
		self.__amtSpent = 0
		self.__amtPaid = 0
		self.__amtToPay = 0
		self.__amtToReceive = 0
	
	def insertIou(self, iou):
		self.__iou = iou
		
	def increaseAmtSpent(self, amount):
		self.__amtSpent += amount
		
	def editAmtSpent(self, amount):
		self.__amtSpent = amount
		
	def setAmtToPay(self, amount):
		self.__amtToPay = amount
		
	def setAmtToReceive(self, amount):
		self.__amtToReceive = amount
		
	def getIou(self):
		return self.__iou
		
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