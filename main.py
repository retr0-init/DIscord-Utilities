'''
Discord-Bot-Module template. For detailed usages,
 check https://interactions-py.github.io/interactions.py/

Copyright (C) 2024  __retr0.init__

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import interactions
from interactions.ext.paginators import Paginator
import datetime
import aiofiles
import aiofiles.os
# Use the following method to import the internal module in the current same directory
# from . import internal_t
elevation_roles: list[int] = []
elevation_members: list[int] = []
'''
Useful utilities
'''
class Retr0initDiscordUtilities(interactions.Extension):
    module_base: interactions.SlashCommand = interactions.SlashCommand(
        name="utility",
        description="Useful utilities for Discord guilds"
    )
    module_group: interactions.SlashCommand = module_base.group(
        name="guild",
        description="Guild related utilities"
    )
    module_group_c: interactions.SlashCommand = module_base.group(
        name="channel",
        description="Channel related utilities"
    )

    '''
    Check the permission to run the privileged command
    The ROLE_ID needs to be set with the elevate command
    '''
    async def my_check(ctx: interactions.BaseContext):
        res: bool = await interactions.is_owner()(ctx)
        r: bool = any(map(ctx.author.has_role, elevation_roles)) if len(elevation_roles) > 0 else False
        u: bool = any(map(ctx.author.id.__eq__, elevation_members)) if len(elevation_members) > 0 else False
        return res or r or u

    @module_base.subcommand("elevate_show", sub_cmd_description="Show Elevation settings")
    async def cmd_elevateShow(self, ctx: interactions.SlashContext):
        await ctx.defer()
        display_str: str = "There is no current elevation setting." if len(elevation_roles) == 0 and len(elevation_members) == 0 else ""
        if len(elevation_roles) > 0:
            display_str += "### Elevated Roles\n"
            for r in elevation_roles:
                display_str += f"- {ctx.guild.get_role(r).name}\n"
        if len(elevation_members) > 0:
            display_str += "### Elevated Members\n"
            for u in elevation_members:
                display_str += f"- {ctx.guild.get_member(u)}\n"
        pag: Paginator = Paginator.create_from_string(self.bot, display_str)
        await pag.send(ctx)

    @module_base.subcommand("elevate_role", sub_cmd_description="Elevate certain role to run privileged commands")
    @interactions.check(interactions.is_owner())
    @interactions.slash_option(
        name = "role",
        description = "Role to be elevated",
        required = True,
        opt_type = interactions.OptionType.ROLE
    )
    async def cmd_elevateRole(self, ctx: interactions.SlashContext, role: interactions.Role):
        if role.id not in elevation_roles:
            elevation_roles.append(role.id)
        await ctx.send(f"Role {role.name} has been elevated for all utility commands!")

    @module_base.subcommand("elevate_member", sub_cmd_description="Elevate certain member to run privileged commands")
    @interactions.check(interactions.is_owner())
    @interactions.slash_option(
        name = "member",
        description = "Member to be elevated",
        required = True,
        opt_type = interactions.OptionType.USER
    )
    async def cmd_elevateMember(self, ctx: interactions.SlashContext, member: interactions.User):
        if member.id not in elevation_members:
            elevation_members.append(member.id)
        await ctx.send(f"Member {member.display_name}({member.username}) has been elevated for all utility commands!")
    
    @module_base.subcommand("elevate_clear", sub_cmd_description="Clear all privilege elevations")
    @interactions.check(interactions.is_owner())
    async def cmd_elevateClear(self, ctx: interactions.SlashContext):
        elevation_members.clear()
        elevation_roles.clear()
        await ctx.send("All privilege elevations have been removed!")

    @module_group.subcommand("members_older_than", sub_cmd_description="(Privileged) Get the list of members whose join date is longer than...")
    @interactions.check(my_check)
    @interactions.slash_option(
        name = "weeks",
        description = "Joined longer than...",
        required = False,
        opt_type = interactions.OptionType.INTEGER
    )
    @interactions.slash_option(
        name = "days",
        description = "Joined longer than...",
        required = False,
        opt_type = interactions.OptionType.INTEGER
    )
    @interactions.slash_option(
        name = "hours",
        description = "Joined longer than...",
        required = False,
        opt_type = interactions.OptionType.INTEGER
    )
    async def cmd_guild_membersOlderThan(self, ctx: interactions.SlashContext, weeks: int = 0, days: int = 30, hours: int = 0):
        await ctx.defer()
        now: interactions.Timestamp = interactions.Timestamp.now()
        td: datetime.timedelta = datetime.timedelta(days=days, weeks=weeks, hours=hours)
        channel: interactions.TYPE_GUILD_CHANNEL = ctx.channel
        valid_members: list[interactions.Member] = [mem for mem in ctx.guild.members if now - mem.joined_at >= td and not mem.bot]
        valid_members_str: list[str] = [f"- {mem.display_name}({mem.username}) ({now.__sub__(mem.joined_at).days} days)" for mem in valid_members]
        pag: Paginator = Paginator.create_from_string(self.bot, '\n'.join(valid_members_str), prefix=f"### Members joined more than {weeks}w{days}d{hours}h")
        await pag.send(ctx)
        async with aiofiles.tempfile.NamedTemporaryFile(prefix=f"users_{weeks}w_{days}d_{hours}h-", suffix=".txt", delete=False) as afp:
            write_str: str = str([str(mem.id) for mem in valid_members])
            await afp.write(str.encode(write_str))
            filename: str = afp.name
            await afp.close()
            await channel.send(f"All members joined more than {weeks}w{days}d{hours}h", file=filename)
            await aiofiles.os.remove(filename)

    @module_group_c.subcommand("rate_limit", sub_cmd_description="(Privileged) Rate limit a channel")
    @interactions.check(my_check)
    @interactions.slash_option(
        name = "channel",
        description = "The channel to set the rate limit",
        required = True,
        opt_type = interactions.OptionType.CHANNEL
    )
    @interactions.slash_option(
        name = "rate",
        description = "How many seconds before user can send another message",
        required = True,
        opt_type = interactions.OptionType.INTEGER
    )
    async def cmd_channel_rate_limit(self, ctx: interactions.SlashContext, channel: interactions.TYPE_GUILD_CHANNEL, rate: int) -> None:
        await ctx.send(f"Setting the rate limit of `{rate}` to {channel.mention}...")
        ctx_ch: interactions.MessageableMixin = ctx.channel
        rate = 0 if rate <= 0 else rate
        if isinstance(channel, interactions.GuildForum) or hasattr(channel, "default_forum_layout"):
            channel.rate_limit_per_user = rate
            active_posts: list[interactions.GuildForumPost] = await channel.fetch_posts()
            for post in active_posts:
                await post.edit(rate_limit_per_user=rate)
            await ctx_ch.send(f"Everyone in {channel.mention} can send message every `{rate}` seconds!")
            return
        await ctx_ch.send("This channel type is not implemented!")

    @module_group_c.subcommand("archive", sub_cmd_description="(Privileged) Archive a forum post")
    @interactions.check(my_check)
    @interactions.slash_option(
        name = "locked",
        description = "Whether to lock the post as well",
        required=False,
        opt_type=interactions.OptionType.INTEGER,
        choices=[
            interactions.SlashCommandChoice(name="true", value=1),
            interactions.SlashCommandChoice(name="false", value=0)
        ]
    )
    @interactions.slash_option(
        name = "reason",
        description = "The reason to archive this post",
        required = False,
        opt_type = interactions.OptionType.STRING
    )
    async def cmd_channel_archive(self, ctx: interactions.SlashContext, locked: Optional[int] = 0, reason: Optional[str] = "Reason not given") -> None:
        channel: interactions.GuildChannel = ctx.channel
        if not isinstance(channel, interactions.ThreadChannel):
            await ctx.send("This is not a thread!")
            return
        await channel.archive(locked=(locked == 1), reason=reason)
        await ctx.send("This forum post is archived!")