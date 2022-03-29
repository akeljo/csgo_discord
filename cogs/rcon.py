from discord.ext import commands
from discord.ext.commands import Bot, has_permissions, CheckFailure
import discord
import valve.rcon
import config
import subprocess
from subprocess import Popen, PIPE
import time
import re

class rcon(commands.Cog):
    """Switch game modes and start or stop the server"""

    @commands.command(name="mode")
    @commands.cooldown(rate=1, per=300)
    @commands.has_any_role('Admin', 'Mod') 
    async def mode(self, ctx: commands.Context, *, text: str):
        """Change Modes"""
        if text:
            rcon_command = f"sm_practicemode_autostart 1; exec sourcemod/trigger{text}.cfg"
            with valve.rcon.RCON((config.ip, config.port), config.rconpass) as rcon:
                    response = rcon.execute(rcon_command)
                    await ctx.send(f"exec practice config")
                    print(f'exec practice config')
        
        else:
            await ctx.send(f"Invalid mode")
            print(f'Invalid mode')

    @mode.error
    async def map_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            message = f"This command is on cooldown. Please try again after {round(error.retry_after, 1)} seconds."
        else:
            message = f"{error}"
        await ctx.send(message, delete_after=5)
        await ctx.message.delete(delay=5)

    @commands.command(name="map")
    @commands.cooldown(rate=1, per=300)
    @commands.has_any_role('Admin', 'Mod') 
    async def map(self, ctx: commands.Context, *, text: str):
        """Change Map"""
        rcon_command = f"changelevel {text}"

        with valve.rcon.RCON((config.ip, config.port), config.rconpass) as rcon:
            response = rcon.execute(rcon_command)
            await ctx.send(f"Map Changed to: {text}")
            print(f"Map Changed to: {text}")
            
    @map.error
    async def map_error(self, ctx: commands.Context, error):
        print(f'{error}')

    @commands.command(name="status")
    @commands.cooldown(rate=1, per=2)
    @has_permissions(manage_messages=True)
    async def rcon_status(self, ctx: commands.Context):
        """Server Status"""
        rcon_command = f"status; sv_password"

        with valve.rcon.RCON((config.ip, config.port), config.rconpass) as rcon:
            response = rcon.execute(rcon_command)
            response_text = response.body.decode("utf-8")
            #print(response.text) #debug
            result = {}
            
            for line in response.text.split('\n'):
                if ': ' in line:
                    key, value = line.split(": ", 1)
                    result[key.strip(' .')] = value.strip()
                elif '= ' in line:
                    key, value = line.split(" = ", 1)
                    result[key.replace('"','')] = value.split()[0].replace('"','')
            #print(f'{result}') #debug
            embed = discord.Embed(title='Status', description=f'{result["hostname"]}\n \
            {result["udp/ip"].split(": ")[0].split()[0]}\n \
            {result["map"]}\n \
            {result["players"].split()[0]} / {result["players"].split("/")[0].split("(")[1]}', color=0x4EA13A)
            await ctx.send(embed=embed)
            if result['sv_password']:
                await ctx.send(f"connect {result['udp/ip'].split(': ')[0].split()[0]}; password {result['sv_password']}")
            else:
                await ctx.send(f"connect {result['udp/ip'].split(': ')[0].split()[0]}")

    @rcon_status.error
    async def status_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            message = f"This command is on cooldown. Please try again after {round(error.retry_after, 1)} seconds."
        elif isinstance(error, commands.MissingPermissions):
            message = "You are missing the required permissions to run this command!"
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"Missing a required argument: {error.param}"
        elif isinstance(error, commands.ConversionError):
            message = str(error)
        else:
            message = f"{error}"
            #print(f'{error}') #debug

        await ctx.send(message, delete_after=5)
        await ctx.message.delete(delay=5)

    @commands.command(name="details")
    @commands.cooldown(rate=1, per=2)
    @commands.has_any_role('Admin', 'Mod') 
    async def details(self, ctx: commands.Context):
        process = Popen(['sudo', '-u', 'akeljo', f'/home/{config.user}/{config.script}', 'details'], stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        exitcode = process.returncode

        escapes = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        output = escapes.sub("", f"{out.decode()}")

        result = {}
        for line in output.split('\n'):
                if ': ' in line:
                    key, value = line.split(": ", 1)
                    result[key.strip(' .')] = value.strip()
                elif '= ' in line:
                    key, value = line.split(" = ", 1)
                    result[key.replace('"','')] = value.split()[0].replace('"','')

        return(result)

    @commands.command(name="stop")
    @commands.cooldown(rate=1, per=2)
    @commands.has_any_role('Admin', 'Mod') 
    async def server_stop(self, ctx: commands.Context):
        result = await self.details(ctx)
        if "STOPPED" in result['Status']:
            await ctx.send(f"Server already stopped")
            print('Server already stopped')
        elif "STARTED" in result['Status']:
            process = Popen(['sudo', '-u', 'akeljo', f'/home/{config.user}/{config.script}', 'stop'], stdout=PIPE, stderr=PIPE)
            out, err = process.communicate()
            exitcode = process.returncode
            output = process.communicate()[0].decode('utf8')
        
            if "  OK  " in output:
                await ctx.send(f"CSGO Server stopped")
                print('Server stopped')
            else:
                await ctx.send(f"No Server to stop", delete_after=5)
                await ctx.message.delete(delay=5)

    @commands.command(name="test")
    @commands.cooldown(rate=1, per=2)
    @commands.has_any_role('Admin', 'Mod') 
    async def test(self, ctx: commands.Context):
        result = await self.details(ctx)
        if "STOPPED" in result['Status']:
            print('stopped')
        elif "STARTED" in result['Status']:
            print('Started')

    @commands.command(name="start")
    @commands.cooldown(rate=1, per=2)
    @commands.has_any_role('Admin', 'Mod') 
    async def server_start(self, ctx: commands.Context):
        result = await self.details(ctx)
        if "STOPPED" in result['Status']:
            print('Server is stopped\nNow Starting Server...')
            process = Popen(['sudo', '-u', 'akeljo', f'/home/{config.user}/{config.script}', 'start'], stdout=PIPE, stderr=PIPE)
            out, err = process.communicate()
            exitcode = process.returncode
            output = process.communicate()[0].decode('utf8')

            if f"  OK  " in output:
                await ctx.send(f"CSGO Server started")
                time.sleep(10)
                await self.rcon_status(ctx)
                print('Server has started')
            else:
                await ctx.send(f"No Server to start", delete_after=5)
                await ctx.message.delete(delay=5)

            #print (exitcode, out, err) #debug
        elif "STARTED" in result['Status']:
            await ctx.send(f"Server already running")
            await self.rcon_status(ctx)
            print('Server already running')

def setup(bot):
    bot.add_cog(rcon(bot))