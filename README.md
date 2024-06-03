# Discord Utility commands module
A few useful utility commands for Discord guild management and bot development.

## Safety settings
The default setting is that only the bot owner can run all commands including the privileged ones. However, we can add the others to run these commands. **_Only the bot owner can run these commands in this section._**
- `/utility elevate_role` elevates a role to run privileged commands
- `/utility elevate_member` elevates a member to run privileged commands
- `/utility elevate_clear` clears all elevation settings
- `/utility elevate_show` displays the elevation settings

## Guild
- `/utility guild members_older_than` returns all the members who join this guild more than `a` weeks `b` days `c` hours. Default to be 30 days. **_This Command is Privileged._**

## Channel
- `/utility channel rate_limit` set the rate limit per user of a channel. **_This Command is Privileged._**
- `/utility channel archive` archives a post or thread. It can also lock and give a reason with optional parameters. **_This Command is Privileged._**
- `/utility channel delete_user_messages` deletes all messages from a member in a certain channel. **_This Command is Preivileged._**

## User
- `/utility user remove_all_roles` removes all roles from a member in a guild. **_This Command is Privileged._**