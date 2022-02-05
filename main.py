import demjson
import ssl
import re
import math
import csv
from urllib import request
from lxml import html
from functools import partial

def getHtmlFromRequest(url):
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  response = request.urlopen(url, context=ctx)
  return html.fromstring(response.read())

def getPlayersContent(allianceHtmlData):
  scriptTags = allianceHtmlData.xpath("//script[@type='text/javascript']")

  playersContent = scriptTags[7].text_content()

  playersContent = playersContent.strip()
  return playersContent.replace("\n", "")

def getPlayersAsVector (playersContent):
  playersMatch = re.search("var players=(\[.*?\])", playersContent)

  return demjson.decode(playersMatch.group(1))

def getPlayers (allianceLink):
  allicanceHtmlData = getHtmlFromRequest(allianceRequestUrl + allianceLink)
  playersContent = getPlayersContent(allicanceHtmlData)
  return getPlayersAsVector(playersContent)

def getPlayersHabitate(players):
  habitate = []

  for player in enemyPlayers:
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

  return habitate

def filterOnlyCastles(habitat):
  return len(habitat["points"]) <= 3

def filterCastlesInHotspot(habitat, hotspots):
  possibleHotspot = list(filter(lambda hotspot: math.sqrt(pow(hotspot["x"] - habitat["coordinate-x"], 2) + pow(hotspot["y"] - habitat["coordinate-y"], 2)) <= hotspot["r"], hotspots))
  return len(possibleHotspot) > 0

if __name__ == "__main__":
  enemyAllianceLink = "l+k://alliance?1155&260"
  allianceRequestUrl = "https://lordsandknights.enjoyed.today/tools/AllianceMembers/default.aspx?alliance="
  playersUrl = "https://lordsandknights.enjoyed.today/PlayerCastles/default.aspx?player="

  enemyPlayers = getPlayers(enemyAllianceLink)
  enemyHabitate = getPlayersHabitate(enemyPlayers)

  hotspots = [{"x": 16269, "y": 16419, "r": 10}, {"x": 16303, "y": 16442, "r": 5}]

  enemyCastles = list(filter(filterOnlyCastles, enemyHabitate))
  enemyCastlesOnlyInHotspot = list(filter(lambda habitat : filterCastlesInHotspot(habitat, hotspots), enemyHabitate))

  with open("enemyCoordinates.txt", "w+", encoding="utf8") as file:
    file.write(str(enemyCastlesOnlyInHotspot))

  ## todo's
  ### python main.py -enemyHotspots [{x: 16444, y: 16533, r: 5}, {x: 16410, y: 16522, r: 10}] -playersInput players.csv -faken 3
  ### mehrere Coordinaten und andere Radien eingeben und auswerten
  ### CSV erstellen, indem alle Spieler aufgelistet werden, die bei Krieg mitmachen
  ### Jeder Spieler bekommt schrittweise die Links verteilts. (änhlich zu Uno)
  ### Als Parameter einen Bereich definieren, wie viele Castels angegriffen werden dürfen.
  ### Gruppenunterteilung, an welchen Tagen die Spieler angreifen können. Die Burgen müssen auf unterschiedliche Zeiten gefaked werden.