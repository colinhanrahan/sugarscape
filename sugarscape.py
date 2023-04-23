#! /usr/bin/python

import agent
import cell
import environment
import gui

import getopt
import json
import math
import random
import sys
#import time

class Sugarscape:
    def __init__(self, configOptions):
        self.__environment = environment.Environment(configOptions["environmentHeight"], configOptions["environmentWidth"], configOptions["environmentMaxSugar"], configOptions["environmentSugarRegrowRate"])
        self.__environmentHeight = configOptions["environmentHeight"]
        self.__environmentWidth = configOptions["environmentWidth"]
        self.configureEnvironment(configOptions["environmentMaxSugar"])
        self.__agents = []
        self.configureAgents(configOptions["initialAgents"], configOptions["agentMaxVision"], configOptions["agentMaxMetabolism"], configOptions["agentMaxInitialWealth"])
        self.__gui = gui.GUI(self)
        self.__run = False # Simulation start flag
        self.__end = False # Simulation end flag
        self.__timestep = 0
        self.__runtimeStats = {"timestep": 0, "agents": 0, "meanMetabolism": 0, "meanVision": 0, "meanWealth": 0, "meanAge": 0, "giniCoefficient": 0,
                               "meanTradePrice": 0, "meanTradeVolume": 0, "totalTradeVolume": 0, "totalWealth": 0, "maxWealth": 0, "minWealth": 0}
        self.__lastLoggedTimestep = 0
        self.__log = open(configOptions["logfile"], 'a') if configOptions["logfile"] != None else None

    # TODO: Make more consistent with book, dispersion more tightly concentrated than in book (ref: pg. 22)
    def addSugarPeak(self, startX, startY, radius, maxCapacity):
        height = self.__environment.getHeight()
        width = self.__environment.getWidth()
        radialDispersion = math.sqrt(max(startX, width - startX)**2 + max(startY, height - startY)**2) * (radius / width)
        for i in range(height):
            for j in range(width):
                if self.__environment.getCell(i, j) == None:
                    self.__environment.setCell(cell.Cell(i, j, self.__environment), i, j)
                euclideanDistanceToStart = math.sqrt((startX - i)**2 + (startY - j)**2)
                currDispersion = 1 + maxCapacity * (1 - euclideanDistanceToStart / radialDispersion)
                cellMaxCapacity = min(currDispersion, maxCapacity)
                cellMaxCapacity = math.ceil(cellMaxCapacity)
                if cellMaxCapacity > self.__environment.getCell(i, j).getMaxSugar():
                    self.__environment.getCell(i, j).setMaxSugar(cellMaxCapacity)
                    self.__environment.getCell(i, j).setCurrSugar(cellMaxCapacity)
 
    def configureAgents(self, initialAgents, maxMetabolism, maxVision, maxInitialWealth):
        if self.__environment == None:
            return
        totalCells = self.__environmentHeight * self.__environmentWidth
        if initialAgents > totalCells:
            print("Could not allocate {0} agents. Allocating maximum of {1}.".format(initialAgents, totalCells))
            initialAgents = totalCells
        agentEndowments = self.randomizeAgentEndowments(initialAgents, maxVision, maxMetabolism, maxInitialWealth)
        for i in range(initialAgents):
            randX = random.randrange(self.__environment.getHeight())
            randY = random.randrange(self.__environment.getWidth())
            while self.__environment.getCell(randX, randY).getAgent() != None:
                randX = random.randrange(self.__environment.getHeight())
                randY = random.randrange(self.__environment.getWidth())
            c = self.__environment.getCell(randX, randY)
            currMetabolism = agentEndowments[i][0]
            currVision = agentEndowments[i][1]
            currWealth = agentEndowments[i][2]
            a = agent.Agent(c, currMetabolism, currVision, currWealth)
            c.setAgent(a)
            self.__agents.append(a)

    def configureEnvironment(self, maxCapacity):
        height = self.__environment.getHeight()
        width = self.__environment.getWidth()
        startX1 = math.ceil(height * 0.7)
        startX2 = math.ceil(height * 0.3)
        startY1 = math.ceil(width * 0.3)
        startY2 = math.ceil(width * 0.7)
        radius = math.ceil(math.sqrt(2 * (height + width)))
        self.addSugarPeak(startX1, startY1, radius, maxCapacity)
        self.addSugarPeak(startX2, startY2, radius, maxCapacity)

    def doTimestep(self):
        if self.__end == True:
            self.endSimulation()
        self.updateRuntimeStats()
        self.writeToLog()
        self.__environment.doTimestep()
        for a in self.__agents:
            if a.isAlive() == False:
                self.__agents.remove(a)
        self.__gui.doTimestep()
        self.__timestep += 1
        #print("Timestep: {0}".format(self.__timestep))

    def endLog(self):
        if self.__log == None:
            return
        logString += '\t' + json.dumps(self.__runtimeStats) + "\n]"
        self.__log.write(logString)
        self.__log.flush()
        self.__log.close()

    def endSimulation(self):
        self.endLog()
        print(str(self))
        exit(0)

    def getAgents(self):
        return self.__agents

    def getEnd(self):
        return self.__end

    def getEnvironment(self):
        return self.__environment
 
    def getEnvironmentHeight(self):
        return self.__environmentHeight

    def getEnvironmentWidth(self):
        return self.__environmentWidth

    def getGUI(self):
        return self.__gui

    def getRun(self):
        return self.__run

    def getRuntimeStats(self):
        return self.__runtimeStats

    def getTimestep(self):
        return self.__timestep

    def pauseSimulation(self):
        while self.__run == False:
            if self.__end == True:
                self.endSimulation()
            self.__gui.getWindow().update()

    def randomizeAgentEndowments(self, initialAgents, maxMetabolism, maxVision, maxInitialWealth):
        endowments = []
        metabolisms = []
        visions = []
        initialWealths = []
        minMetabolism = min(1, maxMetabolism) # Accept 0 case
        minVision = min(1, maxVision) # Accept 0 case
        minWealth = min(1, maxInitialWealth) # Accept 0 case
        currMetabolism = 1
        currVision = 1
        currWealth = 1
        for i in range(initialAgents):
            metabolisms.append(currMetabolism)
            visions.append(currVision)
            initialWealths.append(currWealth)
            currMetabolism += 1
            currVision += 1
            currWealth += 1
            if currMetabolism > maxMetabolism:
                currMetabolism = minMetabolism
            if currVision > maxVision:
                currVision = minVision
            if currWealth > maxInitialWealth:
                currWealth = minWealth
        random.shuffle(metabolisms)
        random.shuffle(visions)
        random.shuffle(initialWealths)
        for i in range(initialAgents):
            endowments.append([metabolisms[i], visions[i], initialWealths[i]])
        return endowments

    def runSimulation(self, timesteps=5):
        self.startLog()
        self.pauseSimulation() # Simulation begins paused until start button in GUI pressed
        t = 0
        timesteps = timesteps - self.__timestep
        while t < timesteps and self.__end == False and len(self.__agents) != 0:
            self.doTimestep()
            t += 1
            if self.__run == False:
                self.pauseSimulation()

    def setAgents(self, agents):
        self.__agents = agents

    def setEnd(self):
        self.__end = not self.__end

    def setEnvironment(self, environment):
        self.__environment = environment

    def setEnvironmentHeight(self, environmentHeight):
        self.__environmentHeight = environmentHeight

    def setEnvironmentWidth(self, environmentWidth):
        self.__environmentWidth = environmentWidth

    def setGUI(self, gui):
        self.__gui = gui

    def setTimestep(self, timestep):
        self.__timestep = timestep
  
    def setRun(self):
        self.__run = not self.__run
  
    def setRuntimeStats(self, runtimeStats):
        self.__runtimeStats = runtimeStats

    def startLog(self):
        if self.__log == None:
            return
        self.__log.write("[\n")

    def updateRuntimeStats(self):
        #self.__runtimeStats = {"agents": 0, "meanMetabolism": 0, "meanVision": 0, "meanWealth": 0, "meanAge": 0, "giniCoefficient": 0, "meanTradePrice": 0, "meanTradeVolume": 0,
        #                       "totalTradeVolume": 0, "totalWealth": 0, "maxWealth": 0, "minWealth": 0}
        numAgents = len(self.__agents)
        meanMetabolism = 0
        meanVision = 0
        meanWealth = 0
        meanAge = 0
        meanTradePrice = 0
        meanTradeVolume = 0
        totalTradeVolume = 0
        totalWealth = 0
        maxWealth = 0
        minWealth = sys.maxsize
        for agent in self.__agents:
            agentWealth = agent.getSugar()
            meanMetabolism += agent.getMetabolism()
            meanVision += agent.getVision()
            meanWealth += agentWealth
            totalWealth += agentWealth
            if agentWealth < minWealth:
                minWealth = agentWealth
            if agentWealth > maxWealth:
                maxWealth = agentWealth
        meanMetabolism = meanMetabolism / numAgents
        meanVision = meanVision / numAgents
        meanWealth = meanWealth / numAgents
        self.__runtimeStats["timestep"] = self.__timestep
        self.__runtimeStats["agents"] = numAgents
        self.__runtimeStats["meanMetabolism"] = meanMetabolism
        self.__runtimeStats["meanVision"] = meanVision
        self.__runtimeStats["meanWealth"] = meanWealth
        self.__runtimeStats["minWealth"] = minWealth
        self.__runtimeStats["maxWealth"] = maxWealth

    def writeToLog(self):
        if self.__log == None:
            return
        self.__lastLoggedTimestep = self.__timestep
        logString = '\t' + json.dumps(self.__runtimeStats) + ",\n"
        self.__log.write(logString)

    def __str__(self):
        string = "{0}Timestep: {1}\nLiving Agents: {2}".format(str(self.__environment), self.__timestep, len(self.__agents))
        return string

def parseConfigFile(configFile, configOptions):
    file = open(configFile)
    options = json.loads(file.read())
    for opt in configOptions:
        if opt in options:
            configOptions[opt] = options[opt]
    return configOptions

def parseOptions(configOptions):
    commandLineArgs = sys.argv[1:]
    shortOptions = "ch:"
    longOptions = ["conf=", "help"]
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        printHelp()
    for currArg, currVal in args:
        # TODO: Passing short option -c requires instead passing --c to grab config file name
        if currArg in ("-c", "--conf"):
            if currVal == "":
                print("No config file provided.")
                printHelp()
            parseConfigFile(currVal, configOptions)
        elif currArg in ("-h", "--help"):
            printHelp()
    return configOptions

def printHelp():
    print("Usage:\n\tpython sugarscape.py --conf config.json\n\nOptions:\n\t-c,--conf\tUse specified config file for simulation settings.\n\t-h,--help\tDisplay this message.")
    exit(0)

if __name__ == "__main__":
    # Set default values for simulation configuration
    configOptions = {"agentMaxVision": 6, "agentMaxMetabolism": 4, "agentMaxInitialWealth": 5, "initialAgents": 250,
                     "environmentHeight": 50, "environmentWidth": 50, "environmentMaxSugar": 4, "environmentSugarRegrowRate": 1,
                     "logfile": None}
    configOptions = parseOptions(configOptions)

    S = Sugarscape(configOptions)
    print(str(S))
    S.runSimulation(10000)
    print(str(S))
    exit(0)