from enum import IntEnum
from database import DB

class Languages(IntEnum):
    English = 0
    Russian = 1

DefaultLanguage = Languages.Russian

EnglishKey = "EnglishKey"
RussianKey = "RussianKey"
SetUsernameKey = "SetUsernameKey"
EmptyKey = "EmptyKey"
UsernameAlreadyRegisteredKey = "UsernameAlreadyRegisteredKey"
UserRegisteredKey = "UserRegisteredKey"
PleaseRegisterGroupChatKey = "PleaseRegisterGroupChatKey"
BuyKey = "BuyKey"
SellKey = "SellKey"
ShowMyReqKey = "ShowMyReqKey"
ShowAllReqKey = "ShowAllReqKey"
VoteKey = "VoteKey"
UnvoteKey = "UnvoteKey"
EscrowListKey = "EscrowListKey"
EnableNotifKey = "EnableNotifKey"
DisableNotifKey = "DisableNotifKey"
StartMessageKey = "StartMessageKey"
CancelKey = "CancelKey"
SkipKey = "SkipKey"
SellingMsgKey = "SellingMsgKey"
BuyingMsgKey = "BuyingMsgKey"
EnterQuantityMsgKey = "EnterQuantityMsgKey"
SelectWhoPayFee = "SelectWhoPayFee"
SellerKey = "SellerKey"
BuyerKey = "BuyerKey"
NobodyKey = "NobodyKey"
EnterFeeMsgKey = "EnterFeeMsgKey"
RemoveKey = "RemoveKey"
ChangeKey = "ChangeKey"
RemoveErrorKey = "RemoveErrorKey"
RemoveSuccessKey = "RemoveSuccessKey"
ChangeErrorKey = "ChangeErrorKey"
ChangingMsgKey = "ChangingMsgKey"
ZeroVotesKey = "ZeroVotesKey"
VotingMsgKey = "VotingMsgKey"
VoteListEmptyKey = "VoteListEmptyKey"
NotificationsDisabledKey = "NotificationsDisabledKey"
NotificationsEnabledKey = "NotificationsEnabledKey"
WrongInputKey = "WrongInputKey"
EnterBankNameKey = "EnterBankNameKey"
EnterReqDurationKey = "EnterReqDurationKey"
SuccessfulRequestKey = "SuccessfulRequestKey"
NewReqNotifKey = "NewReqNotifKey"
SuccessfulChangeKey = "SuccessfulChangeKey"
ChangedReqNotifKey = "ChangedReqNotifKey"
VotedUserNotRegisteredKey = "VotedUserNotRegisteredKey"
VotedUserAlreadyVotedKey = "VotedUserAlreadyVotedKey"
VotedUserIsMySelfKey = "VotedUserIsMySelfKey"
VoteSuccessfulKey = "VoteSuccessfulKey"
UnvoteSuccessfulKey = "UnvoteSuccessfulKey"
FeePaySellerKey = "FeePaySellerKey"
FeePayBuyerKey = "FeePayBuyerKey"
RequestResultStringTemplate = "RequestResultStringTemplate"
NextPageKey = "NextPageKey"
PrevPageKey = "PrevPageKey"
AcceptSellRequestKey = "AcceptSellRequestKey"
AcceptBuyRequestKey = "AcceptBuyRequestKey"
RequestAlreadyAcceptedKey = "RequestAlreadyAcceptedKey"
RequestWasAcceptedKey = "RequestWasAcceptedKey"
AcceptKey = "AcceptKey"
RequestWasSentKey = "RequestWasSentKey"
RequestHasBeenAcceptedBothSidesKey = "RequestHasBeenAcceptedBothSidesKey"
AcceptRequestHasBeenAutoCancelledKey = "AcceptRequestHasBeenAutoCancelledKey"
AcceptRequestNoLongerActiveKey = "AcceptRequestNoLongerActiveKey"

_dic = [
    {
        EnglishKey: "(EN) English",
        RussianKey: "(RU) Русский",
        SetUsernameKey: "Set your 'username' first",
        EmptyKey: "Empty",
        UsernameAlreadyRegisteredKey: "Username {0} already registered",
        UserRegisteredKey: "{0} registered",
        PleaseRegisterGroupChatKey: "For work with me you need to register in group chat",
        BuyKey: "Buy",
        SellKey: "Sell",
        ShowMyReqKey: "Show my requests",
        ShowAllReqKey: "Show all requests",
        VoteKey: "Vote",
        UnvoteKey: "Unvote",
        EscrowListKey: "Escrow List",
        EnableNotifKey: "Enable Notifications",
        DisableNotifKey: "Disable Notifications",
        StartMessageKey: "<b>Select</b>",
        CancelKey: "Cancel",
        SkipKey: "Skip",
        SellingMsgKey: """<b>Selling</b>

Select currency...""",
        BuyingMsgKey: """<b>Buying</b>

Select currency...""",        
        RemoveKey: "Remove",
        ChangeKey: "Change",
        RemoveErrorKey: "Remove error",
        RemoveSuccessKey: "Request #{0} was removed",
        ChangeErrorKey: "Change error",
        ChangingMsgKey: """<b>Changing request</b>

Select currency""",
        ZeroVotesKey: "Available votes - 0",
        VotingMsgKey: """<b>Voting</b>
Enter the username you want to vote for.""",
        VoteListEmptyKey: "You have not voted for anyone yet",
        NotificationsEnabledKey: "Notifications are ON",
        NotificationsDisabledKey: "Notifications are OFF",
        WrongInputKey: "Wrong input",
        EnterQuantityMsgKey: "Enter quantity:",
        SelectWhoPayFee: "Who will pay fee?",
        SellerKey: "Seller",
        BuyerKey: "Buyer",
        NobodyKey: "Nobody",
        EnterFeeMsgKey: "Enter fee:",
        EnterBankNameKey: "Enter bank name. You can also add additional info here if need.",
        EnterReqDurationKey: "Enter request duration in days",
        SuccessfulRequestKey: "Your request was successfully added",
        NewReqNotifKey: """<b>New request</b>
{0}""",
        SuccessfulChangeKey: "Your request was successfully changed",
        ChangedReqNotifKey: """<b>Changed request</b>
{0}""",
        VotedUserNotRegisteredKey: """User {0} is not registered.
Enter another username""",
        VotedUserAlreadyVotedKey: """You have already voted for {0}
Enter another username""",
        VotedUserIsMySelfKey: """You can't vote for yourself.
Enter another username""",
        VoteSuccessfulKey:  """You was successful voted for {0}
You have {1} votes left""",
        UnvoteSuccessfulKey: """You was successful unvote for {0}
You have {1} votes left""",
        FeePaySellerKey: "<i>(pay seller)</i>",
        FeePayBuyerKey: "<i>(pay buyer)</i>",
        RequestResultStringTemplate: """<b>({0})</b>
@{1} <i>wants to {2}</i> <b>{3} {4}</b>
<b>Fee: {5}%</b>{6}
<b>Bank</b> - {7}. 
<b>Start:</b> {8}, <b>End:</b> {9}""",
        NextPageKey: "Next ►",
        PrevPageKey: "◄ Prev",
        AcceptSellRequestKey: "Buy",
        AcceptBuyRequestKey: "Sell",
        RequestAlreadyAcceptedKey: "Request has been already accepted by someone",
        RequestWasAcceptedKey: "Your request #{0} has been accepted by @{1}",
        AcceptKey: "Accept",
        RequestWasSentKey: "Request has been sent. It will be automatically cancelled in 5 minutes if not accepted by the other side.",
        RequestHasBeenAcceptedBothSidesKey: """Request #{0} has been accepted by both sides. You can contact with @{1} to make a deal.
You can make a deal directly or using garantee.
To view the list of garantors press click the appropriate button in start menu""",
        AcceptRequestHasBeenAutoCancelledKey: "Your accept request was auto cancelled",
        AcceptRequestNoLongerActiveKey: "This accept request is no longer active"
    },
    {
        EnglishKey: "(EN) English",
        RussianKey: "(RU) Русский",
        SetUsernameKey: "Вам нужно установить ваш Username",
        EmptyKey: "Пусто",
        UsernameAlreadyRegisteredKey: "Юзер {0} уже зарегистрирован",
        UserRegisteredKey: "{0} зарегистрирован",
        PleaseRegisterGroupChatKey: "Вы не зарегистрированы. Для работы со мной вам нужно зарегистрироваться в групповом чате.",
        BuyKey: "Купить",
        SellKey: "Продать",
        ShowMyReqKey: "Посмотреть мои заявки",
        ShowAllReqKey: "Посмотреть все заявки",
        VoteKey: "Отдать голос",
        UnvoteKey: "Забрать голос",
        EscrowListKey: "Список гарантов",
        EnableNotifKey: "Включить оповещения",
        DisableNotifKey: "Выключить оповещения",
        StartMessageKey: "<b>Выбирайте</b>",
        CancelKey: "Отмена",
        SkipKey: "Пропустить",
        SellingMsgKey: """<b>Продажа</b>

Выберите валюту...""",
        BuyingMsgKey: """<b>Покупка</b>

Выберите валюту...""",
        RemoveKey: "Удалить",
        ChangeKey: "Изменить",
        RemoveErrorKey: "Ошибка удаления",
        RemoveSuccessKey: "Заявка №{0} удалена",
        ChangeErrorKey: "Ошибка изменения",
        ChangingMsgKey: """<b>Изменение заявки</b>

Выберите валюту""",
        ZeroVotesKey: "Доступное количество голосов - 0",
        VotingMsgKey: """<b>Отдать голос</b>
Введите username пользователя, за которого требуется отдать голос.""",
        VoteListEmptyKey: "Вы еще ни за кого не голосовали",
        NotificationsEnabledKey: "Оповещения включены",
        NotificationsDisabledKey: "Оповещения выключены",
        WrongInputKey: "Ошибочный ввод.",
        EnterQuantityMsgKey: "Введите количество:",
        SelectWhoPayFee: "Кто будет платить проценты?",
        SellerKey: "Продавец",
        BuyerKey: "Покупатель",
        NobodyKey: "Никто",
        EnterFeeMsgKey: "Введите проценты:",
        EnterBankNameKey: "Введите название банка. Вы также можете ввести дополнительную информацию сюда же, если нужно.",
        EnterReqDurationKey: "Введите длительность заявки в днях",
        SuccessfulRequestKey: "Ваша заявка успешно добавлена",
        NewReqNotifKey: """<b>Новая заявка</b>
{0}""",
        SuccessfulChangeKey: "Ваша заявка успешно изменена",
        ChangedReqNotifKey: """<b>Измененная заявка</b>
{0}""",
        VotedUserNotRegisteredKey: """Пользователь {0} не зарегистрирован.
Введите другой username""",
        VotedUserAlreadyVotedKey: """Вы уже голосовали за пользователя {0}
Введите другой username""",
        VotedUserIsMySelfKey: """Вы не можете голосовать за себя.
Введите другой username""",
        VoteSuccessfulKey: """Вы успешно проголосовали за {0}
У вас осталось голосов - {1}""",
        UnvoteSuccessfulKey: """Вы сняли свой голос с {0}
У вас осталось голосов - {1}""",
        FeePaySellerKey: "<i>(платит продавец)</i>",
        FeePayBuyerKey: "<i>(платит покупатель)</i>",
        RequestResultStringTemplate: """<b>({0})</b>
@{1} <i>хочет {2}</i> <b>{3} {4}</b>
<b>Процент: {5}%</b>{6}
<b>Банк</b> - {7}. 
<b>Начало:</b> {8}, <b>Окончание:</b> {9}""",
        NextPageKey: "Дальше ►",
        PrevPageKey: "◄ Назад",
        AcceptSellRequestKey: "Купить",
        AcceptBuyRequestKey: "Продать",
        RequestAlreadyAcceptedKey: "Заявка уже принята кем-то",
        RequestWasAcceptedKey: "Ваша заявка №{0} была принята юзером @{1}",
        AcceptKey: "Принять",
        RequestWasSentKey: "Запрос был отправлен. Он будет автоматически отменен через 5 минут, если не будет принят другой стороной",
        RequestHasBeenAcceptedBothSidesKey: """Заявка №{0} была принята обеими сторонами. Вы можете связаться с @{1} для совершения сделки.
Сделку можно совершить напрямую или через гаранта.
Для просмотра списка гарантов нажмите соответствующую кнопку в стартовом меню""",
        AcceptRequestHasBeenAutoCancelledKey: "Ваш запрос был автоматически отменен",
        AcceptRequestNoLongerActiveKey: "Этот запрос уже не активен"
    }
]

def get_translate(db: DB, username, key):
    lang = db.GetUserLanguage(username)
    dic = _dic[lang]
    if key in dic:
        return dic.get(key)
    return key
    