import sqlite3
from datetime import datetime
from enum import IntEnum
import localizationdic as ld
import config
import threading

DBFileName = "db.sqlite"

lock = threading.Lock()

class RequestType(IntEnum):
    Buy = 0
    Sell = 1

class DB:

    MaxVotes = 5
    EscrowListTemplate = "@{0} - <b>{1}</b>"

    def __init__(self):
        self.conn = sqlite3.connect(DBFileName, check_same_thread=False)
        self.cur = self.conn.cursor()
        sql = """CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, requestType INTEGER, quantity INTEGER, currency TEXT, bankName TEXT, fee REAL, startDate TEXT, endDate TEXT);
                 CREATE TABLE IF NOT EXISTS notifications (username TEXT, chatId INTEGER);
                 CREATE TABLE IF NOT EXISTS masterchat (chatId INTEGER);
                 CREATE TABLE IF NOT EXISTS users (username TEXT);
                 CREATE TABLE IF NOT EXISTS users_votes (username TEXT, votedUser TEXT);
                 CREATE TABLE IF NOT EXISTS users_languages (username TEXT, language INTEGER);
                 DROP TABLE IF EXISTS assets;
                 CREATE TABLE IF NOT EXISTS assets (assetName TEXT);
                 CREATE TABLE IF NOT EXISTS additional_assets (assetName TEXT);
                 CREATE TABLE IF NOT EXISTS processing_requests (reqId INTEGER, seller TEXT, buyer TEXT);"""
        self.cur.executescript(sql)
        self.__FillAssetsTable()
        self.__AddChatIdColumnToUsersTable()
        self.__BlacklistMigration()
        self.__cleanup_db()

    def GetAssetsList(self):
        try:
            lock.acquire(True)
            sql = "SELECT * FROM assets"
            self.cur.execute(sql)
            rows = self.cur.fetchall()
            assetsList = [r[0] for r in rows]

            sql = "SELECT * FROM additional_assets"
            self.cur.execute(sql)
            rows = self.cur.fetchall()
            addAssetsList = [r[0] for r in rows]

            assetsList.extend(addAssetsList)
            return assetsList
        finally:
            lock.release()

        return []        

    def IsNotificationsRowExistForUser(self, username):
        try:
            lock.acquire(True)
            sql = "SELECT count(*) FROM notifications WHERE username=\"{}\"".format(username)
            self.cur.execute(sql)
            count = self.cur.fetchone()
        finally:
            lock.release()
            return count[0] > 0

    def AddUserForNotifications(self, username, chatId):
        sql = "INSERT INTO notifications(username, chatId) VALUES(\"{0}\",\"{1}\")".format(username, chatId)
        self.cur.execute(sql)
        self.conn.commit()

    def DeleteUserFromNotifications(self, username):
        sql = "DELETE FROM notifications WHERE username=\"{0}\"".format(username)
        self.cur.execute(sql)
        self.conn.commit()

    def GetUserlistForNotifications(self, excludeUser):
        sql = "SELECT chatId FROM notifications WHERE username != \"{0}\"".format(excludeUser)
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        return [r[0] for r in rows]

    def AddRequest(self, username, reqType: RequestType, quantity, currency, bankName, fee, startDate: datetime, endDate: datetime):
        sql = "INSERT INTO requests(username, requestType, quantity, currency, bankName, fee, startDate, endDate) VALUES(\"{0}\",\"{1}\",\"{2}\",\"{3}\",\"{4}\",\"{5}\",\"{6}\",\"{7}\")".format(username, int(reqType), quantity, currency, bankName, fee, startDate.strftime("%d.%m.%Y"), endDate.strftime("%d.%m.%Y"))
        self.cur.execute(sql)
        self.conn.commit()
        sql = "SELECT last_insert_rowid() FROM requests"
        self.cur.execute(sql)
        rowId = self.cur.fetchone()
        return int(rowId[0])

    def GetRequest(self, reqId, callUser):
        sql = "SELECT * FROM requests WHERE id=" + str(reqId)
        results = self.__getResultsForSql(sql, callUser)
        if len(results) > 0:
            return results[0]
        return None

    def GetRawRequest(self, reqId):
        sql = "SELECT * FROM requests WHERE id=" + str(reqId)
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        return tuple(rows[0])

    def GetRequestsFor(self, username, callUser):
        sql = "SELECT * FROM requests WHERE username = \"{0}\"".format(username)
        results = self.__getResultsForSql(sql, callUser)
        return results

    def GetAllRequestsCount(self):
        sql = "SELECT count(*) FROM requests"
        self.cur.execute(sql)
        row = self.cur.fetchone()
        return int(row[0])

    def GetAllRequests(self, callUser, offset: int, limit: int):
        sql = "SELECT * FROM requests ORDER BY id DESC LIMIT {0}, {1}".format(offset, limit)
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        return [tuple(r) for r in rows]

    def GetAllFormattedRequests(self, callUser, offset: int, limit: int):
        sql = "SELECT * FROM requests LIMIT {0}, {1}".format(offset, limit)
        return self.__getResultsForSql(sql, callUser)

    def DeleteReqWithId(self, reqId):
        sql = "DELETE FROM requests WHERE id={0}".format(reqId)
        self.cur.execute(sql)
        self.conn.commit()

    def UpdateRequest(self, reqId, username, quantity, currency, bankName, fee, startDate: datetime, endDate: datetime = None):
        if (not quantity) and (not currency) and (not bankName) and fee < 0.0 and (not endDate):
            return
        updateValues = []
        updateValues.append("fee=" + str(fee))
        updateValues.append("quantity=\"{}\"".format(quantity))
        updateValues.append("currency=\"{}\"".format(currency))
        updateValues.append("bankName=\"{}\"".format(bankName))
        updateValues.append("startDate=\"{}\"".format(startDate.strftime("%d.%m.%Y")))
        updateValues.append("endDate=\"{}\"".format(endDate.strftime("%d.%m.%Y")))
        aggregated = ",".join(updateValues)
        sql = "UPDATE requests SET " + aggregated + " WHERE id=" + str(reqId) + " AND username=\"" + username + "\""
        self.cur.execute(sql)
        self.conn.commit()

    def DeleteOldRequests(self):
        sql = "SELECT id, endDate FROM requests"
        self.cur.execute(sql)
        results = self.cur.fetchall()
        oldRequests = [r[0] for r in results if datetime.now() > datetime.strptime(r[1], "%d.%m.%Y")]
        for reqId in oldRequests:
            sql = "DELETE FROM requests WHERE id=" + str(reqId)
            self.cur.execute(sql)
        self.conn.commit()

    def GetMasterChatId(self):
        sql = "SELECT chatId FROM masterchat"
        self.cur.execute(sql)
        result = self.cur.fetchone()
        if result and len(result) > 0:
            return int(result[0])
        return 0

    def SetMasterChatId(self, chatId):
        sql = "INSERT INTO masterchat(chatId) VALUES({})".format(chatId)
        self.cur.execute(sql)
        self.conn.commit()

    def IsUserRegistered(self, username):
        try:
            lock.acquire(True)
            sql = "SELECT count(*) FROM users WHERE username=\"{}\"".format(username)
            self.cur.execute(sql)
            result = self.cur.fetchone()
        finally:
            lock.release()
            if result[0] == 0:
                self.AddUser(username)
            return True

    def AddUser(self, username):
        sql = "INSERT INTO users(username) VALUES(\"{}\")".format(username)
        self.cur.execute(sql)
        self.conn.commit()

    def DeleteUser(self, username):
        sql = "DELETE FROM users WHERE username=\"{}\"".format(username)
        self.cur.execute(sql)
        sql = "DELETE FROM requests WHERE username=\"{}\"".format(username)
        self.cur.execute(sql)
        sql = "DELETE FROM notifications WHERE username=\"{}\"".format(username)
        self.cur.execute(sql)
        sql = "DELETE FROM users_votes WHERE username=\"{}\"".format(username)
        self.cur.execute(sql)
        sql = "DELETE FROM users_votes WHERE votedUser=\"{}\"".format(username)
        self.cur.execute(sql)
        sql = "DELETE FROM users_languages WHERE username=\"{}\"".format(username)
        self.cur.execute(sql)
        self.conn.commit()

    def UpdateUser(self, username, userId):
        sql = "UPDATE users SET userId={0}, username=\"{1}\" WHERE username=\"{1}\" OR userId={0}".format(userId, username)
        self.cur.execute(sql)
        self.conn.commit()

    def AddUserToBlackListByReqId(self, reqId: int):
        sql = "SELECT username FROM requests WHERE id={0}".format(reqId)
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if len(result) == 0:
            return
        username = str(result[0][0])
        sql = "SELECT userId FROM users WHERE username = \"{0}\"".format(username)
        self.cur.execute(sql)
        result = self.cur.fetchone()
        if result == None or result[0] == None:
            return
        userId = int(result[0])
        if userId == 0:
            return        
        sql = "INSERT OR IGNORE INTO users_blacklist(userId) VALUES({0})".format(userId)
        self.cur.execute(sql)
        self.conn.commit()
        self.DeleteUser(username)

    def IsUserInBlacklist(self, userId):
        try:
            lock.acquire(True)
            sql = "SELECT count(*) FROM users_blacklist WHERE userId={0}".format(userId)
            self.cur.execute(sql)
            count = self.cur.fetchone()
        finally:
            lock.release()
            return count[0] > 0

    def GetVotesCount(self, username):
        sql = "SELECT count(*) FROM users_votes WHERE username = \"{}\"".format(username)
        self.cur.execute(sql)
        result = self.cur.fetchone()
        return result[0]

    def IsAlreadyVotedByUser(self, username, votedUser):
        sql = "SELECT count(*) FROM users_votes WHERE username = \"{0}\" AND votedUser = \"{1}\"".format(username, votedUser)
        self.cur.execute(sql)
        result = self.cur.fetchone()
        return result[0] > 0

    def Vote(self, username, votedUser):
        if not self.IsUserRegistered(username) or self.IsAlreadyVotedByUser(username, votedUser):
            return False
        sql = "INSERT INTO users_votes(username, votedUser) VALUES(\"{0}\",\"{1}\")".format(username, votedUser)
        self.cur.execute(sql)
        self.conn.commit()
        return True

    def Unvote(self, username, votedUser):
        sql = "DELETE FROM users_votes WHERE username = \"{0}\" AND votedUser = \"{1}\"".format(username, votedUser)
        self.cur.execute(sql)
        self.conn.commit()

    def GetMyVotedUsers(self, username):
        sql = "SELECT votedUser FROM users_votes WHERE username = \"{}\"".format(username)
        self.cur.execute(sql)
        result = self.cur.fetchall()
        usersList = [r[0] for r in result]
        return usersList

    def GetEscrowList(self):
        sql = "SELECT votedUser FROM users_votes"
        self.cur.execute(sql)
        result = self.cur.fetchall()
        escrowDic = {}
        for r in result:
            if r[0] in escrowDic:
                escrowDic[r[0]] += 1
            else:
                escrowDic[r[0]] = 1
        sortedDic = sorted(escrowDic.items(), key = lambda x: x[1], reverse = True)
        return [self.EscrowListTemplate.format(v[0], v[1]) for v in sortedDic]

    def GetUserLanguage(self, username):
        sql = "SELECT count(*) FROM users_languages WHERE username=\"{}\"".format(username)
        self.cur.execute(sql)
        result = self.cur.fetchone()
        userLang = ld.DefaultLanguage
        if result[0] > 0:
            sql = "SELECT language FROM users_languages WHERE username = \"{}\"".format(username)
            self.cur.execute(sql)
            result2 = self.cur.fetchone()
            return int(result2[0])
        else:
            sql = "INSERT INTO users_languages(username, language) VALUES(\"{0}\",\"{1}\")".format(username, int(userLang))
            self.cur.execute(sql)
            self.conn.commit()
        return userLang

    def SetUserLanguage(self, username, language):
        sql = "UPDATE users_languages SET language=\"{0}\" WHERE username=\"{1}\"".format(int(language), username)
        self.cur.execute(sql)
        self.conn.commit()

    def SetUserChatId(self, username, chatId):
        sql = "UPDATE users SET chatId={0} WHERE username=\"{1}\"".format(chatId, username)
        self.cur.execute(sql)
        self.conn.commit()

    def GetUserChatId(self, username):
        sql = "SELECT chatId FROM users WHERE username=\"{0}\"".format(username)
        self.cur.execute(sql)
        row = self.cur.fetchone()
        return row[0]

    def IsRequestProcessing(self, reqId):
        sql = "SELECT count(*) FROM processing_requests WHERE reqId={0}".format(reqId)
        self.cur.execute(sql)
        row = self.cur.fetchone()
        return row[0] > 0

    def AddProcessingRequest(self, reqId, seller, buyer):
        sql = "INSERT INTO processing_requests (reqId, seller, buyer) VALUES ({0},\"{1}\",\"{2}\")".format(reqId, seller, buyer)
        self.cur.execute(sql)
        self.conn.commit()

    def GetProcessingRequest(self, reqId):
        sql = "SELECT * FROM processing_requests WHERE reqId={0}".format(reqId)
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        if len(rows) > 0:
            return tuple(rows[0])
        return tuple()

    def DeleteProcessingRequest(self, reqId):
        sql = "DELETE FROM processing_requests WHERE reqId={0}".format(reqId)
        self.cur.execute(sql)
        self.conn.commit()

    def GetUsersCount(self):
        sql = "SELECT count(*) FROM users"
        self.cur.execute(sql)
        row = self.cur.fetchone()
        return row[0]

    def GetUsersCountWithNotifications(self):
        sql = "SELECT count(*) FROM notifications"
        self.cur.execute(sql)
        row = self.cur.fetchone()
        return row[0]

    def __FillAssetsTable(self):
        self.cur.executemany('INSERT INTO assets (assetName) VALUES (?)', config.assets)

    def __AddChatIdColumnToUsersTable(self):
        sql = "PRAGMA table_info('users')"
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if len(result) > 1 and 'chatId' in result[1]:
            return
        sql = "ALTER TABLE users ADD COLUMN chatId INTEGER"
        self.cur.execute(sql)
        self.conn.commit()

    def __BlacklistMigration(self):
        sql = "CREATE TABLE IF NOT EXISTS users_blacklist (userId INTEGER, UNIQUE(userId))"
        self.cur.execute(sql)
        sql = "PRAGMA table_info('users')"
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if len(result) > 1 and 'userId' in result[2]:
            return
        sql = "ALTER TABLE users ADD COLUMN userId INTEGER DEFAULT 0"
        self.cur.execute(sql)
        self.conn.commit()

    def __getResultsForSql(self, sql, callUser):
        self.cur.execute(sql)
        result = self.cur.fetchall()
        results = []

        for r in result:
            number = r[0]
            username = r[1]
            reqType = self.__getLocalizedRequestType(RequestType(r[2]), callUser)
            quantity = r[3]
            currency = r[4]
            fee = str(r[6]).replace(",", ".")
            bank = r[5]
            startDate = r[7]
            endDate = r[8]
            whoPayFee = ""
            if float(fee) > 0:
                whoPayFee = ld.get_translate(self, callUser, ld.FeePayBuyerKey)
            elif float(fee) < 0:
                whoPayFee = ld.get_translate(self, callUser, ld.FeePaySellerKey)
            req = ld.get_translate(self, callUser, ld.RequestResultStringTemplate).format(number, username, reqType, quantity, currency, fee, whoPayFee, bank, startDate, endDate)
            results.append(req)

        return results

    def __getLocalizedRequestType(self, reqType: RequestType, callUser):
        if reqType == RequestType.Buy:
            return ld.get_translate(self, callUser, ld.BuyKey).lower()
        else:
            return ld.get_translate(self, callUser, ld.SellKey).lower()

    def __cleanup_db(self):
        sqls = [
            "DELETE FROM requests WHERE username NOT IN (SELECT username FROM users)", 
            "DELETE FROM notifications WHERE username NOT IN(SELECT username FROM users)",
            "DELETE FROM users_votes WHERE username NOT IN(SELECT username FROM users)",
            "DELETE FROM users_votes WHERE votedUser NOT IN(SELECT username FROM users)",
            "DELETE FROM users_languages WHERE username NOT IN(SELECT username FROM users)"
            ]
        for sql in sqls:
            self.cur.execute(sql)
        self.conn.commit()