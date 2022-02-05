import demjson
import ssl
import re
import math
import csv
import random
import argparse
from urllib import request
from lxml import html

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

def getPlayersFromAlliance (allianceRequestUrl):
  allicanceHtmlData = getHtmlFromRequest(allianceRequestUrl)
  playersContent = getPlayersContent(allicanceHtmlData)
  return getPlayersAsVector(playersContent)

def getPlayersHabitate(players):
  habitate = []

  for player in players:
    playersHtmlData = getHtmlFromRequest(playersUrl + player["link"])

    playerHabitate = playersHtmlData.xpath("//table[@id='PlayerCastles']/tr")

    for playerHabitat in playerHabitate:
      coordinateLink = playerHabitat.xpath("./td/a")[0].text_content()
      coordinateMatch = re.search("(\d+),(\d+)", coordinateLink)
      pointsMatch = re.search("\d+", playerHabitat.xpath("./td/text()")[0])
      habitatName = playerHabitat.xpath("./td[2]/text()")[0]
      points = pointsMatch.group(0)

      habitate.append({"coordinateLink": coordinateLink,
                       "coordinate-x": int(coordinateMatch.group(1)),
                       "coordinate-y": int(coordinateMatch.group(2)),
                       "points": points,
                       "habitatName": habitatName})

  return habitate

def filterOnlyCastles(habitat):
  return len(habitat["points"]) <= 3

def filterCastlesInHotspot(habitat, hotspots):
  possibleHotspot = list(filter(lambda hotspot: math.sqrt(pow(hotspot["x"] - habitat["coordinate-x"], 2) + pow(hotspot["y"] - habitat["coordinate-y"], 2)) <= hotspot["r"], hotspots))
  return len(possibleHotspot) > 0

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--enemyAllianceIds', type=str, help='Ids der gegnerischen Alliancen')
  parser.add_argument('--hotspots', type=str, help='Bereich für scharfe Ziele definieren.', required=True)
  parser.add_argument('--fakes', type=int, help='Wie viele fakes bekommt jeder Spieler?', required=True)
  parser.add_argument('--offEinheiten', type=int, help='Wie viele Einheiten pro scharfes Ziel benötigt wird.', required=True)
  parser.add_argument('--datum', type=str, help='Am welchen Tag erfolgt der Einschlag?', required=True)
  parser.add_argument('--zeiten', type=str, help='An welchen Zeiten kann angegriffen werden?', default='["7:00", "7:10", "7:20", "7:30", "7:40", "7:50", "8:00", "8:10", "8:20", "8:30", "8:40", "8:50"]')

  args = parser.parse_args()

  aufteilung = {}
  enemyPlayers = []

  enemyAllianceIds = demjson.decode(args.enemyAllianceIds)
  hotspots = demjson.decode(args.hotspots)
  fakes = args.fakes
  offEinheiten = args.offEinheiten
  datum = args.datum
  zeiten = demjson.decode(args.zeiten)

  allianceRequestUrl = "https://lordsandknights.enjoyed.today/tools/AllianceMembers/default.aspx?alliance=l+k://alliance?{}&260"
  playersUrl = "https://lordsandknights.enjoyed.today/PlayerCastles/default.aspx?player="

  for allianceId in enemyAllianceIds:
    allianceUrl = allianceRequestUrl.format(allianceId)
    enemyPlayers.extend(getPlayersFromAlliance(allianceUrl))

  enemyHabitate = getPlayersHabitate(enemyPlayers)
  random.shuffle(enemyHabitate)

  enemyCastles = list(filter(filterOnlyCastles, enemyHabitate))
  enemyCastlesOnlyInHotspot = list(filter(lambda habitat : filterCastlesInHotspot(habitat, hotspots), enemyCastles))

  with open("enemyCoordinates.txt", "w+", encoding="utf8") as file:
    file.write(str(enemyCastlesOnlyInHotspot))

  with open("players.csv", newline='', encoding="utf8") as csvFile:
    enemyCastlesCopy1 = enemyCastles.copy()
    enemyCastlesCopy2 = enemyCastles.copy()
    enemyCastlesOnlyInHotspotCopy = enemyCastlesOnlyInHotspot.copy()
    playersFromCSV = csv.DictReader(csvFile, delimiter=";")
    
    playersCopy = []

    for player in playersFromCSV:
      countCastles = math.floor(int(player["offEinheiten"]) / offEinheiten)
      if (countCastles >= int(player["castles"])):
        countCastles = int(player["castles"])

      player.update({"castles": countCastles, "hotTargets": []})

      playersCopy.append(player)

    
    for playerIndex in range(0, len(playersCopy), 2):
      aufteilung[playersCopy[playerIndex]["name"]] = {**playersCopy[playerIndex], "fakes": [enemyCastlesCopy1.pop() for x in range(fakes)]}
      aufteilung[playersCopy[playerIndex + 1]["name"]] = {**playersCopy[playerIndex + 1], "fakes": [enemyCastlesCopy2.pop() for x in range(fakes)]}
      
    for player in aufteilung:
      for i in range(aufteilung[player]["castles"]):
        aufteilung[player]["hotTargets"].append(enemyCastlesOnlyInHotspotCopy.pop())

  with open("war-plan.txt", "w+", encoding="utf8") as file:
    for player in aufteilung:
      random.shuffle(zeiten)

      file.write("Guten Tag " + aufteilung[player]["name"] + ", \n\nder Einschlag erfolgt am " + datum + ", um " + zeiten[0] + ".\n\n")

      file.write("fake Ziele:\n")
      for fake in aufteilung[player]["fakes"]:
        file.write(fake["habitatName"] + "\n")
        file.write(fake["coordinateLink"] + "\n")

      file.write("\n")

      if len(aufteilung[player]["hotTargets"]) > 0:
        file.write("scharfe Ziele:\n")

      for target in aufteilung[player]["hotTargets"]:
        file.write(target["habitatName"] + "\n")
        file.write(target["coordinateLink"] + "\n")

      file.write("\n")

      file.write("Berichte werden nicht gelöscht! \nIm Forum nach dem Bericht-Protokoll erkundigen.\n\n")

      if len(aufteilung[player]["hotTargets"]) == 0:
        file.write("Nicht genug Einheiten für scharfe Ziele.\nBenötigte Einheiten pro Burg: " + str(offEinheiten) + "\n")

      file.write("----------------------------------------------\n")


      