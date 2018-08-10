import telebot
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup
from telebot.types import ReplyKeyboardRemove
from telebot.types import KeyboardButton
import database as db
from enum import IntEnum
import localizationdic as ld
from datetime import datetime
from datetime import timedelta
import time
import threading

class RequestSteps(IntEnum):
    Start = 0
    EnterCurrency = 1
    EnterQuantity = 2
    EnterFeeType = 3
    EnterFee = 4
    EnterBank = 5
    EnterEndDate = 6
    ChangeCurrency = 7
    ChangeQuantity = 8
    ChangeFeeType = 9
    ChangeFee = 10    
    ChangeBank = 11
    ChangeEndDate = 12
    VoteUser = 13
    UnvoteUser = 14

class FeeTypes(IntEnum):
    Nobody = 0
    Seller = 1
    Buyer = 2

class UserRequestProcess:
    __reqType: db.RequestType
    __quantity: str
    __currency: str
    __feeType: FeeTypes
    __fee: float
    __bank: str
    __daysQuantity: int
    __reqIdForUpdate: int
    __startDate: datetime
    __endDate: datetime
    __currentPage: int
    __startMsgId: int
    __processMsgId: int
    __unvoteMsgId: int
    __allReqMsgIds: list
    __isKeyboardActive: bool

    def __init__(self, bot: telebot.TeleBot, db: db.DB, username, chatId):
        self.username = username
        self.currentStep = RequestSteps.Start
        self.__bot = bot
        self.__db = db
        self.__chatId = chatId
        self.__startMsgId = -1
        self.__processMsgId = -1
        self.__unvoteMsgId = -1
        self.__allReqMsgIds = []
        self.__feeType = -1
        self.__currentPage = 0
        self.__isKeyboardActive = False

    def Start(self):
        self.currentStep = RequestSteps.Start
        self.__currentPage = 0
        self.__deleteAllReqKeyboard()
        isNotifEnabled = self.__db.IsNotificationsRowExistForUser(self.username)
        keyboard = InlineKeyboardMarkup(row_width=5)
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.BuyKey), callback_data=ld.BuyKey), InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SellKey), callback_data=ld.SellKey))
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.ShowMyReqKey), callback_data=ld.ShowMyReqKey), InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.ShowAllReqKey), callback_data=ld.ShowAllReqKey))
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.VoteKey), callback_data=ld.VoteKey), InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.UnvoteKey), callback_data=ld.UnvoteKey), InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.EscrowListKey), callback_data=ld.EscrowListKey))
        btnCallbackData = ld.DisableNotifKey if isNotifEnabled else ld.EnableNotifKey
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, btnCallbackData), callback_data=btnCallbackData))
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.EnglishKey), callback_data=ld.EnglishKey), InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.RussianKey), callback_data=ld.RussianKey))
        self.__deleteStartMessage()
        reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.StartMessageKey), parse_mode="HTML", reply_markup=keyboard)
        self.__startMsgId = reply.message_id

    def ProcessMessage(self, msg):
        switcher = {
            RequestSteps.Start: self.__ProcessStartState,
            RequestSteps.EnterCurrency: self.__ProcessEnterCurrency,
            RequestSteps.EnterQuantity: self.__ProcessEnterQuantity,
            RequestSteps.EnterFeeType: self.__ProcessFeeType,
            RequestSteps.EnterFee: self.__ProcessFee,
            RequestSteps.EnterBank: self.__ProcessBank,
            RequestSteps.EnterEndDate: self.__ProcessEndDate,
            RequestSteps.ChangeCurrency: self.__ProcessChangeCurrency,
            RequestSteps.ChangeQuantity: self.__ProcessChangeQuantity,
            RequestSteps.ChangeFeeType: self.__ProcessChangeFeeType,
            RequestSteps.ChangeFee: self.__ProcessChangeFee,
            RequestSteps.ChangeBank: self.__ProcessChangeBank,
            RequestSteps.ChangeEndDate: self.__ProcessChangeEndDate,
            RequestSteps.VoteUser: self.__ProcessVote,
            RequestSteps.UnvoteUser: self.__ProcessUnvote
        }

        handler = switcher[self.currentStep]
        handler(msg)

    def __ProcessStartState(self, msg: str):
        self.__deleteAllReqMessages()
        if msg == ld.SellKey:
            print(self.username + " Sell")
            self.__deleteAllReqKeyboard()
            self.__reqType = db.RequestType.Sell
            self.currentStep = RequestSteps.EnterCurrency
            self.__deleteStartMessage()
            assets = self.__db.GetAssetsList()
            keyboard = self.__GetMarkupForAssetList(assets)
            reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.SellingMsgKey), parse_mode="HTML", reply_markup=keyboard)
            self.__processMsgId = reply.message_id
        elif msg == ld.BuyKey:
            print(self.username + " Buy")
            self.__deleteAllReqKeyboard()
            self.__reqType = db.RequestType.Buy
            self.currentStep = RequestSteps.EnterCurrency
            self.__deleteStartMessage()
            assets = self.__db.GetAssetsList()
            keyboard = self.__GetMarkupForAssetList(assets)
            reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.BuyingMsgKey), parse_mode="HTML", reply_markup=keyboard)
            self.__processMsgId = reply.message_id
        elif ld.RemoveKey in msg:
            parseResult = self.__ParseReqId(msg)
            if not parseResult[0]:
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.RemoveErrorKey))
                return
            else:
                print(self.username + " are removing request #" + str(parseResult[1]))
                self.__db.DeleteReqWithId(parseResult[1])
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.RemoveSuccessKey).format(parseResult[1]))
        elif ld.ChangeKey in msg:
            parseResult = self.__ParseReqId(msg)
            if not parseResult[0]:
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.ChangeErrorKey))
                return
            else:
                print(self.username + " are changing request #" + str(parseResult[1]))
                self.currentStep = RequestSteps.ChangeCurrency
                self.__reqIdForUpdate = parseResult[1]
                req = self.__db.GetRawRequest(parseResult[1])
                self.__reqType = db.RequestType(req[2])
                self.__quantity = str(req[3])
                self.__currency = req[4]
                self.__fee = float(req[6])
                self.__bank = req[5]
                self.__startDate = datetime.strptime(req[7], "%d.%m.%Y")
                self.__endDate = datetime.strptime(req[8], "%d.%m.%Y")
                self.__daysQuantity = (self.__endDate - self.__startDate).days
                self.__deleteStartMessage()
                assets = self.__db.GetAssetsList()
                keyboard = self.__GetMarkupForAssetList(assets, True)
                reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.ChangingMsgKey), parse_mode="HTML", reply_markup=keyboard)
                self.__processMsgId = reply.message_id
        elif msg == ld.ShowMyReqKey:
            print(self.username + " are browsing his requests")
            self.__deleteAllReqKeyboard()
            self.__ProcessShowMy()
        elif msg == ld.ShowAllReqKey:
            print(self.username + " are browsing all requests")
            self.__currentPage = 1
            self.__ProcessShowAll(self.__currentPage)
        elif msg == "➡️":
            self.__currentPage += 1
            self.__ProcessShowAll(self.__currentPage)
        elif msg == "⬅️":
            self.__currentPage -= 1
            if (self.__currentPage < 1):
                self.__currentPage = 1
            self.__ProcessShowAll(self.__currentPage)
        elif msg == ld.VoteKey:
            self.__deleteAllReqKeyboard()
            if (db.DB.MaxVotes - self.__db.GetVotesCount(self.username)) <= 0:
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.ZeroVotesKey))
                return
            self.currentStep = RequestSteps.VoteUser
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey))
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.VotingMsgKey), parse_mode="HTML", reply_markup=keyboard)
        elif msg == ld.UnvoteKey:
            self.__deleteAllReqKeyboard()
            votedUsersList = self.__db.GetMyVotedUsers(self.username)
            if len(votedUsersList) == 0:
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.VoteListEmptyKey))
                return
            self.currentStep = RequestSteps.UnvoteUser
            reply = self.__bot.send_message(self.__chatId, "<b>{0}</b>".format(ld.get_translate(self.__db, self.username, ld.UnvoteKey)), 
                parse_mode="HTML", reply_markup=self.__GetMarkupForUnvote(votedUsersList))
            self.__unvoteMsgId = reply.message_id
        elif msg == ld.EscrowListKey:
            self.__deleteAllReqKeyboard()
            escrowList = self.__db.GetEscrowList()
            if len(escrowList) == 0:
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EmptyKey))
                return
            result = "\n".join(escrowList)
            self.__bot.send_message(self.__chatId, result, parse_mode="HTML")
        elif msg == ld.DisableNotifKey:
            self.__deleteAllReqKeyboard()
            print(self.username + " has been disabled notifications")
            self.__db.DeleteUserFromNotifications(self.username)
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.NotificationsDisabledKey))
            self.Start()
        elif msg == ld.EnableNotifKey:
            self.__deleteAllReqKeyboard()
            print(self.username + " has been enabled notifications")
            if not self.__db.IsNotificationsRowExistForUser(self.username):
                self.__db.AddUserForNotifications(self.username, self.__chatId)
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.NotificationsEnabledKey))
            self.Start()
        elif msg == ld.EnglishKey:
            self.__deleteAllReqKeyboard()
            self.__db.SetUserLanguage(self.username, ld.Languages.English)
            self.Start()
        elif msg == ld.RussianKey:
            self.__deleteAllReqKeyboard()
            self.__db.SetUserLanguage(self.username, ld.Languages.Russian)
            self.Start()
        elif msg.startswith(ld.AcceptBuyRequestKey) or msg.startswith(ld.AcceptSellRequestKey):
            try:
                msg = msg.replace(ld.AcceptBuyRequestKey, "")
                reqNum = int(msg.replace(ld.AcceptSellRequestKey, ""))
                if self.__db.IsRequestProcessing(reqNum):
                    self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.RequestAlreadyAcceptedKey))
                    return
                req = self.__db.GetRawRequest(reqNum)
                reqType = db.RequestType(req[2])
                buyer = self.username if reqType == db.RequestType.Sell else req[1]
                seller = req[1] if reqType == db.RequestType.Sell else self.username
                self.__db.AddProcessingRequest(reqNum, seller, buyer)
                reqUserChatId = self.__db.GetUserChatId(req[1])
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.AcceptKey), callback_data="{0}{1}".format(ld.AcceptKey, reqNum)))
                print("{0}({1}) sent accept message to user {2}({3})".format(self.username, self.__chatId, req[1], reqUserChatId))
                self.__bot.send_message(reqUserChatId, ld.get_translate(self.__db, req[1], ld.RequestWasAcceptedKey).format(reqNum, self.username), reply_markup=keyboard)
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.RequestWasSentKey))
                self.__StartRequestAcceptTimer(reqNum)
            except Exception as ex:
                print("Exception during accepting request: " + str(ex))

        elif msg.startswith(ld.AcceptKey):
            try:                
                print("{0} trying to accept request {1}".format(self.username, msg))
                reqNum = int(msg.replace(ld.AcceptKey, ""))
                processingReq = self.__db.GetProcessingRequest(reqNum)
                if len(processingReq) == 0:
                    print("Request is no longer exists")
                    self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.AcceptRequestNoLongerActiveKey))
                    return
                seller = processingReq[1]
                buyer = processingReq[2]
                sellerChatId = self.__db.GetUserChatId(seller)
                buyerChatId = self.__db.GetUserChatId(buyer)
                print("Send Finish Accept message to user {0}, chatId {1}".format(seller, sellerChatId))
                self.__bot.send_message(sellerChatId, ld.get_translate(self.__db, seller, ld.RequestHasBeenAcceptedBothSidesKey).format(reqNum, buyer))
                print("Send Finish Accept message to user {0}, chatId {1}".format(buyer, buyerChatId))
                self.__bot.send_message(buyerChatId, ld.get_translate(self.__db, buyer, ld.RequestHasBeenAcceptedBothSidesKey).format(reqNum, seller))
                self.__DeleteProcessingRequest(reqNum)
                self.__db.DeleteReqWithId(reqNum)
            except:
                print("Exception during accepting request")

    def __ProcessEnterCurrency(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled {0} process".format(self.__reqType.name))
            self.__deleteProcessMessage()
            self.Start()
            return
        assets = self.__db.GetAssetsList()
        if msg not in assets:
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.WrongInputKey))
            return
        self.__currency = msg
        self.currentStep = RequestSteps.EnterQuantity
        self.__deleteProcessMessage()
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey))        
        reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EnterQuantityMsgKey), reply_markup=keyboard)
        self.__processMsgId = reply.message_id

    def __ProcessEnterQuantity(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled {0} process".format(self.__reqType.name))
            self.__deleteProcessMessage()
            self.Start()
            return
        try:
            parsedValue = self.__GetNumberFromString(msg)
            if not parsedValue:
                raise Exception("Parsing error!")
            self.__quantity = parsedValue
            self.currentStep = RequestSteps.EnterFeeType
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SellerKey), callback_data=ld.SellerKey),
                         InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.BuyerKey), callback_data=ld.BuyerKey))
            keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.NobodyKey), callback_data=ld.NobodyKey))
            keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey))
            reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.SelectWhoPayFee), reply_markup=keyboard)
            self.__processMsgId = reply.message_id
        except:
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.WrongInputKey))

    def __ProcessFeeType(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled {0} process".format(self.__reqType.name))
            self.__deleteProcessMessage()
            self.Start()
            return
        self.__feeType = FeeTypes.Nobody
        if msg == ld.SellerKey:
            self.__feeType = FeeTypes.Seller
        elif msg == ld.BuyerKey:
            self.__feeType = FeeTypes.Buyer
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey))
        if self.__feeType == FeeTypes.Nobody:
            self.__fee = 0.0
            self.currentStep = RequestSteps.EnterBank
            reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EnterBankNameKey), reply_markup=keyboard)
            self.__processMsgId = reply.message_id
        else:
            self.currentStep = RequestSteps.EnterFee
            reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EnterFeeMsgKey), reply_markup=keyboard)
            self.__processMsgId = reply.message_id

    def __ProcessFee(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled {0} process".format(self.__reqType.name))
            self.__deleteProcessMessage()
            self.Start()
            return
        try:
            self.__fee = float(msg)
            self.currentStep = RequestSteps.EnterBank
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey))
            reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EnterBankNameKey), reply_markup=keyboard)
            self.__processMsgId = reply.message_id
        except:
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.WrongInputKey))

    def __ProcessBank(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled {0} process".format(self.__reqType.name))
            self.__deleteProcessMessage()
            self.Start()
            return
        self.__bank = self.__StripTagsRegex(msg)
        if len(self.__bank) == 0:
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.WrongInputKey))
            return
        self.currentStep = RequestSteps.EnterEndDate
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey))
        self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EnterReqDurationKey), reply_markup=keyboard)

    def __ProcessEndDate(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled {0} process".format(self.__reqType.name))
            self.__deleteProcessMessage()
            self.Start()
            return
        try:
            self.__daysQuantity = int(msg)
            now = datetime.now()
            delta = timedelta(days=self.__daysQuantity, hours=0, minutes=0)
            if self.__feeType == FeeTypes.Seller and self.__fee > 0.0:
                self.__fee = -self.__fee
            reqId = self.__db.AddRequest(self.username, self.__reqType, self.__quantity, self.__currency, self.__bank, self.__fee, now, now + delta)
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.SuccessfulRequestKey))
            self.Start()
            reqStr = self.__db.GetRequest(reqId, self.username)
            self.__SendNotifications(ld.get_translate(self.__db, self.username, ld.NewReqNotifKey).format(reqStr))
        except Exception as ex:
            print(ex)
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.WrongInputKey))

    def __ProcessChangeCurrency(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled changing request process")
            self.__deleteProcessMessage()
            self.Start()
            return
        if not (msg == ld.SkipKey):
            assets = self.__db.GetAssetsList()
            if msg not in assets:
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.WrongInputKey))
                return
            self.__currency = msg

        self.__deleteProcessMessage()
        self.currentStep = RequestSteps.ChangeQuantity
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey), 
                     InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SkipKey), callback_data=ld.SkipKey))
        reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EnterQuantityMsgKey), reply_markup=keyboard)
        self.__processMsgId = reply.message_id

    def __ProcessChangeQuantity(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled changing request process")
            self.__deleteProcessMessage()
            self.Start()
            return
        if not (msg == ld.SkipKey):
            try:
                parsedValue = self.__GetNumberFromString(msg)
                if not parsedValue:
                    raise Exception("Parsing error!")
                self.__quantity = parsedValue
            except:
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.WrongInputKey))
                return

        self.__deleteProcessMessage()
        self.currentStep = RequestSteps.ChangeFeeType
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SellerKey), callback_data=ld.SellerKey),
                     InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.BuyerKey), callback_data=ld.BuyerKey))
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.NobodyKey), callback_data=ld.NobodyKey))
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey), 
                     InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SkipKey), callback_data=ld.SkipKey))
        reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.SelectWhoPayFee), reply_markup=keyboard)
        self.__processMsgId = reply.message_id

    def __ProcessChangeFeeType(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled changing request process")
            self.__deleteProcessMessage()
            self.Start()
            return
        if not (msg == ld.SkipKey):
            self.__feeType = FeeTypes.Nobody
            if msg == ld.SellerKey:
                self.__feeType = FeeTypes.Seller
            elif msg == ld.BuyerKey:
                self.__feeType = FeeTypes.Buyer

        self.__deleteProcessMessage()
        keyboard = InlineKeyboardMarkup(row_width=1)
        msg = ld.get_translate(self.__db, self.username, ld.EnterFeeMsgKey)
        if self.__feeType == FeeTypes.Nobody or self.__feeType == -1:
            if self.__feeType == FeeTypes.Nobody:
                self.__fee = 0.0
            self.currentStep = RequestSteps.ChangeBank
            msg = ld.get_translate(self.__db, self.username, ld.EnterBankNameKey)
        else:
            self.currentStep = RequestSteps.ChangeFee
        
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey), 
                     InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SkipKey), callback_data=ld.SkipKey))
        reply = self.__bot.send_message(self.__chatId, msg, reply_markup=keyboard)
        self.__processMsgId = reply.message_id

    def __ProcessChangeFee(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled changing request process")
            self.__deleteProcessMessage()
            self.Start()
            return
        if not (msg == ld.SkipKey):
            try:
                self.__fee = float(msg)
            except:
                self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.WrongInputKey))
                return

        self.__deleteProcessMessage()
        self.currentStep = RequestSteps.ChangeBank
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey), 
                     InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SkipKey), callback_data=ld.SkipKey))
        reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EnterBankNameKey), reply_markup=keyboard)
        self.__processMsgId = reply.message_id

    def __ProcessChangeBank(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled changing request process")
            self.__deleteProcessMessage()
            self.Start()
            return
        if not (msg == ld.SkipKey):
            self.__bank = self.__StripTagsRegex(msg)

        self.currentStep = RequestSteps.ChangeEndDate
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey), 
                     InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SkipKey), callback_data=ld.SkipKey))
        reply = self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EnterReqDurationKey), reply_markup=keyboard)
        self.__processMsgId = reply.message_id

    def __ProcessChangeEndDate(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled changing request process")
            self.__deleteProcessMessage()
            self.Start()
            return
        if not (msg == ld.SkipKey):
            try:
                self.__daysQuantity = int(msg)
            except:
                self.__daysQuantity = -1

        self.__deleteProcessMessage()
        if self.__daysQuantity > 0:
            now = datetime.now()
            self.__startDate = now
            self.__endDate = now + timedelta(days=self.__daysQuantity)
        if self.__feeType >= 0:
            if (self.__feeType == FeeTypes.Seller and self.__fee > 0.0) or (self.__feeType == FeeTypes.Buyer and self.__fee < 0.0):
                self.__fee = -self.__fee
            elif self.__feeType == FeeTypes.Nobody:
                self.__fee = 0.0
        self.__db.UpdateRequest(self.__reqIdForUpdate, self.username, self.__quantity, self.__currency, self.__bank, self.__fee, self.__startDate, self.__endDate)
        self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.SuccessfulChangeKey))
        self.Start()
        reqStr = self.__db.GetRequest(self.__reqIdForUpdate, self.username)
        self.__SendNotifications(ld.get_translate(self.__db, self.username, ld.ChangedReqNotifKey).format(reqStr))

    def __ProcessVote(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled {0} process".format(self.currentStep.name))
            self.Start()
            return
        votedUser = msg.strip('"').lstrip('@')
        if not self.__db.IsUserRegistered(votedUser):
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.VotedUserNotRegisteredKey).format(votedUser))
            return
        if self.__db.IsAlreadyVotedByUser(self.username, votedUser):
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.VotedUserAlreadyVotedKey).format(votedUser))
            return
        if self.username == votedUser:
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.VotedUserIsMySelfKey))
            return
        self.__db.Vote(self.username, votedUser)
        voteCount = self.__db.GetVotesCount(self.username)
        self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.VoteSuccessfulKey).format(votedUser, db.DB.MaxVotes - voteCount))
        self.Start()

    def __ProcessUnvote(self, msg: str):
        if msg == ld.CancelKey or msg == "/start":
            print(self.username + " has been cancelled {0} process".format(self.currentStep.name))
            self.__bot.delete_message(self.__chatId, self.__unvoteMsgId)
            self.Start()
            return
        votedUser = msg.lstrip('@')
        self.__db.Unvote(self.username, votedUser)
        voteCount = self.__db.GetVotesCount(self.username)
        self.__bot.delete_message(self.__chatId, self.__unvoteMsgId)
        self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.UnvoteSuccessfulKey).format(votedUser, db.DB.MaxVotes - voteCount))
        self.Start()

    def __SendNotifications(self, message:str):
        forNotif = self.__db.GetUserlistForNotifications(self.username)
        for chatId in forNotif:
            try:
                self.__bot.send_message(chatId, message, parse_mode="HTML")
            except Exception as ex:
                print("Exception during send notification: " + str(ex))

    def __GetMarkupForAssetList(self, assetsList: list, withSkipBtn: bool = False):
        assetsCount = len(assetsList)
        rowsCount = assetsCount//5
        if assetsCount%5 > 0:
            rowsCount += 1        
        keyboard = InlineKeyboardMarkup(row_width=rowsCount+1)
        buttons = [InlineKeyboardButton(a, callback_data=a) for a in assetsList]
        keyboard.add(*buttons)
        secondaryButtons = [InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey)]
        if withSkipBtn:
            secondaryButtons.append(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.SkipKey), callback_data=ld.SkipKey))
        keyboard.row(*secondaryButtons)
        return keyboard

    def __GetMarkupForUnvote(self, usernameList: list):
        keyboard = InlineKeyboardMarkup(row_width=len(usernameList)+1)
        for username in usernameList:
            keyboard.row(InlineKeyboardButton(username, callback_data=username))
        keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, ld.CancelKey), callback_data=ld.CancelKey))
        return keyboard

    def __ProcessShowMy(self):
        myReqs = self.__db.GetRequestsFor(self.username, self.username)
        if len(myReqs) == 0:
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EmptyKey))
            return
        for req in myReqs:
            idx1 = req.find('(')
            idx2 = req.find(')')
            if idx1 < 0 or idx2 < 0:
                continue
            reqId = req[idx1:idx2+1]
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.row(InlineKeyboardButton("{0} {1}".format(ld.get_translate(self.__db, self.username, ld.RemoveKey), reqId), callback_data="{0} {1}".format(ld.RemoveKey, reqId)), 
                         InlineKeyboardButton("{0} {1}".format(ld.get_translate(self.__db, self.username, ld.ChangeKey), reqId), callback_data="{0} {1}".format(ld.ChangeKey, reqId)))
            self.__bot.send_message(self.__chatId, req, parse_mode="HTML", reply_markup=keyboard)

    def __ProcessShowAll(self, pageNumber: int):
        limit = 5
        offset = limit*(pageNumber - 1)
        allReqs = self.__db.GetAllRequests(self.username, offset, limit)
        if len(allReqs) == 0:
            self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.EmptyKey))
            return
        for req in allReqs:
            keyboard = InlineKeyboardMarkup(row_width=1)
            buttonTextKey = ld.AcceptSellRequestKey if db.RequestType(req[2]) == db.RequestType.Sell else ld.AcceptBuyRequestKey
            keyboard.row(InlineKeyboardButton(ld.get_translate(self.__db, self.username, buttonTextKey), callback_data="{0}{1}".format(buttonTextKey, req[0])))
            formattedReq = self.__getFormattedRequest(req)
            if str(req[1]) == self.username:
                keyboard = None
            reply = self.__bot.send_message(self.__chatId, formattedReq, parse_mode="HTML", reply_markup=keyboard)
            self.__allReqMsgIds.append(reply.message_id)
        reqCount = self.__db.GetAllRequestsCount()
        showPrevButton = pageNumber > 1
        showNextButton = (reqCount - (limit + limit*(pageNumber - 1))) > 0

        keyboard = None
        if showNextButton or showPrevButton:
            keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            buttons = []
            if showPrevButton:
                buttons.append(KeyboardButton("⬅️"))
            if showNextButton:
                buttons.append(KeyboardButton("➡️"))
            keyboard.add(*buttons)
            self.__isKeyboardActive = True
        maxPageNumber = reqCount//limit
        if reqCount%limit > 0:
            maxPageNumber += 1
        reply = self.__bot.send_message(self.__chatId, "Page {0} of {1}".format(pageNumber, maxPageNumber), parse_mode="HTML", reply_markup=keyboard)
        self.__allReqMsgIds.append(reply.message_id)
    
    def __getFormattedRequest(self, req: tuple):
        number = req[0]
        username = req[1]
        reqType = self.__getLocalizedRequestType(db.RequestType(req[2]), self.username)
        quantity = req[3]
        currency = req[4]
        fee = str(req[6]).replace(",", ".")
        bank = req[5]
        startDate = req[7]
        endDate = req[8]
        whoPayFee = ""
        if float(fee) > 0:
            whoPayFee = ld.get_translate(self.__db, self.username, ld.FeePayBuyerKey)
        elif float(fee) < 0:
            whoPayFee = ld.get_translate(self.__db, self.username, ld.FeePaySellerKey)
        req = ld.get_translate(self.__db, self.username, ld.RequestResultStringTemplate).format(number, username, reqType, quantity, currency, fee, whoPayFee, bank, startDate, endDate)
        return req

    def __getLocalizedRequestType(self, reqType: db.RequestType, callUser):
        if reqType == db.RequestType.Buy:
            return ld.get_translate(self.__db, callUser, ld.BuyKey).lower()
        else:
            return ld.get_translate(self.__db, callUser, ld.SellKey).lower()

    def __deleteProcessMessage(self):
        if self.__processMsgId > 0:
            try:
                self.__bot.delete_message(self.__chatId, self.__processMsgId)
                self.__processMsgId = -1
            except Exception as ex:
                print("Exception during delete process message. Error: " + str(ex))

    def __deleteStartMessage(self):
        if self.__startMsgId > 0:
            try:
                self.__bot.delete_message(self.__chatId, self.__startMsgId)
                self.__startMsgId = -1
            except Exception as ex:
                print("Exception during delete start message. Error: " + str(ex))

    def __deleteAllReqMessages(self):
        if len(self.__allReqMsgIds) > 0:
            for msgId in self.__allReqMsgIds:
                try:
                    self.__bot.delete_message(self.__chatId, msgId)
                except Exception as ex:
                    print("Exception during delete all requests message. Error: " + str(ex))
            self.__allReqMsgIds.clear()

    def __deleteAllReqKeyboard(self):
        if not self.__isKeyboardActive:
            return
        try:
            deleteMarkup = ReplyKeyboardRemove()
            self.__bot.send_message(self.__chatId, "❌", reply_markup=deleteMarkup)
            self.__isKeyboardActive = False
        except:
            print("Exception during remove keyboard.")

    def __ParseReqId(self, msg: str):
        idx1 = msg.find('(')
        idx2 = msg.find(')')
        if idx1 < 0 or idx2 < 0:
            return (False, 0)
        substr = msg[idx1 + 1:idx2]
        try:
            reqId = int(substr)
            return (True, reqId)
        except:
            return (False, 0)

    def __StripTagsRegex(self, source):
        import re
        return re.sub("<.*?>", "", source)

    def __GetNumberFromString(self, source):
        import re
        result = re.findall("([0-9]*[.,][0-9]+|[0-9]+)", source)
        if len(result)>0:
            return result[0]
        return None

    def __StartRequestAcceptTimer(self, reqId):
        threading.Timer(300, lambda: self.__AutoDeleteProcessingRequest(reqId)).start()

    def __AutoDeleteProcessingRequest(self, reqId):
        self.__bot.send_message(self.__chatId, ld.get_translate(self.__db, self.username, ld.AcceptRequestHasBeenAutoCancelledKey))
        self.__DeleteProcessingRequest(reqId)

    def __DeleteProcessingRequest(self, reqId):
        print("Processing request #{0} was deleted".format(reqId))
        self.__db.DeleteProcessingRequest(reqId)