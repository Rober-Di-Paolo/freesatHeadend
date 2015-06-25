"""
Freesat Channel Script
"""
import urllib
import urllib2
import json
import os

g_freesatSourceURL="http://services.platform.freesat.tv/g2/channel_list/chlist.php"

# Note the tvheadend config can be found in /home/hts/.hts/tvheadend just copy it locally and run this script.


# The broadcast names and the names on the freesat website don't always match-up
# So we fix the Freesat names to match the broadcast names
def fixupChannelName(name):

    # This list has mainly been worked out by trial and error and will likely change over time.
    # Might make sense to load this from a file.
    fixupList = [
        ("BBC 1", "BBC One"),
        ("BBC ONE", "BBC One"),
        ("BBC TWO", "BBC Two"),
        ("BBC THREE", "BBC Three"),
        ("BBC FOUR", "BBC Four"),
        ("Smash Hits", "Smash Hits!"),
        ("Pick FSAT", "Pick"),
        ("Community Channel", "Community"),
        ("more than movies", "more>movies"),
        ("Sony SAB", "SONY SAB"),
        ("ITV (Yorks W)", "ITV"),
        ("ITV +1 (Yorkshire)", "ITV +1"),
        ("ITV +1", "ITV+1"),
        ("ITV HD (North)", "ITV HD"),
        ("Channel 5 North", "Channel 5"),
        ("Channel 5 +1", "Channel 5+1"),
        ("5+24", "Channel 5+24"),
        ("euronews", "Euronews"),
        ("Cbeebies", "CBeebies"),
        ("Channel 4 North", "Channel 4"),
        ("Channel 4 North + 1", "Channel 4 +1"),
        ("FLAVA", "Flava"),
        ("Holiday+Cruise", "holiday+cruise"),
        ("More4 + 1", "More4 +1"),
        ("NHK WORLD HD", "NHK World HD"),
        ("Smooth RadioUK", "Smooth"),
        ("Pop", "POP"),
        ("S4C Digidol", "S4C"),
        ("KISS", "Kiss"),
        ("Kiss", "KISS"),
        ("RT HD", "RT"),
        ("BET+1", "BET +1"),
        ("Movies4Men", "movies4men"),
        ("Al Jazeera English", "Al Jazeera Eng"),
        ("Capital Xtra", "Capital XTRA"),
        ("CAPITAL TV", "Capital TV"),
        ("Rocks & Co1", "Rocks & Co 1"),
        ("TV Shop", "TV SHOP"),
        ("CLUBLAND  TV", "Clubland TV"),
        ("heart tv", "Heart TV"),
        ("PlanetRock", "Planet Rock")
    ]

    for src, dest in fixupList:
        name = name.replace(src, dest)

    return name

if __name__ == "__main__":
    options = {"type":"json",
               "device":"hd",
               "pcode":"LS6"}
			   
    iconCache = "W:\\Stuff\\Personal\\FreesatHeadEnd\\IconCache\\"
    tvheadendChannelsPath = "W:\\Stuff\\Personal\\FreesatHeadEnd\\sampleTVHeadendConfig\\channels\\"
    tvheadendTagsPath = "W:\\Stuff\\Personal\\FreesatHeadEnd\\sampleTVHeadendConfig\\channeltags\\"

    print "Reading Channel List from '{0}'...".format(g_freesatSourceURL)
	
    # Download the json
    data = urllib.urlencode(options)
    response = urllib2.urlopen(g_freesatSourceURL + "?" + data)
    page = response.read()

    # Parse it into simple groups and channels
    pageJson = json.loads(page)
    groups = set()
    channels = {}
    class channelObject(object): pass 
    for genre in pageJson["regions"]["genre"]:
        groups.add(genre["name"])
        for channel in genre["channels"]:
            if type(channel) is not dict:
                continue
            strChannelName = fixupChannelName(channel["channelname"])
            currChannel = channelObject()
            currChannel.num = channel["lcn"]
            currChannel.name = strChannelName
            currChannel.logo = channel["logourl"]
            currChannel.group = genre["name"]
			# can remove this, it just downloads the icons to a local cache which may or may not be useful
            #urllib.urlretrieve (channel["logourl"], iconCache + channel["logourl"].split('/')[-1])
            channels[strChannelName] = currChannel
            print currChannel.num + " - " + currChannel.name

    print "\nReading TVHeadend Tag List from '{0}'...".format(tvheadendTagsPath)

    # now we need to check and update the groups
    tvheadendGroups = {}
    groupFiles = os.listdir(tvheadendTagsPath)
    maxGroupId = 0
    for file in groupFiles:
        with open(tvheadendTagsPath + file) as groupFile:
            if int(file) > maxGroupId:
                maxGroupId = int(file)
            fileData = groupFile.read()            
            groupJson = json.loads(fileData)
            if groupJson["name"] in groups:
                groups.remove(groupJson["name"])
            tvheadendGroups[groupJson["name"]] = groupJson["id"]
   
    print "\nWritting new TVHeadend Tag List to '{0}'...".format(tvheadendTagsPath)
	
    for group in groups:
        maxGroupId = maxGroupId + 1        
        with open(tvheadendTagsPath + unicode(maxGroupId), "w") as groupFile:
            data={"comment":"", "name":group, "titledIcon":"", "enabled":1, "internal":0, "id":maxGroupId, "icon":"" }
            groupFile.write(json.dumps(data, indent=4))
            print "New Tag '{0}' Id={1}".format(group, maxGroupId)

			
    print "\nUpdating TVHeadend Channel List in '{0}'...".format(tvheadendTagsPath)
	
    # Finally we need to read in each channel and update the icon
    # and channel number if it's in our channels dictionary
    channelFiles = os.listdir(tvheadendChannelsPath)
    processed = 0
    skipped = 0
    for file in channelFiles:
        with open(tvheadendChannelsPath + file, "r+") as channelFile:
            fileData = channelFile.read()            
            channelJson = json.loads(fileData)
            currChannel = channels.get(channelJson["name"])
            
            # unknown channel
            if currChannel is None:
                print file + ": Unknown Channel \'" + channelJson["name"] + "\' skipping..."
                skipped = skipped + 1
                continue            
            
            #print file + ": Processing Channel \'" + channelJson["name"] + "\' Num=" + currChannel.num + " Logo=\'" + currChannel.logo + "\'"
            processed = processed + 1
            channelJson["channel_number"] = currChannel.num
            channelJson["icon"] = currChannel.logo
            
            groupId = tvheadendGroups.get(currChannel.group)
            if groupId not in channelJson["tags"]:
                channelJson["tags"].append(groupId)

            # nuke and re-write the file
            channelFile.truncate(0)
            channelFile.seek(0)
            channelFile.flush()
            channelFile.write(json.dumps(channelJson, indent=4))            
            
    print "\nProcessed=" + unicode(processed) + " Skipped=" + unicode(skipped) + " Total=" + unicode(skipped+processed)
            
                  
                  
            
    