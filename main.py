from typing import Final
import os
from dotenv import load_dotenv
import discord
from discord import Intents, Client, Embed
from responses import TarnishedTalk
from discord import app_commands

# Load token from somewhere safe
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
GUILD = None #: discord.Object = discord.Object(id=445778700051415040)


# Bot Setup
intents: Intents = Intents.default()
client: Client = Client(intents=intents)
tree: app_commands.CommandTree = app_commands.CommandTree(client)

def constructOptionsList(sourceList, default: str | int | None = None ) -> list[discord.SelectOption]:
        if default == 0: default = sourceList[0]
        return [discord.SelectOption(label = item, 
                                     default = item==default
                                     ) for item in sourceList]    

class DropdownSelect(discord.ui.Select):
    def __init__(self, sourceList, droptype: int, default: str | int | None = None, disabled = False):
        self.droptype = droptype
        if default == 0: default = sourceList[0]
        options =  [discord.SelectOption(label = item, 
                                     default = item==default
                                     ) for item in sourceList]
        super().__init__(options=options, row=3)
        self.disabled = disabled
    
    def update(self, sourceList, droptype: int, default: str | int | None = None, disabled = False):
        self.droptype = droptype
        if default == 0: default = sourceList[0]
        self.options =  [discord.SelectOption(label = item, 
                                     default = item==default
                                     ) for item in sourceList]
        self.disabled = disabled
    
    async def callback(self, interaction: discord.Interaction):
        myview: Menu = self.view
        
        match self.droptype:
            case 0:
                myview.tarnished.templateFirst = self.values[0]
                mybutton: discord.ui.Button = myview.children[self.droptype]
                mybutton.label = f"Template: {myview.tarnished.templateFirst}"
                self.options= constructOptionsList(TarnishedTalk.templateList,default=myview.tarnished.templateFirst)
            case 1:
                if myview.tarnished.categoryFirst != self.values[0]:
                    myview.tarnished.categoryFirst = self.values[0]
                    mybutton: discord.ui.Button = myview.children[self.droptype]
                    mybutton.label = f"Category: {myview.tarnished.categoryFirst}"
                    self.options = constructOptionsList(TarnishedTalk.categoryList,default=myview.tarnished.categoryFirst)

                    myview.tarnished.wordFirst = TarnishedTalk.wordsList[myview.tarnished.categoryFirst][0]
                    wordbutton: discord.ui.Button = myview.children[self.droptype+1]
                    wordbutton.label = f"Word: {myview.tarnished.wordFirst}"
            case 2:
                myview.tarnished.wordFirst = self.values[0]
                mybutton: discord.ui.Button = myview.children[self.droptype]
                mybutton.label = f"Word: {myview.tarnished.wordFirst}"
                self.options = constructOptionsList(TarnishedTalk.wordsList[myview.tarnished.categoryFirst], default=myview.tarnished.wordFirst)
            case 3:
                myview.tarnished.conjunction = self.values[0]
                mybutton: discord.ui.Button = myview.children[self.droptype]
                mybutton.label = f"Conjunction: {myview.tarnished.conjunction}"
                for child in myview.children[4:7]:
                    child.disabled = myview.tarnished.conjunction == TarnishedTalk.conjunctionList[0]
                self.options = constructOptionsList(TarnishedTalk.conjunctionList, default=myview.tarnished.conjunction)
            case 4:
                myview.tarnished.templateSecond = self.values[0]
                mybutton: discord.ui.Button = myview.children[self.droptype]
                mybutton.label = f"Template: {myview.tarnished.templateSecond}"
                self.options= constructOptionsList(TarnishedTalk.templateList,default=myview.tarnished.templateSecond)
            case 5:
                if myview.tarnished.categorySecond != self.values[0]:
                    myview.tarnished.categorySecond = self.values[0]
                    mybutton: discord.ui.Button = myview.children[self.droptype]
                    mybutton.label = f"Category: {myview.tarnished.categorySecond}"
                    self.options = constructOptionsList(TarnishedTalk.categoryList,default=myview.tarnished.categorySecond)

                    myview.tarnished.wordSecond = TarnishedTalk.wordsList[myview.tarnished.categorySecond][0]
                    wordbutton: discord.ui.Button = myview.children[self.droptype+1]
                    wordbutton.label = f"Word: {myview.tarnished.wordSecond}"
            case 6:
                myview.tarnished.wordSecond = self.values[0]
                self.options = constructOptionsList(TarnishedTalk.wordsList[myview.tarnished.categorySecond], default=myview.tarnished.wordSecond)
                mybutton: discord.ui.Button = myview.children[self.droptype]
                mybutton.label = f"Word: {myview.tarnished.wordSecond}"
        await interaction.response.edit_message(embed=myview.getEmbed(),view=myview)

class Menu(discord.ui.View):
    # Dropdown setup
    dropdown: DropdownSelect = None
    currbutton: discord.ui.Button
    templateOptionsList: list[discord.SelectOption] = constructOptionsList(TarnishedTalk.templateList, default=0)
    categoryOptionsList: list[discord.SelectOption] = constructOptionsList(TarnishedTalk.categoryList, default=0)
    conjunctionOptionsList: list[discord.SelectOption] = constructOptionsList(TarnishedTalk.conjunctionList)
    
    def getSubcategoryOptionsList(self, key: str) -> list[discord.SelectOption]:
        return [discord.SelectOption(label=templ, default=templ == self.tarnished.wordFirst) for templ in TarnishedTalk.getWordSublist(key)]
    
    def __init__(self, user: str):
        super().__init__()
        self.tarnished: TarnishedTalk = TarnishedTalk()
        self.username: str = user
        self.dropdown = DropdownSelect(TarnishedTalk.templateList,0,self.tarnished.templateFirst)
        self.add_item(self.dropdown)
        self.currbutton = self.children[0]
        for child in self.children[4:7]:
            child.disabled = True
        self.currbutton.disabled = True
    
    def getEmbed(self) -> Embed: return Embed(title="Message Preview",description = f"> {self.tarnished.getMessage()}\n \\- {self.username}")
    def updateButton(self, button: discord.ui.Button) -> None:
        self.currbutton.style = discord.ButtonStyle.blurple
        self.currbutton.disabled = False
        
        button.style = discord.ButtonStyle.gray
        button.disabled = True
        self.currbutton = button
        
    
    # First Template
    @discord.ui.button(label=f"Template: {TarnishedTalk.templateList[0]}", style=discord.ButtonStyle.gray, row=0)
    async def selectTemplateFirst(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.updateButton(button)
        self.dropdown.update(TarnishedTalk.templateList,0,self.tarnished.templateFirst)
        await interaction.response.edit_message(embed=self.getEmbed(),view=self)
            
    # First Category
    @discord.ui.button(label=f"Category: {TarnishedTalk.categoryList[0]}", style=discord.ButtonStyle.blurple, row=0)
    async def selectCategoryFirst(self, interaction: discord.Interaction, button: discord.ui.Button): 
        self.updateButton(button)
        self.dropdown.update(TarnishedTalk.categoryList,1,self.tarnished.categoryFirst)
        await interaction.response.edit_message(embed=self.getEmbed(),view=self)
    
    # First Word
    @discord.ui.button(label=f"Word: {TarnishedTalk.wordsList[TarnishedTalk.categoryList[0]][0]}", style=discord.ButtonStyle.blurple, row=0)
    async def selectWordFirst(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.updateButton(button)
        self.dropdown.update(TarnishedTalk.wordsList[self.tarnished.categoryFirst],2,self.tarnished.wordFirst)
        await interaction.response.edit_message(embed=self.getEmbed(),view=self)
 
    # Conjunction    
    @discord.ui.button(label=f"Conjunction: {TarnishedTalk.conjunctionList[0]}", style=discord.ButtonStyle.blurple, row=1)
    async def selectConjunction(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.updateButton(button)
        self.dropdown.update(TarnishedTalk.conjunctionList,3,self.tarnished.conjunction)
        await interaction.response.edit_message(embed=self.getEmbed(),view=self)

    # Second Template
    @discord.ui.button(label=f"Template: {TarnishedTalk.templateList[0]}", style=discord.ButtonStyle.blurple, row=2)
    async def selectTemplateSecond(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.updateButton(button)
        self.dropdown.update(TarnishedTalk.templateList,4,self.tarnished.templateSecond, disabled= self.tarnished.conjunction == TarnishedTalk.conjunctionList[0])
        await interaction.response.edit_message(embed=self.getEmbed(),view=self)
            
    # Second Category
    @discord.ui.button(label=f"Category: {TarnishedTalk.categoryList[0]}", style=discord.ButtonStyle.blurple, row=2)
    async def selectCategorySecond(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.updateButton(button)
        self.dropdown.update(TarnishedTalk.categoryList,5,self.tarnished.categorySecond, disabled= self.tarnished.conjunction == TarnishedTalk.conjunctionList[0])
        await interaction.response.edit_message(embed=self.getEmbed(),view=self)
    
    # Second Word
    @discord.ui.button(label=f"Word: {TarnishedTalk.wordsList[TarnishedTalk.categoryList[0]][0]}", style=discord.ButtonStyle.blurple, row=2)
    async def selectWordSecond(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.updateButton(button)
        self.dropdown.update(TarnishedTalk.wordsList[self.tarnished.categorySecond],6,self.tarnished.wordSecond, disabled= self.tarnished.conjunction == TarnishedTalk.conjunctionList[0])
        await interaction.response.edit_message(embed=self.getEmbed(),view=self)

    @discord.ui.button(label="Send Message", style=discord.ButtonStyle.green, row=4)
    async def send_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"> {self.tarnished.getMessage()}\n \\- {self.username}")
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