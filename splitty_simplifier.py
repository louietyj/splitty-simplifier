from config import *
from utils_tgbot import *
import decimal
import re
import telegram.ext

class SplittySimplifier:
    def __init__(self, token):
        self.updater = telegram.ext.Updater(token=token)
        self.dispatcher = self.updater.dispatcher
        self.bot = BotWrapper(self.dispatcher.bot)

        # Add handler
        self.dispatcher.add_handler(
            telegram.ext.MessageHandler(
                telegram.ext.Filters.forwarded & telegram.ext.Filters.text,
                self.handler,
            )
        )
        self.updater.start_polling()

    @staticmethod
    def parse(text):
        creditor = None
        balance = {}
        for line in text.split('\n'):
            if not line.strip():
                continue
                
            # "XX, your debtors:"
            match = re.match('(.+), your debtors:', line)
            if match:
                creditor = match.group(1)
                continue

            # "- YY, ZZ💰"
            # Means YY owes XX the amount of ZZ
            match = re.match('- (.+), (\d+.?\d*)💰', line)
            if match:
                if not creditor:
                    raise ValueError('Debtor without creditor')
                debtor, amount = match.group(1), decimal.Decimal(match.group(2))
                balance[creditor] = balance.get(creditor) or 0
                balance[debtor] = balance.get(debtor) or 0
                balance[creditor] += amount
                balance[debtor] -= amount
                continue

            raise ValueError('Unparseable line')
        return balance

    @staticmethod
    def greedy_simplify(balance):
        balance = balance.copy()
        transfers = []
        while any(num != 0 for num in balance.values()):
            debtor = min(balance, key=balance.get)
            creditor = max(balance, key=balance.get)
            value = min(-balance[debtor], balance[creditor])
            transfers.append((debtor, creditor, value))
            balance[debtor] += value
            balance[creditor] -= value
        return transfers

    @staticmethod
    def create_output(transfers):
        return 'Simplified debt:\n' + \
            '\n'.join('%s → %s, %s💰' % transfer for transfer in sorted(transfers))

    def handler(self, bot, update):
        if update.message.forward_from.username != 'splittybot':
            return
        balance = self.parse(update.message.text)
        transfers = self.greedy_simplify(balance)
        output = self.create_output(transfers)
        self.bot.reply(update.message, output)

if __name__ == '__main__':
    splitty_simplifier = SplittySimplifier(token=TOKEN)
