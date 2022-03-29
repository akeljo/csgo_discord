# -*- coding: utf-8 -*-

from discord.ext import commands
from discord.ext.commands import Bot, has_permissions, CheckFailure
import discord
import valve.rcon
import config

class Admin(commands.Cog):
    """The description for Admin goes here."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, *, text: str):
        """Reload cog"""
        self.bot.reload_extension(f"cogs.{text}")
        await ctx.channel.purge()
        embed = discord.Embed(title='Reload', description=f'{text} successfully reloaded', color=0xff00c8)
        await ctx.send(embed=embed)
        print(f'{text} successfully reloaded')

    @commands.command(name="clear")
    @commands.cooldown(rate=1, per=30)
    @commands.has_any_role('Admin', 'Mod') 
    async def clear_channel(self, ctx: commands.Context):
        """Clear Channel"""
        await ctx.channel.purge()

    @commands.command(name="quit")
    @has_permissions(administrator=True)
    async def quit(self, ctx: commands.Context):
        """Kills the bot"""
        print(f'{self.bot.user.name} has disconnected')
        await ctx.send(f"Shutting down...")
        await self.bot.close()

    @commands.command(name="setstatus")
    @commands.cooldown(rate=1, per=30)
    @commands.has_any_role('Admin', 'Mod') 
    async def setstatus(self, ctx: commands.Context, *, text: str):
        """Set the bot's status."""
        await self.bot.change_presence(activity=discord.Game(name=f'{text} https://kalex.ca'))
        print(f'change status: {text} https://kalex.ca')

    @commands.command(name="invite")
    @commands.cooldown(rate=1, per=300)
    @commands.has_any_role('Admin', 'Mod') 
    async def create_invite(self, ctx: commands.Context):
        """Create invite"""
        invite = await ctx.channel.create_invite(max_age = 300)
        await ctx.send(f"Invite: {invite}")

    @setstatus.error
    async def setstatus_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            message = f"This command is on cooldown. Please try again after {round(error.retry_after, 1)} seconds."
        elif isinstance(error, commands.MissingPermissions):
            message = "You are missing the required permissions to run this command!"
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"Missing a required argument: {error.param}"
        elif isinstance(error, commands.ConversionError):
            message = str(error)
        else:
            message = f"Oh no! Something went wrong while running the command!"
            print(f'{error}')

        await ctx.send(message, delete_after=5)
        await ctx.message.delete(delay=5)

    @quit.error
    async def quit_error(self, ctx: commands.Context, error):
        print(f'{error}')

    @reload.error
    async def reload_error(self, ctx: commands.Context, error):
        print(f'{error}')

def setup(bot):
    bot.add_cog(Admin(bot))
