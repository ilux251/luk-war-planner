import demjson
import ssl
import re
import math
from urllib import request
from lxml import html

def getHtmlFromRequest(url):
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  response = request.urlopen(url, context=ctx)
  return html.fromstring(response.read())

if __name__ == "__main__":
  allianceRequestUrl = "https://lordsandknights.enjoyed.today/tools/AllianceMembers/default.aspx?alliance=l+k://alliance?1155&260"
  playersUrl = "https://lordsandknights.enjoyed.today/PlayerCastles/default.aspx?player="

  allicanceHtmlData = getHtmlFromRequest(allianceRequestUrl)

  scriptTags = allicanceHtmlData.xpath("//script[@type='text/javascript']")

  playersContent = scriptTags[7].text_content()

  playersContent = playersContent.strip()
  playersContent = playersContent.replace("\n", "")

  playersMatch = re.search("var players=(\[.*?\])", playersContent)

  players = demjson.decode(playersMatch.group(1))

  habitate = []

  for player in players:
    playersHtmlData = getHtmlFromRequest(playersUrl + player["link"])

    playerHabitate = playersHtmlData.xpath("//table[@id='PlayerCastles']/tr")

    for playerHabitat in playerHabitate:
      coordinateLink = playerHabitat.xpath("./td/a")[0].text_content()
      coordinateMatch = re.search("(\d+),(\d+)", coordinateLink)
      pointsMatch = re.search("\d+", playerHabitat.xpath("./td/text()")[0])
      points = pointsMatch.group(0)

      habitate.append({"coordinateLink": coordinateLink,
                       "coordinate-x": int(coordinateMatch.group(1)),
                       "coordinate-y": int(coordinateMatch.group(2)),
                       "points": points})

  # {'coordinateLink': 'l+k://coordinates?16303,16442&260', 'coordinate-x': 16303, 'coordinate-y': 16442, 'points': '290'}
  # (x2-x1)^2+(y2-y1)^2 (Wurzel ziehen)

  castles = list(filter(lambda habitat : (len(habitat["points"]) <= 3 and
                                          math.sqrt(pow(16303 - habitat["coordinate-x"], 2) + pow(16442 - habitat["coordinate-y"], 2)) <= 5), habitate))

  with open("coordinates.txt", "w+", encoding="utf8") as file:
    file.write(str(castles))

  ## todo's
  ### CSV erstellen, indem alle Spieler aufgelistet werden, die bei Krieg mitmachen
  ### Jeder Spieler bekommt schrittweise die Links verteilts. (änhlich zu Uno)
  ### Als Parameter einen Bereich definieren, wie viele Castels angegriffen werden dürfen.
  ### Gruppenunterteilung, an welchen Tagen die Spieler angreifen können. Die Burgen müssen auf unterschiedliche Zeiten gefaked werden.