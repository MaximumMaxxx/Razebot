import discord
import lib.accHelpers as accHelpers


def accountSelectorFactory(options: "list[discord.SelectOption]", region: "dict[str, str]"):
    class AccountSelector(discord.ui.View):
        result = None
        regions = region

        """
        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
        async def cancel_callback(self, button, interaction):
            for child in self.children:
                child.disabled = True
            self.result = None
            await self.message.edit(content="Cancelled", view=self)

        @discord.ui.button(label="Select", style=discord.ButtonStyle.green, emoji="✔️")
        async def select_callback(self, button, interaction):
            for child in self.children:
                child.disabled = True
            self.message.edit(view=self)
            name, tag = self.result.value.split("#")
            interaction.response.edit(
                embed=accHelpers.get_acc(
                    name,
                    tag,
                    self.regions[f"{name}#{tag}"]
                )
            )
        """

        @discord.ui.select(
            placeholder="Select an account",
            min_values=1,
            max_values=1,
            options=options

        )
        async def select_callback(self, select, interation):
            name, tag = select.values[0].split("#")
            # await interation.defer()
            # await interation.response.edit_message(
            #    content="Please wait a moment while we fetch your account..."
            # )
            await interation.response.edit_message(
                embed=await accHelpers.get_acc(
                    name,
                    tag,
                    self.regions[f"{name}#{tag}"]
                ),
                view=None
            )

    return AccountSelector()
