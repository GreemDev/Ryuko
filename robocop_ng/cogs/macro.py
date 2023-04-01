from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context, BucketType

from robocop_ng.helpers.checks import check_if_staff
from robocop_ng.helpers.macros import (
    get_macro,
    add_macro,
    edit_macro,
    remove_macro,
    get_macros_dict,
    add_aliases,
    remove_aliases,
    clear_aliases,
)


class Macro(Cog):
    @commands.cooldown(3, 30, BucketType.member)
    @commands.command(aliases=["m"])
    async def macro(self, ctx: Context, target: Optional[discord.Member], key: str):
        await ctx.message.delete()
        if len(key) > 0:
            text = get_macro(key)
            if text is not None:
                if target is not None:
                    await ctx.send(f"{target.mention}:\n{text}")
                else:
                    if ctx.message.reference is not None:
                        await ctx.send(text, reference=ctx.message.reference, mention_author=True)
                    else:
                        await ctx.send(text)
            else:
                await ctx.send(
                    f"{ctx.author.mention}: The macro '{key}' doesn't exist."
                )

    @commands.check(check_if_staff)
    @commands.command(name="macroadd", aliases=["ma", "addmacro", "add_macro"])
    async def add_macro(self, ctx: Context, key: str, *, text: str):
        if add_macro(key, text):
            await ctx.send(f"Macro '{key}' added!")
        else:
            await ctx.send(f"Error: Macro '{key}' already exists.")

    @commands.check(check_if_staff)
    @commands.command(name="aliasadd", aliases=["addalias", "add_alias"])
    async def add_alias_macro(self, ctx: Context, existing_key: str, *new_keys: str):
        if len(new_keys) == 0:
            await ctx.send("Error: You need to add at least one alias.")
        else:
            if add_aliases(existing_key, list(new_keys)):
                await ctx.send(f"Added {len(new_keys)} aliases to macro '{existing_key}'!")
            else:
                await ctx.send(f"Error: No new and unique aliases found.")

    @commands.check(check_if_staff)
    @commands.command(name="macroedit", aliases=["me", "editmacro", "edit_macro"])
    async def edit_macro(self, ctx: Context, key: str, *, text: str):
        if edit_macro(key, text):
            await ctx.send(f"Macro '{key}' edited!")
        else:
            await ctx.send(f"Error: Macro '{key}' not found.")

    @commands.check(check_if_staff)
    @commands.command(name="aliasremove", aliases=[
        "aliasdelete", "delalias", "aliasdel", "removealias", "remove_alias", "delete_alias"
    ])
    async def remove_alias_macro(self, ctx: Context, existing_key: str, *remove_keys: str):
        if len(remove_keys) == 0:
            await ctx.send("Error: You need to remove at least one alias.")
        else:
            if remove_aliases(existing_key, list(remove_keys)):
                await ctx.send(f"Removed {len(remove_keys)} aliases from macro '{existing_key}'!")
            else:
                await ctx.send(f"Error: None of the specified aliases were found for macro '{existing_key}'.")

    @commands.check(check_if_staff)
    @commands.command(
        name="macroremove",
        aliases=[
            "mr",
            "md",
            "removemacro",
            "remove_macro",
            "macrodel",
            "delmacro",
            "delete_macro",
        ],
    )
    async def remove_macro(self, ctx: Context, key: str):
        if remove_macro(key):
            await ctx.send(f"Macro '{key}' removed!")
        else:
            await ctx.send(f"Error: Macro '{key}' not found.")

    @commands.check(check_if_staff)
    @commands.command(name="aliasclear", aliases=["clearalias", "clear_alias"])
    async def clear_alias_macro(self, ctx: Context, existing_key: str):
        if clear_aliases(existing_key):
            await ctx.send(f"Removed all aliases of macro '{existing_key}'!")
        else:
            await ctx.send(f"Error: No aliases found for macro '{existing_key}'.")

    @commands.cooldown(3, 30, BucketType.channel)
    @commands.command(name="macros", aliases=["ml", "listmacros", "list_macros"])
    async def list_macros(self, ctx: Context):
        macros = get_macros_dict()
        if len(macros["macros"]) > 0:
            macros = [f"- {key}\n" for key in sorted(macros["macros"].keys())]
            message = "📝 **Macros**:\n"
            for macro_key in macros:
                message += macro_key
            await ctx.send(message)
        else:
            await ctx.send("Couldn't find any macros.")

    @commands.cooldown(3, 30, BucketType.channel)
    @commands.command(name="aliases", aliases=["listaliases", "list_aliases"])
    async def list_aliases(self, ctx: Context, existing_key: str):
        macros = get_macros_dict()
        existing_key = existing_key.lower()
        if existing_key in macros["aliases"].keys():
            message = f"📝 **Aliases for '{existing_key}'**:\n"
            for alias in sorted(macros["aliases"][existing_key]):
                message += f"- {alias}\n"
            await ctx.send(message)
        else:
            await ctx.send(f"Couldn't find any aliases for macro '{existing_key}'.")


async def setup(bot):
    await bot.add_cog(Macro(bot))
