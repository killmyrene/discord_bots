import discord
import datetime
from discord.ext import commands
from datetime import datetime, timezone, date

class EFRaid:
	def __init__(self, bot):
		self.bot = bot
		self.rotation = ["1.9, 1.11, 4.8, 2x 5.6", "2x 1.9, 4.8, 2x 5.6"]

	def get_total_days(self):
		now = datetime.utcnow()
		ordinal = datetime.fromordinal(1)
		totalNumDays = (now - ordinal).days
		return totalNumDays

	def get_current(self):
		return (self.get_total_days() - 1) % len(self.rotation)

	def get_modulus(self):
		return (self.get_total_days()) % len(self.rotation)

	@commands.command()
	async def raidremind(self):
		"""Raid Reminder"""

		await self.bot.say("Raid Schedule:")
		current = self.get_current()
		modulus = self.get_modulus()


		for i in range(len(self.rotation)) :
			if i == current:
				await self.bot.say("Day " + str(i + 1) + ": " + self.rotation[i] + " :star:")
			else:
				await self.bot.say("Day " + str(i + 1) + ": " + self.rotation[i])

		await self.bot.say("Next Rotation: " + self.rotation[modulus])

	@commands.command()
	async def raidopen(self):
		"""Raid Open"""

		modulus = self.get_current()
		await self.bot.say("@everyone Raid open (" + self.rotation[modulus] + ")")



def setup(bot):
    bot.add_cog(EFRaid(bot))
