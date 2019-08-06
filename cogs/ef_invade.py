import discord
import datetime
import os
from discord.ext import commands
from datetime import datetime, timezone, date
from math import ceil
from .utils.dataIO import dataIO
import collections

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

        do_message = """**Do:**
1. Always pick a one hit monster
2. Open all monster lv 300 and above
3. Can enchant any monster start from 390 and above
"""

        dont_message = """**Dont: **
1. Dont enchant at day one
2. Dont hit any tile with less than level 300
"""

        await self.bot.say(do_message)
        await self.bot.say(dont_message)

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

        routepic_path = os.path.join("data", "ef_invade", "files", "route_round41.jpg")
        channel = ctx.message.channel

        try:
            await self.bot.say("White: main path\nYellow: secondary path")
            await self.bot.send_file(channel, routepic_path)
        except HTTPException as x:
            print(x)
            await self.bot.say("Failed to send guide pic. Please complain to killmyrene about this")

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

    @_invade.command(pass_context=True, name="showsimplepr")
    async def _invade_show_simple_priority(self, ctx: commands.Context):

        server_setting = self.get_server_setting(ctx.message.server.id)
        await self.show_simple_priority(server_setting)

    @_invade.command(pass_context=True, name="showpr")
    async def _invade_show_priority(self, ctx: commands.Context):
        """ Shows the current priority to clear. It can be a star priority, high point prioirity or both
        Shows priority on +0, +1, +2 and +3 blocks

        Priorities can be modified by either using setpr and/or clearpr
        """
        await self.show_priority_internal(ctx)
    
    async def show_priority_internal(self, ctx: commands.Context):


        server_setting = self.get_server_setting(ctx.message.server.id)
        #await self.show_simple_priority(server_setting)
        await self.show_level_priority(server_setting)

    async def show_simple_priority(self, server_setting):
        hasPriority = False
        for priorityKey in ['0', '1', '2', '3']:
            priorities = server_setting[priorityKey]
            if not priorities:
                #Skip if theres no priorities
                continue
            await self.bot.say("+{}: {}".format(priorityKey, ", ".join(priorities)))
            hasPriority = True

        if not hasPriority:
            await self.bot.say("Unfortunately there's no priority to set. Please complain to killmyrene to set priorities. You could focus on making the path if its not been made yet")

    async def show_level_priority(self, server_setting):
        if not server_setting['board']:
            await self.bot.say("Unfortunately there's no priority and board being set. Please complain to killmyrene to set priorities. You could focus on making the path if its not been made yet")
            return

        await self.bot.say("Priorities according to level")

        board = server_setting['board']

        level_priorities = collections.OrderedDict()

        criterias = [650, 640, 630, 620, 610, 600, 570, 540, 500, 460, 380]
        for criteria in criterias:
            level_priorities[str(criteria)] = []

        belowToleranceKey = 380
        level_priorities["below {}".format(belowToleranceKey)] = []

        hasPriority = False
        for priorityKey in ['0', '1', '2', '3']:
            for priority in server_setting[priorityKey]:
                for criteria in criterias:
                    board_index = int(priority) - 1
                    board_level = board[board_index] + 50 * int(priorityKey)
                    print("Priority {}: {} lvl +{} > {} criteria. Original: {}".format(priority, board_level, priorityKey, criteria, board[board_index]))
                    if board_level >= criteria:
                        level_priorities[str(criteria)].append(priority)
                        break
                    elif board_level < belowToleranceKey:
                        level_priorities["below {}".format(belowToleranceKey)].append(priority)
                        break

            isFirst = True
            for criteria, priorities in level_priorities.items():
                if priorities:
                    if isFirst:
                        await self.bot.say("+{} \n".format(priorityKey))
                        isFirst = False
                    
                    await self.bot.say("{}s: {}".format(criteria, ", ".join(priorities)))
                        #await self.bot.say("{}s at +{}: {}".format(criteria, priorityKey, ", ".join(priorities)))

                    hasPriority = True
                level_priorities[criteria] = []

        if not hasPriority:
            await self.bot.say("Unfortunately there's no priority to set. Please complain to killmyrene to set priorities. You could focus on making the path if its not been made yet")


    @_invade.command(pass_context=True, name="showprandnotify")
    async def _invade_show_priority_and_notify(self, ctx: commands.Context):
        """ Shows the current priority to clear and notify the entire channel. It can be a star priority, high point prioirity or both
        Shows priority on +0, +1, +2 and +3 blocks

        Priorities can be modified by either using setpr and/or clearpr
        """
        
        #await self.bot.say("To those that haven't used their invasion tix please use them before reset. Also use up war tix if you haven't yet\nHere's the priority to clear before reset")
        await self.bot.say("Here's the priority to clear before reset")
        await self.show_priority_internal(ctx)

    @_invade.command(pass_context=True, name="setpr")
    async def _invade_set_priority(self, ctx: commands.Context, enchant_lvl: str, *, block_numbers: str):
        """ Set the priority according to their enchant lvls. For example
        !invade setpr 0 2 3 4 will set priority of blocks 2, 3 and 4 on enchant 0
        """

        server_setting = self.get_server_setting(ctx.message.server.id)

        #Validate enchant lvl
        if not self.is_enchant_lvl_valid(enchant_lvl):
            await self.bot.say("Enchant LVL should be within 0-3")
            return

        server_setting[enchant_lvl] = block_numbers.split(" ")
        await self.bot.say("{} has been set on +{} enchant lvl as priority".format(", ".join(server_setting[enchant_lvl]), enchant_lvl))
        self.save_server_settings(ctx.message.server.id, server_setting)

    @_invade.command(pass_context=True, name="addpr")
    async def _invade_add_priority(self, ctx: commands.Context, enchant_lvl: str, *, block_numbers: str):
        """ Add new additional blocks according to their enchant lvls as a priority. For example
        !invade addpr 0 2 3 4 will add blocks 2, 3 and 4 as a priority as enchant 0

        Existing blocks in enchants will be ignored
        """

        server_setting = self.get_server_setting(ctx.message.server.id)

        #Validate enchant lvl
        if not self.is_enchant_lvl_valid(enchant_lvl):
            await self.bot.say("Enchant LVL should be within 0-3")
            return

        blocks = block_numbers.split(" ")
        enchant_priority_list = server_setting[enchant_lvl]
        isUpdated = False
        for block in blocks:
            if block in enchant_priority_list:
                await self.bot.say("Block {} already exists in +{} enchant priority".format(block, enchant_lvl))
            else:
                enchant_priority_list.append(block)
                enchant_priority_list.sort(key=int)
                isUpdated = True


        server_setting[enchant_lvl] = enchant_priority_list
        self.save_server_settings(ctx.message.server.id, server_setting) 
        if isUpdated:
            await self.bot.say("New priority on +{} enchant: {}".format(enchant_lvl, ", ".join(enchant_priority_list)))
        

    @_invade.command(pass_context=True, name="removepr")
    async def _invade_remove_priority(self, ctx: commands.Context, enchant_lvl: str, *, block_numbers: str):
        """ Remove blocks according to their enchant lvls from the priority. For example
        !invade removepr 0 2 3 4 will remove blocks 2, 3 and 4 as a priority from enchant 0

        Blocks not in priority per enchant will be ignored
        """

        server_setting = self.get_server_setting(ctx.message.server.id)

        #Validate enchant lvl
        if not self.is_enchant_lvl_valid(enchant_lvl):
            await self.bot.say("Enchant LVL should be within 0-3")
            return

        blocks = block_numbers.split(" ")
        enchant_priority_list = server_setting[enchant_lvl]
        isUpdated = False
        for block in blocks:
            if block not in enchant_priority_list:
                await self.bot.say("Block {} doesnt exists in +{} enchant priority".format(block, enchant_lvl))
            else:
                enchant_priority_list.remove(block)
                isUpdated = True


        server_setting[enchant_lvl] = enchant_priority_list
        self.save_server_settings(ctx.message.server.id, server_setting) 
        if isUpdated:
            await self.bot.say("New priority on +{} enchant: {}".format(enchant_lvl, ", ".join(enchant_priority_list)))
        

    @_invade.command(pass_context=True, name="clearpr")
    async def _invade_clear_priority(self, ctx: commands.Context, enchant_lvl: str = None):
        """Clears all priorities, or specific enchant lvl if it were set """

        server_id = ctx.message.server.id
        server_setting = self.get_server_setting(server_id)
        #Validate enchant lvl
        if enchant_lvl is None:

            for priorityKey in ['0', '1', '2', '3']:
                server_setting[priorityKey] = []

            await self.bot.say("All priorites have been cleared")
        else:
            if not self.is_enchant_lvl_valid(enchant_lvl):
                await self.bot.say("Enchant LVL should be within 0-3")
                return
            server_setting[enchant_lvl] = []
            await self.bot.say("Priorities under +{} enchant lvl has been cleared".format(enchant_lvl))

        self.save_server_settings(server_id, server_setting)

    @_invade.command(pass_context=True, name="setboard")
    async def _invade_set_board(self, ctx: commands.Context, *, block_numbers: str):
        """ Set the board layout in a list. Each block number represents the index of the block
        For example, setting !invade setboard 70 300 50 500 represents the board on a 2x2 format
        """
        server_setting = self.get_server_setting(ctx.message.server.id)

        board = block_numbers.replace("\n", " ").split(" ")
        server_setting['board'] = [int(s) for s in list(filter(len, board))]

        await self.bot.say("Board of size {} has been set".format(len(server_setting['board'])))
        self.save_server_settings(ctx.message.server.id, server_setting)

    def is_enchant_lvl_valid(self, enchant_lvl):
        enchant_lvl_int = int(enchant_lvl)
        if enchant_lvl_int < 0 or enchant_lvl_int > 3:
            return False
        return True


    def get_server_setting(self, server_id):
        if server_id not in self.settings:
            #create default settings for the server
            self.save_server_settings(server_id, generate_default_invade_priority_settings())
        return self.settings[server_id]

    def save_server_settings(self, server_id, server_setting):
        self.settings[server_id] = server_setting
        dataIO.save_json(get_invade_setting_filepath(), self.settings)



def check_folders():
    paths = ("data/ef_invade", "data/ef_invade/files")
    for path in paths:
        if not os.path.exists(path):
            print("Creating {} folder...".format(path))
            os.makedirs(path)

def get_invade_setting_filepath():
    return "data/ef_invade/settings.json"

def get_invade_import_api_filepath():
    return "../data/ef_invade/secret_file.json"

def check_files():
    f = get_invade_setting_filepath()
    if not dataIO.is_valid_json(f):
        print("Creating {}...".format(f))
        dataIO.save_json(f, {'dummy_server_id' : generate_default_invade_priority_settings()})

def generate_default_invade_priority_settings():
    return { '0' : [], '1' : [], '2' : [], '3' :[], 'board' :[]}

def setup(bot):
    check_folders()
    check_files()
    
    bot.add_cog(EFInvade(bot))
