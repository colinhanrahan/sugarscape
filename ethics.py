import agent
import random

class Bentham(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration, lookahead=None):
        super().__init__(agentID, birthday, cell, configuration)
        self.lookahead = lookahead

    def findEthicalValueOfCell(self, cell):
        cellSiteWealth = cell.sugar + cell.spice
        # Max combat loot for sugar and spice
        globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
        cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
        if cell.agent != None:
            cellSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
            cellMaxSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
        cellNeighborWealth = cell.findNeighborWealth()
        globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
        cellValue = 0
        selfishnessFactor = self.selfishnessFactor
        neighborhoodSize = len(self.neighborhood)
        futureNeighborhoodSize = len(self.findNeighborhood(cell))
        for neighbor in self.neighborhood:
            # Timesteps to reach cell, currently 1 since agents only plan for the current timestep
            timestepDistance = 1
            neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
            # If agent does not have metabolism, set duration to seemingly infinite
            cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
            certainty = 1 if neighbor.canReachCell(cell) == True else 0
            proximity = 1 / timestepDistance
            intensity = (1 / (1 + neighbor.findTimeToLive()) / (1 + cell.pollution))
            duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
            discount = 0.5
            futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
            futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
            # Assuming agent can only see in four cardinal directions
            extent = neighborhoodSize / (neighbor.vision * 4) if neighbor.vision > 0 else 1
            futureExtent = futureNeighborhoodSize / (neighbor.vision * 4) if neighbor.vision > 0 and self.lookahead != None else 1
            neighborValueOfCell = 0
            # If not the agent moving, consider these as opportunity costs
            if neighbor != self and cell != neighbor.cell and self.selfishnessFactor < 1:
                duration = -1 * duration
                intensity = -1 * intensity
                futureDuration = -1 * futureDuration
                futureIntensity = -1 * futureIntensity
                if self.lookahead == None:
                    neighborValueOfCell = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
                else:
                    neighborValueOfCell = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
            # If move will kill this neighbor, consider this a penalty
            elif neighbor != self and cell == neighbor.cell and self.selfishnessFactor < 1:
                if self.lookahead == None:
                    neighborValueOfCell = -1 * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
                else:
                    neighborValueOfCell = -1 * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
                # If penalty is too slight, make it more severe
                if neighborValueOfCell > -1:
                    neighborValueOfCell = -1
            else:
                if self.lookahead == None:
                    neighborValueOfCell = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
                else:
                    neighborValueOfCell = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
            if selfishnessFactor != -1:
                if neighbor == self:
                    neighborValueOfCell *= selfishnessFactor
                else:
                    neighborValueOfCell *= 1-selfishnessFactor
            cellValue += neighborValueOfCell
        return cellValue

    def spawnChild(self, childID, birthday, cell, configuration):
        return Bentham(childID, birthday, cell, configuration, self.lookahead)

class Economist(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration):
        super().__init__(agentID, birthday, cell, configuration)
        # format: {"cell": <some cell>, "value": <cell value>}
        self.bestCell, self.secondBestCell = None
        self.findBestCells()

    def findBestCells(self):
        self.findNeighborhood()
        random.shuffle(self.cellsInRange)

        retaliators = self.findRetaliatorsInVision()
        combatMaxLoot = self.cell.environment.maxCombatLoot
        aggression = self.findAggression()
        cellScores = []

        for currCell in self.cellsInRange:
            cell = currCell["cell"]

            if cell.isOccupied() == True and aggression == 0:
                continue
            prey = cell.agent
            # Avoid attacking agents ineligible to attack
            if prey != None and self.isNeighborValidPrey(prey) == False:
                continue
            preyTribe = prey.tribe if prey != None else "empty"
            preySugar = prey.sugar if prey != None else 0
            preySpice = prey.spice if prey != None else 0
            # Aggression factor may lead agent to see more reward than possible meaning combat itself is a reward
            welfarePreySugar = aggression * min(combatMaxLoot, preySugar)
            welfarePreySpice = aggression * min(combatMaxLoot, preySpice)

            # Modify value of cell relative to the metabolism needs of the agent
            welfare = self.findWelfare((cell.sugar + welfarePreySugar), (cell.spice + welfarePreySpice))
            cellWealth = welfare / (1 + cell.pollution)

            # Avoid attacking agents protected via retaliation
            if prey != None and retaliators[preyTribe] > self.wealth + cellWealth:
                continue

            cellValue = self.findEthicalValueOfCell(cell)
            cellRecord = (cell, cellValue)
            cellScores.append(cellRecord)

        # sort the cells based on their calculated values
        cellScores = sorted(cellScores, key = lambda x: x[1], reverse = True)
        self.bestCell = {"cell": cellScores[0][0], "value": cellScores[0][1]}
        self.secondBestCell = {"cell": cellScores[1][0], "value": cellScores[1][1]}

    def findEthicalValueOfCell(self, cell):
        # Step 1: find egoist value of cell
        cellSiteWealth = cell.sugar + cell.spice
        # Max combat loot for sugar and spice
        globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
        cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
        if cell.agent != None:
            cellSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
            cellMaxSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
        cellNeighborWealth = cell.findNeighborWealth()
        globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
        neighborhoodSize = len(self.neighborhood)
        futureNeighborhoodSize = len(self.findNeighborhood(cell))
        # Timesteps to reach cell, currently 1 since agents only plan for the current timestep
        timestepDistance = 1
        metabolism = self.sugarMetabolism + self.spiceMetabolism
        # If agent does not have metabolism, set duration to seemingly infinite
        cellDuration = cellSiteWealth / metabolism if metabolism > 0 else 0
        certainty = 1
        proximity = 1 / timestepDistance
        intensity = (1 / (1 + self.findTimeToLive()) / (1 + cell.pollution))
        duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
        discount = 0.5
        futureDuration = (cellSiteWealth - metabolism) / metabolism if metabolism > 0 else cellSiteWealth
        futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
        # Assuming agent can only see in four cardinal directions
        extent = neighborhoodSize / (self.vision * 4) if self.vision > 0 else 1
        futureExtent = futureNeighborhoodSize / (self.vision * 4) if self.vision > 0 and self.lookahead != None else 1
        
        cellValue = 0
        if self.lookahead == None:
            cellValue = (extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration)))
        else:
            cellValue = (certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration))))

        # Step 2: subtract opportunity costs
        suitorNeighbors = self.neighborhood & cell.suitorAgents
        for neighbor in suitorNeighbors:
            opportunityCost = neighbor.bestCell.wealth - neighbor.nextBestCell.wealth
            cellValue -= opportunityCost
        return cellValue

    def moveToBestCell(self):
        bestCell = self.bestCell # update this in updateCellScore(), just check best and second best
        oldCell = self.cell

        if "all" in self.debug or "agent" in self.debug:
            print("Agent {0} moving to ({1},{2})".format(self.ID, bestCell.x, bestCell.y))
        if self.findAggression() > 0:
            self.doCombat(bestCell)
        else:
            self.gotoCell(bestCell)
              
        self.findBestCells()
        oldCell.viewerAgents.remove(self)
        for viewer in oldCell.viewerAgents:
            viewer.updateCellScore(newCell)

        newCell = self.cell
        if newCell != oldCell: # If agent does not move, only update viewers once
            for viewer in newCell.viewerAgents:
                viewer.updateCellScores(newCell)
        newCell.viewerAgents.append(self)

    def updateCellScores(self, cell):
        # calculate wealth
        cellScore = self.findEthicalValueOfCell(cell)

        if cell == self.bestCell["cell"]:
            self.bestCell["value"] = cellScore
        elif cell == self.secondBestCell["cell"]:
            self.secondBestCell["value"] = cellScore

        cellScores = [(self.bestCell["cell"],       self.bestCell["value"]),
                      (self.secondBestCell["cell"], self.secondBestCell["value"])]
        if cell != self.bestCell["cell"] and cell != self.secondBestCell["cell"]:
            cellScores.append((cell, cellScore))
        
        # sort the cells based on their calculated values
        cellScores = sorted(cellScores, key = lambda x: x[1], reverse = True)
        self.bestCell = {"cell": cellScores[0][0], "value": cellScores[0][1]}
        self.secondBestCell = {"cell": cellScores[1][0], "value": cellScores[1][1]}