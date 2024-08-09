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
from typing import Optional, cast
import asyncio
import traceback
from src import logutil

logger = logutil.init_logger("Discord-Utilities")
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
    module_group_u: interactions.SlashCommand = module_base.group(
        name = "user",
        description = "User related utilities"
    )
    cmd_guild_deleteAllUrMsg_members: list[int] = []

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
        
    @module_group.subcommand("delete_all_ur_msg", sub_cmd_description="Delete all your messages in this guild and soft ban you to further delete msg")
    @interactions.max_concurrency(interactions.Buckets.GUILD, 2)
    async def cmd_guild_deleteAllUrMsg(self, ctx: interactions.SlashContext) -> None:
        if ctx.author.id in self.cmd_guild_deleteAllUrMsg_members:
            await ctx.send("You are already running this command!", ephemeral=True)
            return
        self.cmd_guild_deleteAllUrMsg_members.append(ctx.author.id)
        this_channel: interactions.GuildChannel = ctx.channel
        current_author: interactions.User = ctx.author
        confirmation_msg: str = "DELETE ME"
        modal_timeout: int = 60
        modal: interactions.Modal = interactions.Modal(
            interactions.ParagraphText(
                label=f"Please enter '{confirmation_msg}' in {modal_timeout} seconds",
                placeholder=f"{confirmation_msg}"
            ),
            title="Are you sure?"
        )
        await ctx.send_modal(modal)
        try:
            modal_ctx: interactions.ModalContext = await ctx.bot.wait_for_modal(modal, timeout=modal_timeout)
        except asyncio.TimeoutError:
            self.cmd_guild_deleteAllUrMsg_members.remove(current_author.id)
            return
        modal_text: str = list(modal_ctx.responses.values())[0]
        all_main_channels: list[interactions.GuildChannel] = await ctx.guild.fetch_channels()
        async def __delete_reactions_from_message(msg: interactions.Message) -> None:
            try:
                for react in msg.reactions:
                    usr_list: list[interactions.User] = await react.users().fetch()
                    if any(current_author.id == usr.id for usr in usr_list):
                        await msg.remove_reaction(react.emoji, member=current_author)
            except Exception as e:
                logger.error(traceback.format_exc())
        def __is_delete(msg: Optional[interactions.Message], user_id: int) -> bool:
            return msg and (msg.author.id == user_id or (msg.interaction_metadata and msg.interaction_metadata._user_id == user_id))
        async def __delete_all_msgs_in_messagable(channel: interactions.MessageableMixin) -> None:
            """
            Delete all messages in MessagableMixin. Skip extra exceptions.
            """
            if channel is None:
                logger.error("Channel is None")
                return
            archived: bool = False
            archived_operated: bool = False
            skip_this_loop: bool = False
            msg: interactions.Message = None
            if isinstance(channel, interactions.ThreadChannel):
                channel: interactions.ThreadChannel = cast(interactions.ThreadChannel, channel)
                archived = channel.archived
            history: interactions.ChannelHistory = channel.history(0)
            while True:
                try:
                    if not skip_this_loop:
                        msg = await history.__anext__()
                        skip_this_loop = False
                    if __is_delete(msg, current_author.id):
                        if archived and not archived_operated:
                            try:
                                await channel.edit(archived=False)
                                archived_operated = True
                            except Exception:
                                logger.error(traceback.format_exc())
                                return
                        await msg.delete()
                    else:
                        await __delete_reactions_from_message(msg)
                except StopAsyncIteration:
                    break
                except interactions.errors.HTTPException as e:
                    match int(e.code):
                        case 50083:
                            """Operation in archived thread"""
                            skip_this_loop = True
                            archived = True
                            try:
                                await channel.edit(archived=False)
                            except Exception:
                                logger.error(traceback.format_exc())
                                return
                        case 10003:
                            """Unknown channel"""
                            return
                        case 10008:
                            """Unknown message"""
                            return
                        case 50001:
                            """No Access"""
                            return
                        case 50013:
                            """Lack permission"""
                            return
                        case 50021:
                            """Cannot execute on system message"""
                            pass
                        case 160005:
                            """Thread is locked"""
                            pass
                        case _:
                            """Default"""
                            pass
                except Exception:
                    logger.error(traceback.format_exc())
            if archived:
                try:
                    await channel.edit(archived=True)
                except Exception:
                    logger.error(traceback.format_exc())
        if modal_text.strip() == confirmation_msg:
            await modal_ctx.send("Deleting your messages...", ephemeral=True)
            for ch in all_main_channels:
                if isinstance(ch, interactions.MessageableMixin):
                    ch = cast(interactions.MessageableMixin, ch)
                    await __delete_all_msgs_in_messagable(ch)
                    ch = cast(interactions.GuildText, ch)
                    if isinstance(ch, interactions.GuildText):
                        thread_list: interactions.ThreadList = await ch.fetch_active_threads()
                        for thread in thread_list.threads:
                            await __delete_all_msgs_in_messagable(thread)
                        thread_list = await ch.fetch_archived_threads()
                        for thread in thread_list.threads:
                            await __delete_all_msgs_in_messagable(thread)
                if isinstance(ch, interactions.GuildForum):
                    ch: interactions.GuildForum = cast(interactions.GuildForum, ch)
                    posts = ch.get_posts()
                    for post in posts:
                        await __delete_all_msgs_in_messagable(post)
                    _posts = await self.bot.http.list_public_archived_threads(channel_id=ch.id)
                    posts = [int(_["id"]) for _ in _posts["threads"]]
                    for p in posts:
                        post: interactions.GuildForumPost = await self.bot.fetch_channel(channel_id=p)
                        await __delete_all_msgs_in_messagable(post)
            await this_channel.send("Message deletion complete!")
            _dm_ch = current_author.get_dm()
            if _dm_ch:
                await _dm_ch.send(f"Message delete in {this_channel.guild.name} completed!")
        else:
            await modal_ctx.send("Operation cancelled!", ephemeral=True)
        self.cmd_guild_deleteAllUrMsg_members.remove(current_author.id)

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

    @module_group_c.subcommand(
        "delete_user_messages", sub_cmd_description="Delete all messages from a specific user in a channel"
    )
    @interactions.check(my_check)
    @interactions.slash_option(
        "user",
        "The member to delete the message",
        interactions.OptionType.USER,
        required=True
    )
    @interactions.slash_option(
        "channel_id",
        "The channel ID of the channel",
        interactions.OptionType.STRING,
        required=True
    )
    async def cmd_channel_delete_messages(self, ctx: interactions.SlashContext, user: interactions.Member, channel_id: str):
        try:
            channel = await self.bot.fetch_channel(channel_id)
        except:
            await ctx.send("Channel ID is invalid!", ephemeral=True)
            return
        dm = await user.fetch_dm(force=True)
        button: interactions.Button = interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            label="Click to agree deleting messages"
        )
        dm_msg: interactions.Message = await dm.send(
            content=f"{ctx.author.mention} wants to delete all your messages in {channel.mention}",
            components=[button]
            )
        await ctx.send("Awaiting for user's confirmation. Will timeout in 2 minutes.", ephemeral=True)
        try:
            component = await self.bot.wait_for_component(components=button, timeout=120)
        except TimeoutError:
            await ctx.channel.send("The user didn't agree to delete the messages within 2 minutes.")
        else:
            await ctx.channel.send("The user agreed to delete the message. Proceed with the deletion.")
            await component.ctx.send("The user agreed to delete the message. Proceed with the deletion.")
            msg_to_delete: list[interactions.Message] = []
            count_msg_deleted: int = 0
            count_msg_not_deleted: int = 0
            async for message in channel.history(limit=0):
                if message.author.id == user.id:
                    msg_to_delete.append(message)
            archived: bool = channel.archived
            if archived:
                await channel.edit(archived=False)
            for msg in msg_to_delete:
                if msg is None:
                    continue
                try:
                    await channel.delete_message(msg)
                    count_msg_deleted += 1
                except:
                    count_msg_not_deleted += 1
            if archived:
                await channel.edit(archived=True)
            await dm.send(f"Messages Deleted. Deleted {count_msg_deleted} messages. {count_msg_not_deleted} messages failed to delete.")
            await ctx.channel.send(f"Message deletion completed. Deleted {count_msg_deleted} messages. {count_msg_not_deleted} messages failed to delete.")
        finally:
            button.disabled = True
            await dm_msg.edit(components=button)

    @module_group_u.subcommand(
        "remove_all_roles", sub_cmd_description="Remove all of the roles from a user"
    )
    @interactions.check(my_check)
    @interactions.slash_option(
        "user",
        "The member to remove the role",
        interactions.OptionType.USER,
        required=True
    )
    async def cmd_user_remove_all_roles(self, ctx: interactions.SlashContext, user: interactions.Member) -> None:
        await user.remove_roles(user.roles)
        await ctx.send(f"User {user.display_name} removed all roles")
