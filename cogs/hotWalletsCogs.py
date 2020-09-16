"""
COGS: Management of the whole payment system
"""
import os
import sys

from discord.ext import commands

from backOffice.stellarOnChainHandler import StellarWallet
from cogs.utils.monetaryConversions import convert_to_usd
from cogs.utils.systemMessaages import CustomMessages
from cogs.utils.customCogChecks import is_one_of_gods
from utils.tools import Helpers

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)
helper = Helpers()
stellar = StellarWallet()

customMessages = CustomMessages()
d = helper.read_json_file(file_name='botSetup.json')
auto_channels = helper.read_json_file(file_name='autoMessagingChannels.json')

CONST_STELLAR_EMOJI = '<:stelaremoji:684676687425961994>'

class HotWalletCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.check(is_one_of_gods)
    async def hot(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if ctx.invoked_subcommand is None:
            value = [{'name': f'***{d["command"]}hot stellar*** ',
                      'value': f"Returns information from wallet RPC on stellar balance"}
                     ]
            await customMessages.embed_builder(ctx, title='Querying hot wallet details',
                                               description="All available commands to operate with hot wallets",
                                               data=value, destination=1)

    @hot.command()
    async def stellar(self, ctx):
        data = stellar.get_stellar_hot_wallet_details()
        get_usd_value = convert_to_usd(amount=float(data['balances'][0]['balance']), coin_name='stellar')
        if data:
            title = 'Stellar hot wallet details'
            description = 'Bellow are provided all details on integrated Stellar Wallet'

            list_of_values = [{'name': f'Address',
                               'value': f"{data['account_id']}"},
                              {'name': f'Balance',
                               'value': f"{data['balances'][0]['balance']} {CONST_STELLAR_EMOJI}"},
                              {'name': f'In USD $',
                               'value': f"$ {get_usd_value['total']}\n"
                                        f"Rate: {get_usd_value['usd']} $ 1XLM"},
                              {'name': f'Buying liabilities',
                               'value': f"{data['balances'][0]['buying_liabilities']} {CONST_STELLAR_EMOJI}"},
                              {'name': f'Selling liabilities',
                               'value': f"{data['balances'][0]['selling_liabilities']} {CONST_STELLAR_EMOJI}"}
                              ]
            await customMessages.embed_builder(ctx=ctx, title=title, description=description, data=list_of_values,
                                               destination=1)
        else:
            sys_msg_title = 'Stellar Wallet Query Server error'
            message = 'Status of the wallet could not be obtained at this moment'
            await customMessages.system_message(ctx=ctx, color_code=1, message=message, destination=1,
                                                sys_msg_title=sys_msg_title)


def setup(bot):
    bot.add_cog(HotWalletCommands(bot))
