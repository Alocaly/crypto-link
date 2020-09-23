"""
Back end script: Used to manage merchant system, all users and roles
"""

import os
import sys

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo import errors

from utils.tools import Helpers

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

helper = Helpers()
d = helper.read_json_file(file_name='botSetup.json')


class MerchantManager:
    def __init__(self):
        self.connection = MongoClient(d['database']['connection'], maxPoolSize=20)
        self.communities = self.connection['CryptoLink']

        # Collection of community profiles
        self.community_profiles = self.communities.MerchantCommunityProfile

        # Collection of stellar community wallets
        self.community_stellar_wallets = self.communities.StellarCommunityWallets

        # Collection of monetized roles per each community
        self.monetized_roles = self.communities.MerchantMonetizedRoles

        # Collection of applied users in the system
        self.applied_users = self.communities.MerchantAppliedUsers

        # Collection of all applied communities who payed for the fees
        self.activeLicenses = self.communities.MerchantPurchasedLicenses

    def check_community_license_status(self, community_id):
        """
        Checks if community has already live license
        :param community_id:
        :return:
        """
        data = self.activeLicenses.find_one({"communityId": int(community_id)})
        if data:
            return True
        else:
            return False

    def get_community_license_details(self, community_id):
        """
        Get license details from active community
        :param community_id:
        :return:
        """
        data = self.activeLicenses.find_one({"communityId": int(community_id)},
                                            {"_id": 0})
        return data

    def insert_license(self, community_name, owner_id, community_id, start, end, ticker, value):
        """
        Insert license into directory of active licenses
        :param community_name:
        :param community_id:
        :param date:
        :param ticker:
        :param value:
        :return:
        """
        try:
            data = {
                "communityName": community_name,
                "communityId": int(community_id),
                "ownerId": int(owner_id),
                "start": int(start),
                "end": int(end),
                "ticker": ticker,
                "value": value
            }
            self.activeLicenses.insert_one(data)
            return True
        except errors.PyMongoError:
            return False

    def get_over_due_communities(self, timestamp: int):
        """
        Returns all communities who have expired licenses
        :param timestamp: unix time stamp
        :return:
        """
        all_communities = list(self.activeLicenses.find({"end": {"$lt": timestamp}}))
        return all_communities

    def remove_over_due_community(self, discord_id):
        """
        Removes the overdue from community based on discord id
        :param discord_id:
        :return:
        """
        try:
            self.activeLicenses.delete_one({'communityId': int(discord_id)})
            return True
        except errors.PyMongoError:
            return False

    def check_if_community_exist(self, community_id: int):
        """
        Check if community is registered into the system
        :param community_id: unique community ID provided by discord
        :return: booleasn
        """
        result = self.community_profiles.find_one({"communityId": community_id})
        if result:
            return True
        else:
            return False

    def check_if_community_does_not_exist(self, community_id):
        """
        Check if community is not registered in system
        :param community_id: unique community ID provided by discord
        :return: booleasn
        """
        result = self.community_profiles.find_one({"communityId": community_id})
        if result:
            return False
        else:
            return True

    def register_role(self, community_id: int, role_id: int, role_name: str, penny_value: int, weeks: int, days: int,
                      hours: int,
                      minutes: int):
        """
        Register community role into the system and make it availabale for menetization
        :param community_id: unique community id
        :param role_id: created role id
        :param penny_value: value in pennies
        :param weeks: duration in weeks
        :param days:duration in days
        :param hours:
        :param minutes:
        :return:
        """
        new_role = {
            "roleId": int(role_id),
            "roleName": role_name,
            "communityId": int(community_id),
            "pennyValues": int(penny_value),
            "weeks": int(weeks),
            "days": int(days),
            "hours": int(hours),
            "minutes": int(minutes),
            "status": "active"
        }
        try:
            self.monetized_roles.insert_one(new_role)
            return True
        except errors.PyMongoError:
            return False

    def get_all_roles_community(self, community_id: int):
        """
        Returns all the roles in the system which were monetized by owner of the community
        :param community_id: unique community ID
        :return:
        """
        roles = list(self.monetized_roles.find({"communityId": community_id},
                                               {"_id": 0}))
        return roles

    def find_role_details(self, role_id: int):
        """
        Returns the information on specifc role ID
        :param role_id: Unique role id
        :return: role details as dict, or empty dict
        """
        role_details = self.monetized_roles.find_one({"roleId": role_id},
                                                     {'lastModified': 0})

        if role_details:
            return role_details
        else:
            return {}

    def register_community_wallet(self, community_id: int, community_owner_id: int, community_name: str):
        """
        Makes community wallets once owner of the community registers details
        :param community_id:
        :param community_owner_id:
        :return: boolean
        """
        # Data for registration entry
        community_details = {
            "communityId": int(community_id),
            "communityOwner": int(community_owner_id),
            "communityName": community_name
        }

        # DData for stellar community wallet
        stellar_community_wallet = {
            "communityId": int(community_id),
            "communityOwner": int(community_owner_id),
            "communityName": community_name,
            "balance": int(0),
            "overallGained": int(0),
            "rolesObtained": int(0)
        }

        try:
            self.community_profiles.insert_one(community_details)
            self.community_stellar_wallets.insert_one(stellar_community_wallet)
            return True
        except errors.PyMongoError:
            return False

    def get_wallet_balance(self, community_id: int):
        """
        Get merchant community wallet balances
        :param community_id: unique discord community ID
        :return: data on both wallets if exist or nothing
        """
        stellar_wallet = self.community_stellar_wallets.find_one({"communityId": community_id},
                                                                 {"_id": 0,
                                                                  "balance": 1})

        if stellar_wallet:
            details = {
                "stellar": stellar_wallet
            }
            return details
        else:
            return {}

    def modify_funds_in_community_merchant_wallet(self, community_id: int, amount: int, wallet_tick: str,
                                                  direction: int):
        """
        Trasnfers funds to community merchant wallet once user has payed for it
        :param community_id: Unique community ID
        :param amount: atomic amount as integer of any currency
        :param wallet_tick: ticker to crossreference the wallet for update
        :return: boolean
        """
        if direction == 0:
            pass
        else:
            amount = amount * (-1)

        if wallet_tick == 'xlm':
            # Trasnfer funds to xlm wallet
            try:
                self.community_stellar_wallets.update_one({"communityId": community_id},
                                                          {"$inc": {"balance": amount},
                                                           "$currentDate": {"lastModified": True}})
                return True
            except errors.PyMongoError:
                return False

    def add_user_to_payed_roles(self, community_id, community_name, user_id, user_name, start: int, end: int,
                                role_id: int, role_name, currency: str, currency_value_atom: int, pennies: int):
        """
        add users to the payed roles in the system
        :param community_id: Discord ID
        :param community_name: Community Name
        :param user_id: user ID unique
        :param user_name: user nae
        :param start:
        :param end:
        :param role_id:
        :param role_name:
        :return: boolean
        """
        try:
            new_user_with_role = {
                "userId": int(user_id),
                "userName": user_name,
                "roleId": role_id,
                "roleName": role_name,
                "start": start,
                "end": end,
                "currency": currency,  # Monero or Stellar
                "atomicValue": currency_value_atom,
                "pennies": pennies,
                "communityName": community_name,
                "communityId": community_id}

            self.applied_users.insert_one(new_user_with_role)
            return True
        except errors.WriteConcernError:
            return False
        except errors.WriteError:
            return False

    def remove_monetized_role_from_system(self, role_id, community_id):
        """
        Removes the monetized roles from the system if they get deleted
        :param role_id:
        :param community_id:
        :return:
        """
        result = self.monetized_roles.delete_one({"roleId": role_id, "communityId": community_id})

        if result.deleted_count == 1:
            return True
        else:
            return False

    def remove_all_monetized_roles(self, guild_id):
        try:
            self.monetized_roles.delete_many({"communityId": guild_id})
            return True
        except errors.PyMongoError:
            return False

    def check_user_roles(self, user_id, discord_id):
        """
        return roles which user has obtained on the community
        :param user_id:
        :param discord_id:
        :return:
        """
        applied_roles = list(self.applied_users.find({'userId': user_id, "communityId": discord_id},
                                                     {"_id": 0}))

        if applied_roles:
            return applied_roles
        else:
            return []

    def get_over_due_users(self, timestamp: int):
        """
        Returns all users whos role is overdue based on the timestamp
        :param timestamp: unix time stamp
        :return:
        """
        all_users = list(self.applied_users.find({"end": {"$lt": timestamp}}))
        return all_users

    def remove_overdue_user_role(self, community_id, user_id, role_id):
        """
        Remove user from the active role database uppon expirey
        :param community_id:
        :param user_id:
        :param role_id:
        :return:
        """
        result = self.applied_users.delete_one({"communityId": community_id, "userId": user_id, "roleId": role_id})

        if result.deleted_count == 1:
            return True
        else:
            return False

    def change_role_details(self, role_data):
        """
        Change the role ID based pn object ID
        :param role_data:
        :return:
        """
        result = self.monetized_roles.update_one({'_id': ObjectId(role_data['_id'])},
                                                 {"$set": role_data,
                                                  "$currentDate": {"lastModified": True}})
        if result.modified_count > 0:
            return True
        else:
            return False

    def delete_user_from_applied(self, community_id: int, user_id: int):
        """
        Removing user from database of active purchased roles as he/she does not exist anymore
        """
        result = self.applied_users.delete_many({"communityId": community_id, "userId": user_id})
        if result.deleted_count > 0:
            return True
        else:
            return False

    def delete_all_users_with_role_id(self, community_id: int, role_id: int):
        # TODO integrate into on role remove
        """
        Delete all entries under active roles in database if community does not have that role anymore.
        """
        try:
            self.applied_users.delete_many({"communityId": community_id, "roleId": role_id})
            return True
        except errors.PyMongoError:
            return False

    def bulk_user_clear(self, community_id, role_id):
        """
        Delete all users who have applied for the role however owner of the community has delete the role from the
        system and is not avialabale anymore. Function used to kepp database in check
        :param community_id:
        :param role_id:
        :return:
        """
        result = self.applied_users.delete_many({"communityId": community_id, "roleId": role_id})
        if result.deleted_count > 0:
            return True
        else:
            return False

    def get_balance_based_on_ticker(self, community_id, ticker):

        if ticker == 'xlm':
            stellar_wallet = self.community_stellar_wallets.find_one({"communityId": community_id},
                                                                     {"_id": 0,
                                                                      "balance": 1})
            return stellar_wallet['balance']
