from typing import Final
import os
from dotenv import load_dotenv
import discord
from discord import Intents, Client, Embed
from responses import tarnishedLists
from discord import app_commands
from enum import Enum
import re

# Load token from somewhere safe
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
GUILD = None

class WordType(Enum):
    Template = 0
    Category = 1
    Word = 2
    Conjunction = 3
    
def getwordList(listType: WordType, key = None): return tarnishedLists[listType][key] if listType == WordType.Word else tarnishedLists[listType]
        
# Bot Setup
intents: Intents = Intents.default()
client: Client = Client(intents=intents)
tree: app_commands.CommandTree = app_commands.CommandTree(client)

def constructOptionsList(sourceList:list[str], default: str) -> list[discord.SelectOption]:
        return [discord.SelectOption(label = item, 
                                     default = item==default
                                     ) for item in sourceList]    

class DropdownSelect(discord.ui.Select):
    def __init__(self, droptype: WordType, chunk: bool):
        super().__init__(row=3)
        self.view: Menu =  self.view
        self.update(droptype, chunk)
    
    def update(self, droptype: WordType, chunk: bool):
        self.chunk = chunk
        self.droptype: WordType = droptype
        self.updateOptions
        self.disabled = chunk and self.view.chunk2disabled
    
    def updateOptions(self)-> None:
        self.options = constructOptionsList(
            getwordList(self.droptype, self.view.message[WordType.Category][self.chunk]), 
            self.view.message[self.droptype][self.chunk])
        
    
    async def callback(self, interaction: discord.Interaction):
        self.view.message[self.droptype][self.chunk] = self.values[0]
        mybutton: discord.ui.Button = self.view.buttons[self.droptype][self.chunk]
        mybutton.label = f"{self.droptype.name}: {self.view.message[self.droptype][self.chunk]}"
        self.updateOptions()
        if self.droptype == WordType.Category:
            self.view.message[WordType.Word][self.chunk] = tarnishedLists[WordType.Word][self.view.message[WordType.Category][self.chunk]][0]
            wordbutton: discord.ui.Button = self.view.buttons[WordType.Word][self.chunk]
            wordbutton.label = f"{WordType.Word.name}: {self.view.message[WordType.Word][self.chunk]}"
            self.view.updateButton(wordbutton)
            self.view.dropdown.update(WordType.Word,self.chunk)
        elif self.droptype == WordType.Conjunction:
            self.view.chunk2disabled = self.view.message[WordType.Conjunction][0] == tarnishedLists[WordType.Conjunction][0]
            for button in self.view.buttons[0:3]:
                button[1].disabled = self.view.chunk2disabled
        await interaction.response.edit_message(embed=self.view.getEmbed(),view=self.view)

class switchButton(discord.ui.Button):
    def __init__(self, buttonType: WordType, chunk: bool):
        super().__init__(style=discord.ButtonStyle.blurple)
        self.buttonType: WordType = buttonType
        self.chunk: bool = chunk
        self.view: Menu = self.view
        self.label=f"{buttonType.name}: {getwordList(buttonType,self.view.message[WordType.Category][self.chunk])}"
        self.row = 2 if self.chunk else int(self.buttonType == WordType.Conjunction)
        self.disabled=chunk
        
    async def callback(self, interaction: discord.Interaction):
        self.view.updateButton(self)
        self.view.dropdown.update(self.buttonType,self.chunk)
        await interaction.response.edit_message(embed=self.view.getEmbed(),view=self.view)
    
class Menu(discord.ui.View):
    def __init__(self, user: str):
        super().__init__()
        self.message = [
            [tarnishedLists[WordType.Template][0],tarnishedLists[WordType.Template][0]],
            [tarnishedLists[WordType.Category][0],tarnishedLists[WordType.Category][0]],
            [tarnishedLists[WordType.Word][0],tarnishedLists[WordType.Word][0]],
            [tarnishedLists[WordType.Conjunction][0]]
        ]
        self.buttons:list[list[switchButton]] = [
            [switchButton(WordType.Template,False),switchButton(WordType.Template,True)],
            [switchButton(WordType.Category, False),switchButton(WordType.Category, True)],
            [switchButton(WordType.Word, False),switchButton(WordType.Word, True)],
            [switchButton(WordType.Conjunction,False)]
        ]
        self.username: str = user
        self.chunk2disabled: bool = True
        for chunk in range(2):
            for wtype in range (3):
                self.add_item(self.buttons[wtype][chunk])
            if not chunk: self.add_item(self.buttons[WordType.Conjunction][0])
        self.dropdown: DropdownSelect = DropdownSelect(WordType.Template, False)
        self.add_item(self.dropdown)
        self.currbutton: discord.ui.Button = self.buttons[WordType.Template][0]
        self.currbutton.disabled = True
        self.currbutton.style = discord.ButtonStyle.gray
        
    def getChunk(self, chunk=False) -> str: return re.sub("____", self.message[WordType.Word][chunk],self.message[WordType.Template][chunk])
    
    def getMessage(self, user) -> str:
        firstHalf = self.getChunk()
        message = firstHalf
        if self.message[WordType.Conjunction][0] != tarnishedLists[WordType.Conjunction][0]:
            secondHalf = f"{self.message[WordType.Conjunction][0]} {self.getChunk(True)}"
            message += secondHalf if self.message[WordType.Conjunction][0] == "," else f" {secondHalf}"
        return f"> {message}\n \\- {user}"
    
    def getEmbed(self) -> Embed: return Embed(title="Message Preview",description = self.getMessage(self.username))
    
    def updateButton(self, button: discord.ui.Button) -> None:
        self.currbutton.style = discord.ButtonStyle.blurple
        self.currbutton.disabled = False
        
        button.style = discord.ButtonStyle.gray
        button.disabled = True
        self.currbutton = button
        
    @discord.ui.button(label="Send Message", style=discord.ButtonStyle.green, row=4)
    async def send_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.getMessage(self.username))
        await interaction.followup.delete_message(interaction.message.id)
        self.stop()

# Handle startup
@client.event
async def on_ready() -> None:
    await tree.sync(guild=GUILD)
    print(f'{client.user} is now running')

@tree.command(name='tarnished', description='Use the UI to send a Tarnished Message', guild=GUILD)
async def tarnished(interaction: discord.Interaction):
    if interaction.is_guild_integration() and interaction.user.display_name != interaction.user.name:
        username: str = f"{interaction.user.display_name} ({interaction.user.name})"
    else:
        username: str  = interaction.user.name
    view: Menu = Menu(username)
    await interaction.response.send_message(view=view, ephemeral=True, embed=view.getEmbed())
   
# Main entry point
def main() -> None:
    client.run(token=TOKEN)
    
if __name__ == '__main__':
    main()