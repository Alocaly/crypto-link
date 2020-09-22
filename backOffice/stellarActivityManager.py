"""
Class StellarManager is designed to handle off-chain and on-chain activities and store data
into history

"""
import os
import sys
from pymongo import MongoClient, errors
from utils.tools import Helpers

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)


helper = Helpers()
hot = helper.read_json_file(file_name='hotWallets.json')
d = helper.read_json_file(file_name='botSetup.json')


class StellarManager:
    def __init__(self):
        self.xlmHotWallet = hot['xlm']
        self.connection = MongoClient(d['database']['connection'], maxPoolSize=20)
        self.stellarCoin = self.connection['CryptoLink']

        # Collections connections
        self.stellarWallets = self.stellarCoin.StellarWallets  # Access to all stellar wallets
        self.stellarDeposits = self.stellarCoin.StellarDeposits  # Access to history of successfull deposits
        self.stellarWithdrawals = self.stellarCoin.StellarWithdrawals  # Access to history of successfull withdrawals
        self.stellarUnprocessedDep = self.stellarCoin.StellarUnprocessedDeposits  # Accaes to history of unsuccessfull deposits
        self.stellarUnprocessedWith = self.stellarCoin.StellarUnprocessedWithdrawals  # Access to history of unprocessed withdrawals
        self.stellarCorpWallets = self.stellarCoin.StellarCorporateWallets

    def stellar_deposit_history(self, type: int, data):
        """
        Managing history of deposits
        :param type:
        :param data:
        :return:
        """
        if type == 1:
            result = self.stellarDeposits.insert_one(data)
        elif type == 2:
            result = self.stellarUnprocessedDep.insert_one(data)

        if result.inserted_id:
            return True
        else:
            return False

    def stellar_withdrawal_history(self, type: int, data: dict):
        """
        Managing history off withdrawals

        :param type:
        :param data:
        :return:
        """
        if type == 1:  # IF Successfull
            result = self.stellarWithdrawals.insert_one(data)
        elif type == 2:  # IF error
            result = self.stellarUnprocessedWith.insert_one(data)

        if result.inserted_id:
            return True
        else:
            return False

    def check_if_stellar_memo_exists(self, memo):
        """
        Check if deposit payment ID exists in the system
        :param memo: Deposit payment ID for Stellar Wallet
        :return: boolean
        """

        result = self.stellarWallets.find_one({"depositId": memo})

        if result:
            return True
        else:
            return False

    def check_if_deposit_hash_processed_succ_deposits(self, hash):
        """
        Function which checks if HASH has been already processed
        """
        result = self.stellarDeposits.find_one({"hash": hash})

        if result:
            return True
        else:
            return False

    def check_if_deposit_hash_processed_unprocessed_deposits(self, hash):
        """
        Check if hash is stored in unprocessed deposits
        """
        result = self.stellarUnprocessedDep.find_one({"hash": hash})

        if result:
            return True
        else:
            return False

    def get_stellar_wallet_data_by_discord_id(self, discord_id):
        """
        Get users wallet details by unique Discord id.
        """
        result = self.stellarWallets.find_one({"userId": discord_id},
                                              {"_id":0})
        if result:
            return result
        else:
            return {}

    def update_stellar_balance_by_memo(self, memo, stroops: int, direction: int):
        """
        Updates the balance based on stellar memo with stroops
        :param memo: Deposit payment id
        :param stroops: minimal stellar unit stroop as int
        :return:
        """
        if direction == 1:  # Append
            pass
        else:
            stroops *= (-1)  # Deduct

        try:
            result = self.stellarWallets.update_one({"depositId": memo},
                                                    {'$inc': {"balance": stroops},
                                                     "$currentDate": {"lastModified": True}})

            return result.matched_count > 0
        except errors.PyMongoError as e:
            return False

    def update_stellar_balance_by_discord_id(self, discord_id: int, stroops: int, direction: int):
        """
        Updates the balance based on discord id  with stroops
        :param discord_id: Unique Discord id
        :param stroops: stroops
        :return:
        """
        if direction == 1:  # Append
            pass
        else:
            stroops *= (-1)  # Deduct

        try:
            result = self.stellarWallets.update_one({"userId": discord_id},
                                                    {'$inc': {"balance": int(stroops)},
                                                     "$currentDate": {"lastModified": True}})

            return result.matched_count > 0
        except errors.PyMongoError as e:
            print(e)
            return False

    def get_discord_id_from_deposit_id(self, deposit_id):
        """
        Query unique users discord if based on deposit_id / memo
        """
        result = self.stellarWallets.find_one({"depositId": deposit_id})
        return result
