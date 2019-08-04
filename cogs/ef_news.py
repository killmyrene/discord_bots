import discord
import re
import textwrap
import os
from discord.ext import commands
from discord.errors import HTTPException
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
from .utils import checks, chat_formatting as cf
from .utils.dataIO import dataIO
from cogs.utils import checks
#pip installs
from bs4 import BeautifulSoup
from google.cloud import translate
from dotmap import DotMap

class EFNews:

    """ Post EF news to discord channel. """
    def __init__(self, bot : commands.Bot):

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="C:\\Users\Paolo\Desktop\DiscordDev\googleapi-31e7520fc607.json"
        self.bot = bot
        self.globalUrlHost = "http://ef-server12-13-2052877516.us-west-1.elb.amazonaws.com:8080/EF/"
        self.globalUrlPath = "getNewsMultiLang?domain=J&lang=EN"
        self.globalFullUrl = self.globalUrlHost + self.globalUrlPath

        self.krUrlHost = "http://14.63.200.181:8080/EF/"
        self.krUrlPath = "getNews?domain=A"
        self.krFullUrl = self.krUrlHost + self.krUrlPath

        self.settings_path = "data/ef_news/settings.json"
        self.settings = dataIO.load_json(self.settings_path)

        self.disableEmbedMake = False
        self.server_used = None

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def gbnews_p(self, ctx: commands.Context,
                       channel: discord.Channel=None):
        """ Get html body from global news site """
        
        server = ctx.message.server
        if channel is None:
            channel = ctx.message.channel
        
        if not self.speak_permissions(server, channel):
            await self.bot.reply(
                "I don't have permission to send messages in {0.mention}."
                .format(channel))
            return
        
        print("Fetching Global news")
        globalSoup = self.get_soup_content(self.globalFullUrl)
        hasSendEmbed = False
        self.server_used = server
        self.disableEmbedMake = False
        for link in self.filter_valid_efglobal_links(globalSoup.find_all('a')):
            newsPath = link.get('href')
            newsUrl = self.globalUrlHost + newsPath
            embedNews = self.make_global_news_embed(server, newsUrl)
            for embed in embedNews:
                hasSendEmbed = True
                self.printembedlogs(embed)
                try:
                    await self.bot.send_message(channel, embed=embed)
                except HTTPException as x:
                    await self.bot.say("Encountered error posting the news '" + embed.title + "'")
                    print(x)
                    break
            if self.disableEmbedMake:
                #Exit loop immediately since we don't want to post further embeds anymore
                break

        if not hasSendEmbed:
            await self.bot.say("No new news available.")


    def get_soup_content(self, url):
        soup = BeautifulSoup(urlopen(url), "html5lib")
        return soup
           
    def filter_valid_efglobal_links(self, links):
        return self.filter_valid_links(links, 10000)

    def filter_valid_links(self, links, minSeq):
        for link in links:
            parse = urlparse(link.get('href'))
            query = parse_qs(parse.query)
            if 'seq' in query:
                seq = query['seq'][0]
                if int(seq) > minSeq:
                    yield link

    def make_global_news_embed(self, server: discord.Server, news_url):
        print(news_url)
        news_soup = self.get_soup_content(news_url)
        news_body = news_soup.body

        info = self.extract_news_info(news_body)
#         if "Purchase Bonus" in info.title or self.disableEmbedMake:
#             #Ignore Monthly purchase bonus and any news after it for now
#             print("ignore news cause of the purchase bonus")
#             self.disableEmbedMake = True
#             return []

        embeds = self.make_embeds(server, info.title, news_url, info.thumbnail, info.date, info.text, info.sections)
        return embeds

    def extract_news_info(self, soupBody):
        title = soupBody.find(id="news-title").string
        date = soupBody.find(id="news-date").string
        thumbnail = soupBody.find(id="news-img").img.get('src')
        soupText = soupBody.find(id="news-text")

        #attemp to section texts by img srcs. 
        images = soupText.find_all("img")
        images.append(BeautifulSoup("<img src=\"dummy\"/>")) #add a hack so that the last partition is added
        sections = []
        prettyText = soupText.prettify()
        for img in images:
            splitText = prettyText.split(img.prettify())
            info = {
                "text": re.sub(r'\n\s*\n', '\n\n', BeautifulSoup(splitText[0], "html5lib").get_text()),
                "imageUrl": img.get("src")
            }
            if len(splitText) > 1:
                prettyText = splitText[1]
            sections.append(info)

        d = {
            "title" : title,
            "date" : date,
            "thumbnail" : thumbnail,
            "sections" : sections,
            "text": re.sub(r'\n\s*\n', '\n\n', soupText.get_text())
        }
        return DotMap(d)

    def make_embeds(self, server:discord.Server, title, url, thumbnail, name, value, sections):
        embeds = []

        if self.isembedcontentcached(server, value):
            print("Cannot make embed as its already cached beforehand")
            return embeds

        for section in sections:
            for splitstring in self.chunkstring(section.text, 1024):
                embed = self.make_default_embed(title, url, thumbnail)
                embed.add_field(name=name, value=splitstring, inline=False)
                embeds.append(embed)
            # add image on last of the embeds
            if section.imageUrl is not None:
                embeds[-1].set_image(url=section.imageUrl)

        self.saveembedcontent(server, value)
        return embeds

    def make_default_embed(self, title, url, thumbnail):
        embed = discord.Embed(title=title, color=0x5f69c5, url=url)
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text="Programmed by @killmyrene#4221", icon_url="https://cdn.discordapp.com/avatars/270627944014151681/69467a58556a81a580a747d79b6edb12.png?size=128")
        return embed

    def chunkstring(self, string, length):
        return (string[0+i:length+i] for i in range(0, len(string), length))

    def isembedcontentcached(self, server:discord.Server, content): 
        self.check_server_setting(server.id)   
        server_setting = self.settings[server.id]    
        if server_setting['use_cache'] and content in server_setting['embed_content']:
            return True
        return False

    def saveembedcontent(self, server:discord.Server, content):
        self.check_server_setting(server.id)    
        if not self.settings[server.id]['use_cache']:
            return
    
        self.settings[server.id]['embed_content'].append(content)
        dataIO.save_json(self.settings_path, self.settings)

    def printembedlogs(self, embed):
        print("Title: " + embed.title)
        print("Thumbnail: " + embed.thumbnail.url)
        if len(embed.fields) > 0:
            field = embed.fields[0]
            print("Date: " + field.name)
            print("Text count: {}".format(len(field.value)))


    @commands.command(pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def krnews_p(self, ctx: commands.Context,
                       channel: discord.Channel=None):
        
        server = ctx.message.server
        if channel is None:
            channel = ctx.message.channel
        
        if not self.speak_permissions(server, channel):
            await self.bot.reply(
                "I don't have permission to send messages in {0.mention}."
                .format(channel))
            return
        
        print("Fetching Korean news")
        krSoup = self.get_soup_content(self.krFullUrl)
        hasSendEmbed = False
        self.disableEmbedMake = False

        for link in self.filter_valid_efkorean_links(krSoup.find_all('a')):
            newsPath = link.get('href')
            newsUrl = self.krUrlHost + newsPath
            embedNews = self.make_korean_news_embed(server, newsUrl)
            for embed in embedNews:
                hasSendEmbed = True
                self.printembedlogs(embed)
                try:
                    await self.bot.send_message(channel, embed=embed)
                except HTTPException as x:
                    await self.bot.say("Encountered error posting the news '" + embed.title + "'")
                    print(x)
                    break
            if self.disableEmbedMake:
                #Exit loop immediately since we don't want to post further embeds anymore
                break

        if not hasSendEmbed:
            await self.bot.say("No new news available.")
            
    
    def filter_valid_efkorean_links(self, links):
        return self.filter_valid_links(links, 1500)

    def make_korean_news_embed(self, server: discord.Server, news_url):
        print(news_url)
        news_soup = self.get_soup_content(news_url)
        news_body = news_soup.body

        info = self.extract_news_info(news_body)
        #modify thumbnail to add KR url host, as the body doesn't return the full url
        info.thumbnail = self.krUrlHost[:-4] + info.thumbnail

        #Check cache to reduce Translate API usage
        if self.isembedcontentcached(server, info.text):
            print("Korean news already cached")
            return []
        #Save cache for further cache check
        self.saveembedcontent(server, info.text)
        
        #Start translating
        translatedTitle = self.translate(info.title)
        if "payment bonus" in translatedTitle or self.disableEmbedMake:
            #Ignore Monthly purchase bonus and any news after this for now
            self.disableEmbedMake = True
            return []

        translatedText =  self.translate(info.text)
        print (translatedText)

        #translate each text in the section infos
        sections = info.sections
        for section in sections:
            section.text = self.translate(section.text)

        embeds = self.make_embeds(server, translatedTitle, news_url, info.thumbnail, info.date, translatedText, sections)
        return embeds

    def translate(self, text):
        #Set environment to get the translate API working
        translate_client = translate.Client()

        #There's an issue with text containing newlines not being preserved after being translated
        #So workaround would be to replace newlines with <br/> and replace it back after translation
        replacedText = re.sub('\n', '<br/>', text)
        translation = translate_client.translate(replacedText, target_language='en')
        translatedText = translation['translatedText']
        return re.sub('<br/>', '\n', translatedText)

    @commands.command(pass_context=True)
    async def clearnews(self, ctx : commands.Context):
        server = ctx.message.server
        server_id = ctx.message.server.id
        self.check_server_setting(server_id)

        self.settings[server_id]['embed_content'] = []
        dataIO.save_json(self.settings_path, self.settings)
        await self.bot.say("Cached news have been cleared for Server {}".format(server))

    @commands.command(pass_context=True)
    async def togglecache(self, ctx : commands.Context):
        server = ctx.message.server
        server_id = ctx.message.server.id
        self.check_server_setting(server_id)

        toggle_cache = not self.settings[server_id]['use_cache']

        if toggle_cache:
            await self.bot.say("Caching is enabled")
        else:
            await self.bot.say("Caching is disabled")

        self.settings[server_id]['use_cache'] = toggle_cache
        dataIO.save_json(self.settings_path, self.settings)

    def check_server_setting(self, server_id):
        if server_id not in self.settings:
            #create default settings for the server
            self.settings[server_id] = {'embed_content' : [], 'use_cache' : True}
            dataIO.save_json(self.settings_path, self.settings)

    def speak_permissions(self, server: discord.Server,
                          channel: discord.Channel=None):
        return server.get_member(
            self.bot.user.id).permissions_in(channel).send_messages

def check_folders():
    if not os.path.exists("data/ef_news"):
        print("Creating data/ef_news directory...")
        os.makedirs("data/ef_news")

def check_files():
    f = "data/ef_news/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/ef_news/settings.json...")
        dataIO.save_json(f, {'dummy_server_id' : { 'embed_content' : [], 'use_cache' : True} })

def setup(bot: commands.Bot):
    check_folders()
    check_files()
    bot.add_cog(EFNews(bot))
