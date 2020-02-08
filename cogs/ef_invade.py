import discord
import datetime
import os
from discord.ext import commands
from datetime import datetime, timezone, date
from math import ceil
from .utils.dataIO import dataIO
import collections
from .utils.priority_info import PriorityInfo
from .utils.ef_invade_utils import *

import requests
from textwrap import dedent

class EFInvade:
    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json(get_invade_setting_filepath())

    @commands.group(pass_context=True, no_pm=True, name="invade")
    async def _invade(self, ctx: commands.Context):
        """EF Guild Invasion Commands to plan ahead accordingly"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
            return

    @_invade.command(pass_context=True, name="guide")
    async def _invade_guideline(self, ctx: commands.Context):
        """Shows the guidelines in bullet form"""

        #Find a clean way to use multi line with indentations

        await self.bot.say(self.get_do_msg())
        await self.bot.say(self.get_dont_msg())

    def get_do_msg(self):

        do_message = '''**Order of Priorities:**
        1. Clear all tiles that has more than 2 stars
        2. If possible, enchant and clear 690+ tiles w/ no star. Higher the better.
        3. Enchant and clear all tiles up to 649
        4. Clear all 460-480 tiles at +1.
        '''
        return dedent(do_message)

    def get_dont_msg(self):

        dont_message = '''**Dont: **
        1. Dont enchant at day one
        2. Dont hit any tile with less than level 300 unless specified 
        3. Don't clear 650-689 w/ no star
        4. After clearing 460-480 at +1, don't enchant further 
        '''

        return dedent(dont_message)


    @_invade.command(pass_context=True, name="guide_pic")
    async def _invade_guideline_pic(self, ctx: commands.Context):
        """Shows the guidelines in image form"""

        guidepic_path = os.path.join("data", "ef_invade", "files", "guideline.jpg")
        channel = ctx.message.channel

        try:
            await self.bot.send_file(channel, guidepic_path)
        except HTTPException as x:
            print(x)
            await self.bot.say("Failed to send guide pic. Please complain to killmyrene about this")

    @_invade.command(pass_context=True, name="route")
    async def _invade_route_pic(self, ctx: commands.Context):
        """Shows the optimal route of the board to clear and unlock high valued blocks"""

        routepic_path = os.path.join("data", "ef_invade", "files", "route.jpg")
        channel = ctx.message.channel

        try:
            # await self.bot.say("White: main path\nYellow: secondary path")
            await self.bot.send_file(channel, routepic_path)

        except HTTPException as x:
            print(x)
            await self.bot.say("Failed to send guide pic. Please complain to killmyrene about this")

        await self.bot.say(self.get_do_msg())
        await self.bot.say(self.get_dont_msg())

    @_invade.command(pass_context=True, name="plan")
    async def _invade_plan(self, ctx: commands.Context, base_area_point: int, no_stars : float, *, new_points: str):
        """ Plan ahead by calculating the new total area points after adding the new area point.

        Calculation are based on the following
        Total Area Points = (Base Area Point + New Area Point) * (1 + 0.01 * # stars)

        [new_points] can be entered with multiple numbers separated by a space, ie 250 300 ...
        """

        list_points = [int(s) for s in new_points.split(" ")]
        sum_points = sum(list_points)

        multiplier = 1 + 0.01 * no_stars
        total_area_points = base_area_point * multiplier
        new_point_multiplied = sum_points * multiplier
        new_total_area_points = total_area_points + new_point_multiplied

        #message = "Multiplier: %0.2f\nTotal Area Point: %0.2f\nNew Points Gain: %0.2f\n\nNew Total Area Points: %d" % (multiplier, 
         #   total_area_points, 
          #  new_point_multiplied, 
           # ceil(new_total_area_points))

        message = "Multiplier: {:,}\nTotal Area Point: {:,}\nNew Points Gain: {:,}\n\nNew Total Area Points: {:,}".format(multiplier, 
            total_area_points, 
            new_point_multiplied, 
            ceil(new_total_area_points))

        await self.bot.say(message)
 
    @_invade.command(pass_context=True, name="setboard")
    async def _invade_set_board(self, ctx: commands.Context, *, block_numbers: str):
        """ Set the board layout in a list. Each block number represents the index of the block
        For example, setting !invade setboard 70 300 50 500 represents the board on a 2x2 format
        """
        board = block_numbers.replace("\n", " ").split(" ")
        self.settings['board'] = [int(s) for s in list(filter(len, board))]

        await self.bot.say("Board of size {} has been set".format(len(self.settings['board'])))
        dataIO.save_json(get_invade_setting_filepath(), self.settings)


    @_invade.command(pass_context=True, name="importpr")
    async def _invade_import_pr(self, ctx: commands.Context, spreadsheetId : str, channel: discord.Channel=None):
        """Downloads a Google Spreadsheet file and imports and displays the priority lists
        The content of the spreadsheet expects the following

        Total Score, <Score>
        Num of Stars, <Star>
        Priority +0, <Block #1>, <Block #2>, <Block#3>, ...
        Priority +1, <Block #1>, <Block #2>, <Block#3>, ...
        Priority +2, <Block #1>, <Block #2>, <Block#3>, ...
        Priority +3, <Block #1>, <Block #2>, <Block#3>, ...

        """

        if channel is None:
            channel = ctx.message.channel
        
        spreadsheetUrl = "https://docs.google.com/spreadsheets/d/{0}/export?format=csv&id={0}&gid=0".format(spreadsheetId)
        response = requests.get(spreadsheetUrl)
        
        if response.status_code != 200:
            await self.bot.say("Unable to download spreadsheet with id {}. Return status code {}".format(spreadsheetId, response.status_code))
            return

        try:
            print("Creating PriorityInfo with {}".format(response.text))
            pr = PriorityInfo(response.text)
        except Exception as e:
            print(e)
            await self.bot.say(dedent('''\
                Failed to parse priorityInfo. The contents should be the following format
                Total Score, <Score>
                Num of Stars, <Star> 
                Priority +0, <Block #1>, <Block #2>, <Block#3>, ...
                Priority +1, <Block #1>, <Block #2>, <Block#3>, ...
                Priority +2, <Block #1>, <Block #2>, <Block#3>, ...
                Priority +3, <Block #1>, <Block #2>, <Block#3>, ... '''))
            return


        print(dedent('''\
            Score: {}
            Stars: {}
            PR +0: {}
            PR +1: {}
            PR +2: {}
            PR +3: {}
            Num PRs: {}
            '''.format(pr.score, 
                pr.stars, 
                pr.priority[0], 
                pr.priority[1], 
                pr.priority[2], 
                pr.priority[3],
                pr.numPriorities)))

        criterias = [800, 780, 740, 730, 720, 710, 700, 680, 670, 660, 650, 640, 630, 620, 610, 600, 570, 540, 500, 490, 460, 420, 380]

        print("Initial Score: {}, Star: {}".format(pr.score, pr.stars))
        await self.bot.send_message(channel, "Priorities according to level\n")

        sum_new_score = 0
        sum_new_stars = 0

        #Changing the order of priorities to display. Starting from +0, +3, +2, +1

        reordered_priority = [pr.priority[0], pr.priority[3], pr.priority[2], pr.priority[1]]
        reorderd_enchant_lvl = [0, 3, 2, 1]

        for index, pr_list in enumerate(reordered_priority):
            
            if len(pr_list) == 0:
                continue

            enchant_lvl = reorderd_enchant_lvl[index]

            score_list = list(map(lambda x: self.lookup_score(x, enchant_lvl), pr_list))
            print(pr_list)
            print(score_list)
            current_pr_score = sum(score_list)
            current_pr_stars = sum(list(map(lambda x: get_num_stars(x, enchant_lvl > 0), score_list)))

            print("Total Scores at +{}: {}, Stars: {}".format(enchant_lvl, current_pr_score, current_pr_stars))
            sum_new_score += current_pr_score
            sum_new_stars += current_pr_stars
    
            message = "+{}\n".format(enchant_lvl)

            for criteria in criterias:
                prInCriteria = list(filter(lambda x: self.lookup_score(x, enchant_lvl) >= criteria, pr_list))
                if len(prInCriteria) > 0:
                    message += "{}s: {}\n".format(criteria, ", ".join(prInCriteria))
                    pr_list = [x for x in pr_list if x not in prInCriteria]

            if len(pr_list) > 0:
                message += "below 380s: {}\n".format(", ".join(pr_list))
            
            await self.bot.send_message(channel, message)

        if sum_new_stars == 0:
            await self.bot.send_message(channel, "No priority list made at the moment. Recommend following the heatmap/spreadsheet on pinned messages")
            return

        print("Initial Area Score: {}".format(pr.score))

        sum_new_score += pr.score
        sum_new_stars += pr.stars

        print("Total Area Score: {}, Stars: {}".format(sum_new_score, sum_new_stars))
        final_score = sum_new_score * (1 + 0.01 * sum_new_stars)
        print("Final Score: {}".format(final_score))
        print("Tix usage: {}".format(pr.numPriorities))

        await self.bot.send_message(channel, dedent('''\
            Initial Score & Stars: {:,} pts / {} :star:
            Projected Tix Used: {}
            Projected Total Score: {:,}
            '''.format(pr.score, pr.stars,
                pr.numPriorities, 
                ceil(final_score))))
    
    def lookup_score(self, block_num:str, enchant_lvl:int):
        board = self.settings['board']
        return board[int(block_num) - 1] + 50 * enchant_lvl

def setup(bot):
    check_folders()
    check_files()

    bot.add_cog(EFInvade(bot))
