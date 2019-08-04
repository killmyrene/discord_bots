
import math
import re
import datetime
import time
import pydash
from pydash import collection as co, objects as obj
import numpy

# Let's assume that it's impossible to achieve an SR rate above 100%
# (usually it's below 10%, so this should be fairly conservative)
def validate_percentage(p):
	return !!p && p > 0 && p < 100

def parseGoldString(gold):
	if math.isfinite(gold):
		try:
        	return int(gold)
    	except ValueError:
        	return float(gold)

    # make sure the string follows the template of {number}{letters}
    efGoldFormatRegExp = '(^\d+\.?\d*)(\D?)'
    matches = re.match(efGoldFormatRegExp, gold)
    if matches is None:
    	return None

    matchResult = matches.groups()
    numPart = matchResult[0]
    multiplierPart = matchResult[1].lower()
    multiplier = 1

    if multiplierPart:
    	multiplierCharCode = ord(multiplierPart[0])
    	aCharCode = ord('a'[0])
    	multiplier = 10 ** (multiplierCharCode - (aCharCode - 1) * 3)

    try:
    	return int(numPart) * multiplier
    except ValueError:
        return float(numPart) * multiplier

def formatGoldString(gold):
	if not math.isfinite(gold):
		return "Could not parse number: " + str(gold)

	tempGold = gold
	multiplier = 0

	while (tempGold >= 1000):
		tempGold = math.floor(tempGold) / 1000
		multiplier += 1

	multiplierCharCode = ord('a'[0]) - 1 + multiplier
	multiplierChar = multiplier ? chr(multiplierCharCode) : ''

	return str(tempGold) + multiplierChar

def getHoursSince(date):
    return int(datetime.timedelta(days=date.days, hours=date.hours).total_seconds() // 3600)

def generateProgressChangeSummary(currentKL, currentTotalMedals, latestProgress)
	#latestProgress is either a class or a dictionary
	currentTotalMedalsNumber = parseGoldString(currentTotalMedals)
    previousTotalMedalsNumber = parseGoldString(latestProgress.totalMedals)
    medalsGained = currentTotalMedalsNumber - previousTotalMedalsNumber
    medalsGainedPercentage = (medalsGained / previousTotalMedalsNumber) * 100
    klGained = currentKL - latestProgress.kl
    hoursDiff = getHoursSince(latestProgress.timestamp)
    return "Welcome back! You've gained {klGained} KL and {medalGainedPercent:0.02f}% total medals over the last {hourDiff:0.02f} hour(s).".format(klGained=klGained, medalGainedPercent=str(medalGainedPercentage), hoursDiff=str(hoursDiff))


def klAssessmentMapping(klAssessment, groupKL):
  return {
    name: "KL{} ({} record{})".format(groupKL, klAssessment.n, klAssessment.n > 1 ? "s" : ""),
    value: "{}%-{}%".format(klAssessment.percentageMin, klAssessment.percentageMax),
    inline: true
  }

def generateSrMessage(msg, timestamp, percentage, medalsGained, percentageWithDoubled, description, assessment):
	srFields = [
	{
		name: "Spirt Rest",
		value: "{percentage:0.02f}% {medalGained}".format(percentage=str(percentage), medalGained=formatGoldString(medalsGained)),
		inline= true
	},
	{
		name: "Spirt Rest Doubled",
		value: "{percentage:0.02f}% {medalGained}".format(percentage=str(percentageWithDoubled), medalGained=formatGoldString(medalsGained*2)),
		inline: true
	}
	]

	gradeField = [
	{
		name: "SR Guide",
		value: assessment && assessment.score is not None ? "{}/100".format(assessment.score) : "Sorry, but your grade could not be calculated based on lack of data"
	}
	]

  mapValues = obj.map_values(assessment.kls, klAssessmentMapping)
  gradeKLFields = obj.values(mapValues)

  return {
    embed: {
      description,
      author: {
        name: msg.member.displayName,
        icon_url: msg.author.avatar ? "https://cdn.discordapp.com/avatars/${id}/${avatar}.png".format(id=msg.author.id, avatar=msg.author.avatar: None,
      },
      footer: {
        icon_url: 'https://cdn.discordapp.com/avatars/294466905073516554/07714791affb9af210756ce2565e6488.png',
        text: 'NephBot created by @stephenmesa#1219',
      },
      title: 'Spirit Rest Calculator',
      color: 13720519,
      timestamp: timestamp.toISOString(),
      fields: srFields + gradeField + gradeKLFields,
    },
  }

def filterOutlierProgresses(records):
	return list(filter(lambda record:validatePercentage(record.percentage), records))

def assessProgress(currentPercentage, comparableProgresses):
	normalizedProgresses = filterOutlierProgresses(comparableProgresses)
	allPercentages = list(map(lambda p: p.percentage, normalizedProgresses))
	klProgresses = co.group_by(normalizedProgresses, "kl")
  	def mapProgressValues(progresses):
	  	percentages = list(map(lambda e: e.percentage, progresses))
	  	percentageMin = min(percentages)
	  	percentageMax = max(percentages)
	  	return {
	  		n: progresses.length,
	  		percentageMin: float("{:.2f}".format(percentageMin)),
	  		percentageMax: float("{:.2f}".format(percentageMax))
	  	}
	kls = obj.map_values(klProgresses, mapProgressValues)
	score = normalizedProgresses.length > 0 ? numpy.percentile(allPercentages, currentPercentage) : None
  
	return {
	    kls,
	    score,
	}



def generateSrGradeMessage(message, timestamp, assessment, kl, percentage):

  mapValues = obj.map_values(assessment.kls, klAssessmentMapping)
  gradeKLFields = obj.values(mapValues)
  description = assessment.score ? "Your SR grade is **{}/100**".format(assessment.score) : "Sorry, but your grade could not be calculated based on lack of data"

  return {
    embed: {
      description,
      author: {
        name: "{displayName} (KL{kl} {percentage:.2f})".format(displayName=message.member.displayName, kl=kl, percentage=percentage),
        icon_url: message.author.avatar ? "https://cdn.discordapp.com/avatars/${id}/${avatar}.png".format(id=message.author.id, avatar=message.author.avatar) : None,
      },
      footer: {
        icon_url: 'https://cdn.discordapp.com/avatars/294466905073516554/07714791affb9af210756ce2565e6488.png',
        text: 'NephBot created by @stephenmesa#1219',
      },
      title: 'SR Grade',
      color: 13720519,
      timestamp: timestamp.toISOString(),
      fields: klFields,
    },
  }