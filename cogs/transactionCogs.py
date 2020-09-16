import discord
from discord.ext import commands

from backOffice.botStatistics import BotStatsManager
from backOffice.profileRegistrations import AccountManager
from backOffice.stellarActivityManager import StellarManager
from cogs.utils import monetaryConversions
from cogs.utils.systemMessaages import CustomMessages
from utils.tools import Helpers
from cogs.utils.customCogChecks import is_public, has_wallet

helper = Helpers()
account_mng = AccountManager()
stellar = StellarManager()
bot_stats = BotStatsManager()
customMessages = CustomMessages()
d = helper.read_json_file(file_name='botSetup.json')
auto_channels = helper.read_json_file(file_name='autoMessagingChannels.json')
CONST_STELLAR_EMOJI = '<:stelaremoji:684676687425961994>'


class TransactionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.symbols = ['xlm']

    @commands.group()
    @commands.check(is_public)
    @commands.check(has_wallet)
    async def send(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if ctx.invoked_subcommand is None:
            title = '__Available functions and  coins for P2P transactions'
            description = "Bellow are presented all available currencies for P2P transacitons on Launch Pad Investments"
            list_of_values = [
                {"name": f"{CONST_STELLAR_EMOJI} Stellar Lumen {CONST_STELLAR_EMOJI}",
                 "value": f"{d['command']}send xlm <amount> <@DiscordUser>"}]

            await customMessages.embed_builder(ctx=ctx, title=title, description=description, data=list_of_values)

    @send.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def xlm(self, ctx, amount: float, recipient: discord.User):
        """
        Initiates off chain transaction for stellar lumen currency
        :param ctx:
        :param amount:
        :param recipient:
        :return:
        """

        stroops = (int(amount * (10 ** 7)))
        if stroops > 0:
            if not ctx.message.author == recipient and not recipient.bot:
                wallet_value = stellar.get_stellar_wallet_data_by_discord_id(discord_id=ctx.message.author.id)[
                    'balance']
                if int(wallet_value) >= int(stroops):
                    if not account_mng.check_user_existence(user_id=recipient.id):
                        account_mng.register_user(discord_id=recipient.id, discord_username=f'{recipient}')
                    decimal_point = monetaryConversions.get_decimal_point('xlm')
                    assert amount == float(monetaryConversions.get_normal(str(stroops),
                                                                          decimal_point=decimal_point))

                    if stellar.update_stellar_balance_by_discord_id(discord_id=ctx.message.author.id,
                                                                    stroops=int(stroops), direction=2):
                        if stellar.update_stellar_balance_by_discord_id(discord_id=recipient.id, stroops=int(stroops),
                                                                        direction=1):

                            if bot_stats.update_off_chain_activity_stats(ticker='stellar',
                                                                         amount=stroops):  # Updating bbot stats
                                pass
                            else:
                                print('Stats could not be updated')

                            await customMessages.transaction_report_to_channel(ctx=ctx, recipient=recipient,
                                                                               amount=amount, currency='xlm')

                            # report to sender
                            await customMessages.transaction_report_to_user(direction=0, amount=amount, symbol='xlm',
                                                                            user=recipient,
                                                                            destination=ctx.message.author)
                            # report to recipient
                            await customMessages.transaction_report_to_user(direction=1, amount=amount,
                                                                            symbol='xlm', user=ctx.message.author,
                                                                            destination=recipient)


                        else:
                            stellar.update_stellar_balance_by_discord_id(discord_id=ctx.message.author.id,
                                                                         stroops=int(stroops),
                                                                         direction=1)
                            title = '__Error in transaction__'
                            message = f'{amount} XLA could not be sent to the {recipient} please try again later'
                            await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                                sys_msg_title=title)

                    else:
                        title = '__Error in transaction__'
                        message = f'There has been an error while making P2P transaction please try again later'
                        await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                            sys_msg_title=title)

                else:
                    title = '__Insufficient balance__'
                    message = f'You have insufficient balance! Your current wallet balance is {wallet_value / 10000000} XLM'
                    await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                        sys_msg_title=title)
            else:
                title = '__Recipient error__'
                message = f'You are not allowed to send {amount} xlm to either yourself or the bot.'
                await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                    sys_msg_title=title)
        else:
            title = '__Amount error__'
            message = f'Amount needs to be greater than 0.0000000 XLM'
            await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                sys_msg_title=title)

    @xlm.error
    async def xlm_send_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            title = f'__Bad Argument Provided __'
            message = f'You have provided wrong argument either for amount or than for the recipient'
            await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                sys_msg_title=title)
        elif isinstance(error, AssertionError):
            title = f'__Amount Check failed __'
            message = f'You have provided wrong amount for tx value.'
            await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                sys_msg_title=title)
        elif isinstance(error, commands.CommandOnCooldown):
            title = f'__Command on cooldown__!'
            message = f'You have tried to use the same command to fast. Please wait few momemnts.'
            await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                sys_msg_title=title)

        elif isinstance(error, commands.MissingRequiredArgument):
            title = f'__Missing Required Argument Error __'
            message = f'{str(error)}'
            await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                sys_msg_title=title)

        elif isinstance(error, commands.CheckFailure):
            title = f'__System Transaction Error__'
            message = f'In order to execute P2P transaction you need to be registered into the system, and ' \
                      f'transaction request needs to be executed on one of the text channels on {ctx.message.guild}'
            await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                sys_msg_title=title)

        elif isinstance(error, AssertionError):
            print(error)

        else:
            print(f"Unknown error which ahs not been handled: {error}")


def setup(bot):
    bot.add_cog(TransactionCommands(bot))
