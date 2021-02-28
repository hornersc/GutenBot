import os
from dotenv import load_dotenv
from discord.ext import  commands
from gutenberg.acquire import load_etext
from gutenberg.cleanup import strip_headers
import urllib
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix="!")

bot.NOTES = []
bot.ETEXT_NUMBER = 0
bot.RESULTS_MAX = 10
bot.SEARCH_MIN = 3
bot.LINE_WIDTH = 5
bot.LAST_TEXT = ""
bot.LAST_SEARCH = ""

url = "https://www.gutenberg.org/dirs/GUTINDEX.ALL"
etext = urllib.request.urlopen(url)
etextTable = []
for line in etext:
    etextTable.append(line.decode('utf-8'))

@bot.command(name="begin", help="Shows the begining lines of a text")
async def begin(ctx, length):
    length = int(length)
    msg = ""
    if bot.ETEXT_NUMBER != 0:
        if length > 0 and length <= 50:
            text = strip_headers(load_etext(bot.ETEXT_NUMBER)).strip()
            text = text.splitlines()
            text = text[:length]
            for line in text:
                msg += line + "\n"
        else:
            msg = "Length must be between 0 and 30"
    else:
        msg = "Use !searchTitle or !setNum to choose a text"
    await ctx.channel.send(msg)

@bot.command(name="addNote", help="Adds a given selection from the last search to notes")
async def addNote(ctx, *args):
    if args and args[0].isdigit():
        addNum =  args[0]
        addNum = int(addNum)
        annotation = (" ".join(args[1:]))
        if bot.LAST_SEARCH and bot.ETEXT_NUMBER != 0 and addNum > 0 and addNum <= bot.RESULTS_MAX:
            bot.NOTES.append([bot.LAST_SEARCH, bot.ETEXT_NUMBER, bot.LINE_WIDTH, addNum, annotation])
            msg = ("Successfully added note.")
        else:
            msg = ("Do a !searchBody first")
    else:
        msg = ("Write in the form !addNote [# in results] [annotation].")
    await ctx.channel.send(msg)

@bot.command(name="deleteNote", help="Deletes the note of the number given")
async def deleteNote(ctx, num):
    num = int(num)
    num = num - 1
    if num >= 0 and num <= len(bot.NOTES):
        bot.NOTES.pop(num)
        msg = "Removed note " + str(num + 1) + "."
    else:
        msg = "Invalid number."
    await ctx.channel.send(msg)

@bot.command(name="showNotes", help="Shows previous collected notes")
async def showNotes(ctx):
    NOTES = bot.NOTES
    if NOTES:
        for num, note in enumerate(NOTES):
            SELECT_WORD = note[0]
            ETEXT_NUMBER = note[1]
            LINE_WIDTH = note[2]
            RESULTS_NUM = note[3]
            ANNOTATIONS = note[4]

            seperator = 20 * '-'
            text = strip_headers(load_etext(ETEXT_NUMBER)).strip()
            text = text.splitlines()
            wordsFound = 0
            msg = ""
            OFFSET = int(LINE_WIDTH / 2)

            for i, line in enumerate(text):
                SELECT_WORD = SELECT_WORD.lower()
                SELECT_WORD = SELECT_WORD.replace("'", "’")
                lowerLine = line.lower()
                if SELECT_WORD in lowerLine:
                    wordsFound += 1
                    if wordsFound == RESULTS_NUM:
                        msg += ("Number |" + str(num + 1) + "|" + "----eText no. |" + str(ETEXT_NUMBER) + "|\n")
                        start = lowerLine.find(SELECT_WORD)
                        end = start + len(SELECT_WORD)
                        text[i] = text[i][:start] + "[" + SELECT_WORD + "]" + text[i][end:]
                        for j in range(LINE_WIDTH):
                            toPrint = text[i+j-OFFSET]
                            if not toPrint.isspace():
                                msg += (toPrint + "\n")
                        msg += seperator + "\nAnnotations: " + ANNOTATIONS + "\n"
                        await ctx.channel.send(msg + seperator + "\n\n")
                        msg = ""
    else:
        await ctx.channel.send("There are no notes.")

@bot.command(name="text", help="Shows current text")
async def getText(ctx):
    if bot.ETEXT_NUMBER != 0:
        msg = ("Using text from search '" + bot.LAST_TEXT + "', Gutenberg book #" + str(bot.ETEXT_NUMBER))
    else:
        msg = "No text has been stored. Use !searchTitle or !setNum to do so."
    await ctx.channel.send(msg)

@bot.command(name="setNum", help="Directly sets text with Gutenberg #")
async def setNum(ctx, newNum):
    newNum = int(newNum)
    if newNum < 0 or newNum > 64630:
        msg = "Invalid Gutenberg eText #"
    else:
        msg = "Successfully set from " + str(bot.ETEXT_NUMBER) + " to " + str(newNum)
        bot.ETEXT_NUMBER = newNum
    await ctx.channel.send(msg)


@bot.command(name="setWidth", help="Changes how many lines are shown with !searchBody")
async def setWidth(ctx, newWidth):
    newWidth = int(newWidth)
    if newWidth < 1 or newWidth > 10:
        msg = "Invalid width."
    else:
        msg = "Successfully set from " + str(bot.LINE_WIDTH) + " to " + str(newWidth)
        bot.LINE_WIDTH = newWidth
    await ctx.channel.send(msg)

@bot.command(name="setResults", help="Changes how many results are shown with !searchBody")
async def setResults(ctx, newResult):
    newResult = int(newResult)
    if newResult < 1 or newResult > 20:
        msg = "Invalid number of results."
    else:
        msg = "Successfully set from " + str(bot.RESULTS_MAX) + " to " + str(newResult)
        bot.RESULTS_MAX = newResult
    await ctx.channel.send(msg)

@bot.command(name="searchTitle", help="Finds text title from projectgutenberg.org")
async def title_search(ctx, *args):
    SEARCH_TERM = (" ".join(args[:]))
    START_SCROLL = False
    EXIT_SCROLL = False
    if not SEARCH_TERM:
        await ctx.channel.send("Nothing entered. Try again.")
        EXIT_SCROLL = True
    SEARCH_TERM = SEARCH_TERM.lower()

    for i, line in enumerate(etextTable):
        readableLine = line.lower()
        if "title and author" in readableLine:
            START_SCROLL = True
        if "==" in readableLine:
            START_SCROLL = False

        if "audio:" not in readableLine and "~ ~" not in readableLine and not EXIT_SCROLL and START_SCROLL:
            if SEARCH_TERM in readableLine:
                if not etextTable[i-1].isspace():
                    startOffset = -10
                    for j in range(10):
                        if etextTable[i-j].isspace():
                            startOffset = -j+1
                            break
                else:
                    startOffset = 0
                if not etextTable[i+1].isspace():
                    endOffset = 10
                    for j in range(10):
                        if etextTable[i+j].isspace():
                            endOffset = j-1
                            break
                else:
                    endOffset = 0

                readableStartLine = etextTable[i+startOffset]
                searchLine = re.split(r'\s{2,}', readableStartLine)
                for j in range(1+endOffset-startOffset):
                    await ctx.channel.send(etextTable[i+startOffset+j])
                await ctx.channel.send("? (respond y for yes, q for quit, or anything else for no)")
                def check(m):
                    return m.author == ctx.author
                ans = await bot.wait_for("message", check=check)
                ans = ans.content
                if ans == 'y':
                    bot.ETEXT_NUMBER = (int) (searchLine[1])
                    EXIT_SCROLL = True
                    bot.LAST_TEXT = SEARCH_TERM
                    await ctx.channel.send("Using Gutenberg text #" + str(bot.ETEXT_NUMBER))
                elif ans == 'q':
                    EXIT_SCROLL = True
                    await ctx.channel.send("Exiting search.")
    if bot.ETEXT_NUMBER <= 0 and not EXIT_SCROLL:
        await ctx.channel.send("The text was not found.")




@bot.command(name="searchBody", help="Finds quotes in body from projectgutenberg.org")
async def title_search(ctx, *args):
    SELECT_WORD = (" ".join(args[:]))
    msg = ""
    OFFSET = int(bot.LINE_WIDTH / 2)
    EXIT_CONTENT_SEARCH = False

    if bot.ETEXT_NUMBER != 0:
        WORD_FOUND = False
        wordsFound = 0

        if not SELECT_WORD or len(SELECT_WORD) < bot.SEARCH_MIN:
            await ctx.channel.send("Too short. Try again.")
            EXIT_CONTENT_SEARCH = True

        if not EXIT_CONTENT_SEARCH:
            bot.LAST_SEARCH = SELECT_WORD
            seperator = 20 * '-'
            text = strip_headers(load_etext(bot.ETEXT_NUMBER)).strip()
            text = text.splitlines()

            for i, line in enumerate(text):
                SELECT_WORD = SELECT_WORD.lower()
                SELECT_WORD = SELECT_WORD.replace("'", "’")
                lowerLine = line.lower()
                if SELECT_WORD in lowerLine and wordsFound < bot.RESULTS_MAX:
                    WORD_FOUND = True
                    wordsFound += 1
                    msg += ("Number |" + str(wordsFound) + "|" + "----Line |" + str(i) + "|\n")
                    start = lowerLine.find(SELECT_WORD)
                    end = start + len(SELECT_WORD)
                    text[i] = text[i][:start] + "[" + SELECT_WORD + "]" + text[i][end:]
                    for j in range(bot.LINE_WIDTH):
                        toPrint = text[i+j-OFFSET]
                        if not toPrint.isspace():
                            msg += (toPrint + "\n")
                    await ctx.channel.send(msg + seperator + "\n\n")
                    msg = ""

            if not WORD_FOUND:
                await ctx.channel.send("The word was not found in the text.")

    else:
        await ctx.channel.send("Use !searchTitle or !setNum to find the text first.")

bot.run(TOKEN)