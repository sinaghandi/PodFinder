import discord
import discord.ui
from discord.ui import Button, View
from discord.ext import commands
from config import BOT_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def update_embed(participants: [discord.Member], needed):
    """Generate an embed with updated names and countdown value.

    Args:
        participants: String with concatenated names to update the embed with.
        needed: Integer specifying how many more are needed.

    Returns:
        discord.Embed: A discord.Embed object with the updated information.
    """
    str_names = ", ".join(member.display_name for member in participants)
    embed = discord.Embed(color=discord.Color.random())
    if needed == 0:
        embed.add_field(
            name=str_names, value=f"can fire their pod. Good luck, have fun!"
        )
    else:
        embed.add_field(name=str_names, value=f"need {needed} more for their pod!")
    return embed


class EmbedView(View):
    def __init__(self, needed, original_participants, message_id, original_author):
        super().__init__()
        self.needed = needed
        self.message_id = message_id
        self.participants = original_participants

        self.add_button = Button(
            label="Count me in!",
            style=discord.ButtonStyle.green,
            emoji="👍",
        )
        self.remove_button = Button(
            label="Actually, I can't make it.",
            style=discord.ButtonStyle.red,
        )
        self.add_button.callback = self.add_button_callback
        self.remove_button.callback = self.remove_button_callback
        self.add_item(self.add_button)
        self.add_item(self.remove_button)

    async def add_button_callback(self, interaction: discord.Interaction):
        if interaction.user in self.participants:
            await interaction.response.send_message(
                "You're already in the pod! Sit tight till you have enough to fire a "
                "game.",
                ephemeral=True,
            )
        else:
            self.needed -= 1
            self.participants.append(interaction.user)
            print(self.participants)
            embed = update_embed(self.participants, self.needed)
            # if no more people are needed, remove all buttons from view
            if self.needed == 0:
                for item in list(self.children):
                    if isinstance(item, Button):
                        self.remove_item(item)
                mentions = [user.mention for user in self.participants]
                await interaction.message.channel.send(
                    f"{' '.join(mentions)} game time!"
                )
            else:
                await interaction.response.send_message(
                    "You've been added to the pod! I'll ping you when there's enough "
                    "for your game.",
                    ephemeral=True,
                )
            await interaction.message.edit(view=self, embed=embed)

    async def remove_button_callback(self, interaction: discord.Interaction):
        if interaction.user in self.participants:
            await interaction.response.send_message(
                "You've been removed from the pod.",
                ephemeral=True,
            )
            self.participants.remove(interaction.user)
            if len(self.participants) == 0:
                await interaction.message.delete()
            else:
                self.needed += 1
                embed = update_embed(self.participants, self.needed)
                await interaction.message.edit(view=self, embed=embed)
        else:
            await interaction.response.send_message(
                "Oops! Looks like you weren't in the pod anyway.",
                ephemeral=True,
            )


@bot.command()
async def need(context, needed: int, *members: discord.Member):
    """Command to initialize the countdown and display it.

    Usage: !need <number> <name1> <name2> ...
    """
    participants = list(members)
    if context.author not in participants:
        participants.append(context.author)
    try:
        if needed <= 0:
            raise ValueError(
                "The number of needed members must be an integer greater than 0."
            )
    except IndexError:
        await context.send(
            "Usage: !need <number> <name1> <name2> ... \nThe number needed and at least"
            "one name must be provided."
        )
        return
    except ValueError as e:
        await context.send(f"Usage: !need <number> <name1> <name2> ... \nError: {e}")
        return

    embed = update_embed(participants, needed)

    view = EmbedView(needed, participants, context.message.id, context.author)

    await context.send(view=view, embed=embed)


@need.error
async def need_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send(
            f"Error: {error}\nPlease mention whatever members you would like added to "
            f"the pod."
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        if str(error.param) == "needed: int":
            await ctx.send("You must provide the number of needed members.")
        else:
            await ctx.send(
                "An error occurred. Usage: !need <number> <@user1> <@user2> ... "
            )
    else:
        await ctx.send(
            "An error occurred. Usage: !need <number> <@user1> <@user2> ... "
        )


bot.run(BOT_TOKEN)
