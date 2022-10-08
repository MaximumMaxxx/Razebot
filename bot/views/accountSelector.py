import discord
from lib.get_accs import get_acc


def accountSelectorFactory(options: "list[discord.SelectOption]", region: "dict[str, str]", callback: "callable" = get_acc):
    """
    Returns an account selector that lets you select an account from a list of accounts

    :param options: The list of accounts to select from type: list[discord.SelectOption]
    :param region: The region to select from type: dict[str, str] (key: name#tag, value: region: str)

    :param callback: The callback to call when an account is selected type: callable (default: accHelpers.get_acc) requireds 3 arguments: ctx, account, region return type: discord.Embed
    """
    class AccountSelector(discord.ui.View):
        result = None
        regions = region

        @discord.ui.select(
            placeholder="Select an account",
            min_values=1,
            max_values=1,
            options=options

        )
        async def select_callback(self, select, interation):
            name, tag = select.values[0].split("#")
            await interation.response.edit_message(
                embed=await get_acc(
                    name,
                    tag,
                    self.regions[f"{name}#{tag}"]
                ),
                view=None
            )

    return AccountSelector()
