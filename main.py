from typing import Final
import os
from dotenv import load_dotenv
import discord
from discord import Intents, Client, Embed
from discord import app_commands
from enum import IntEnum
import re
import json
from itertools import starmap

# Load token from somewhere safe
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
GUILD = None

# Bot Setup
intents: Intents = Intents.default()
client: Client = Client(intents=intents)
tree: app_commands.CommandTree = app_commands.CommandTree(client)

# Load actual text data from json file into a list of format: 
# [
#   List[Templates]
#   List[Categories]
#   Dict{Categories:List[Words]}
#   List[Conjunctions]
# ]
tarnishedLists = json.load(open('./responses.json'))

class WordType(IntEnum):
    Template = 0
    Category = 1
    Word = 2
    Conjunction = 3
    
class Segment(IntEnum):
    First = 0
    Second = 1
    
def getwordList(listType: WordType, key: str = None) -> list[str]: 
    return tarnishedLists[listType][key] if listType == WordType.Word else tarnishedLists[listType]

def constructOptionsList(sourceList:list[str], defaultItem: str) -> list[discord.SelectOption]:
        return [discord.SelectOption(label = item, 
                                     default = item==defaultItem
                                     ) for item in sourceList]    
def getFirstWord(listType:WordType, key: str = None) -> str:
    if not key and listType == WordType.Word: 
        key = getwordList(WordType.Category)[0]
    return getwordList(listType,key)[0]

class Menu(discord.ui.View):
    _defaultgrid = [[(segment,wtype)
                     for wtype in WordType
                     if (segment == Segment.First or wtype != WordType.Conjunction)]
                    for segment in Segment]
    _defaultmessage = list(map(lambda row : list(starmap(lambda _, wtype: getFirstWord(wtype), row)), _defaultgrid))
   
    
    def _addbutton(self, segment, wtype):
        newbutton = switchButton(wtype,segment, self.message[segment][wtype])
        self.add_item(newbutton)
        return newbutton
    
    def __init__(self, user: str):
        super().__init__()
        self.message = self._defaultmessage.copy()
        self.buttons = list(map(lambda row : list(starmap(self._addbutton, row)),self._defaultgrid))
        self.username: str = user
        self.isSecondSegmentDisabled: bool = True
        self.dropdown: DropdownSelect = DropdownSelect(WordType.Template, Segment.First, self.message)
        self.add_item(self.dropdown)
        self._currbutton=None
        self.currbutton: discord.ui.Button = self.buttons[Segment.First][WordType.Template]
        
    def getMessageSegment(self, segment:Segment) -> str: 
        return re.sub("____", self.message[segment][WordType.Word],self.message[segment][WordType.Template])
    
    def getMessage(self, user=None) -> str:
        if not user: user = self.username
        firstHalf = self.getMessageSegment(Segment.First)
        message = firstHalf
        conj = self.message[Segment.First][WordType.Conjunction]
        if conj != getFirstWord(WordType.Conjunction):
            if conj != ",": conj = " " + conj
            secondHalf = f"{conj} {self.getMessageSegment(Segment.Second)}"
            message += secondHalf
        return f"> {message}\n-# \\-{user}"
    
    def getEmbed(self) -> Embed: return Embed(title="Message Preview", description = self.getMessage(self.username))
    
    @property
    def currbutton(self):
        return self._currbutton
    
    @currbutton.setter
    def currbutton(self, button: discord.ui.Button):
        if self._currbutton is not None:
            self._currbutton.disabledState = False
        self._currbutton = button
        self.currbutton.disabledState = True
        
    @discord.ui.button(label="Send Message", style=discord.ButtonStyle.green, row=4)
    async def send_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.getMessage(self.username))
        await interaction.followup.delete_message(interaction.message.id)
        self.stop()

class DropdownSelect(discord.ui.Select):
    view: Menu
    def __init__(self, droptype: WordType, segment: Segment, message:list):
        self.segment = segment
        self.droptype: WordType = droptype
        super().__init__(row=3,
                         options = constructOptionsList(
                                getwordList(self.droptype, message[self.segment][WordType.Category]), 
                                message[self.segment][self.droptype]))
    
    def update(self, droptype: WordType, segment: Segment):
        self.segment = segment
        self.droptype: WordType = droptype
        self.updateOptions()
        self.disabled = segment and self.view.isSecondSegmentDisabled
    
    def updateOptions(self)-> None:
        self.options = constructOptionsList(
            getwordList(self.droptype, self.view.message[self.segment][WordType.Category]), 
            self.view.message[self.segment][self.droptype])
        
    
    async def callback(self, interaction: discord.Interaction):
        self.view.message[self.segment][self.droptype] = self.values[0]
        mybutton: discord.ui.Button = self.view.buttons[self.segment][self.droptype]
        mybutton.label = f"{self.droptype.name}: {self.view.message[self.segment][self.droptype]}"
        self.updateOptions()
        if self.droptype == WordType.Category:
            self.view.message[self.segment][WordType.Word] = getFirstWord(WordType.Word, self.view.message[self.segment][WordType.Category])
            wordbutton: discord.ui.Button = self.view.buttons[self.segment][WordType.Word]
            wordbutton.label = f"{WordType.Word.name}: {self.view.message[self.segment][WordType.Word]}"
            self.view.currbutton = wordbutton
            self.view.dropdown.update(WordType.Word,self.segment)
        elif self.droptype == WordType.Conjunction:
            self.view.isSecondSegmentDisabled = self.view.message[Segment.First][WordType.Conjunction] == getFirstWord(WordType.Conjunction)
            for button in self.view.buttons[Segment.Second]:
                button.disabledState = self.view.isSecondSegmentDisabled
        await interaction.response.edit_message(embed=self.view.getEmbed(),view=self.view)

class switchButton(discord.ui.Button):
    view: Menu
    def __init__(self, buttonType: WordType, segment: Segment, submessage:str):
        super().__init__(style=discord.ButtonStyle.blurple)
        self.buttonType: WordType = buttonType
        self.segment: Segment = segment
        self.label=f"{buttonType.name}: {submessage}"
        self.row = 2 if self.segment == Segment.Second else int(self.buttonType == WordType.Conjunction)
        self.disabledState=segment
        
    async def callback(self, interaction: discord.Interaction):
        self.view.currbutton = self
        self.view.dropdown.update(self.buttonType,self.segment)
        await interaction.response.edit_message(embed=self.view.getEmbed(),view=self.view)
    
    @property
    def disabledState(self):
        return self.disabled
    
    @disabledState.setter
    def disabledState(self,disabled:bool):
        self.style = discord.ButtonStyle.gray if disabled else discord.ButtonStyle.blurple
        self.disabled = disabled

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