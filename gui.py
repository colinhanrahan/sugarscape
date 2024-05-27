import math
import tkinter

class GUI:
    def __init__(self, sugarscape, screenHeight=1000, screenWidth=900):
        self.sugarscape = sugarscape
        self.screenHeight = screenHeight
        self.screenWidth = screenWidth
        self.window = None
        self.canvas = None
        self.grid = [[None for j in range(self.sugarscape.environmentWidth)]for i in range(self.sugarscape.environmentHeight)]
        # TODO: Add a simplified way to have a bunch of colors programatically chosen during runtime
        self.colors = {"sugar": "#F2FA00", "spice": "#9B4722", "sugarAndSpice": "#CFB20E", "noSex": "#FA3232", "female": "#FA32FA", "male": "#3232FA", "pollution": "#803280",
                       "green": "#32FA32", "blue": "#3232FA", "red": "#FA3232", "pink": "#FA32FA", "yellow": "#FAFA32", "teal": "#32FAFA", "purple": "#6432FA", "orange": "#FA6432",
                       "salmon": "#FA6464", "mint": "#64FA64", "blue2": "#3264FA",
                       "none": "#32FA32", "benthamHalfLookaheadBinary": "#3232FA", "egoisticHalfLookaheadBinary": "#FA3232", "altruisticHalfLookaheadBinary": "#FA32FA",
                       "benthamNoLookaheadBinary": "#FAFA32", "egoisticNoLookaheadBinary": "#32FAFA", "altruisticNoLookaheadBinary": "#6432FA", "benthamHalfLookaheadTop": "#FA6432",
                       "egoisticHalfLookaheadTop": "#FA6464", "altruisticHalfLookaheadTop": "#64FA64", "benthamNoLookaheadTop": "#3264FA"}
        self.widgets = {}
        self.infoColumnWidth = 150
        self.paddingColumnWidth = 20
        self.lastSelectedAgentColor = None
        self.lastSelectedEnvironmentColor = None
        self.highlightedCell = None
        self.highlightedAgent = None
        self.highlightRectangle = None
        self.activeColorOptions = {"agent": None, "environment": None}
        self.siteHeight = self.screenHeight / self.sugarscape.environmentHeight
        self.siteWidth = self.screenWidth / self.sugarscape.environmentWidth
        self.configureWindow()
        self.stopSimulation = False

    def clearHighlight(self):
        self.highlightedAgent = None
        self.highlightedCell = None
        if self.highlightRectangle != None:
            self.canvas.delete(self.highlightRectangle)
            self.highlightRectangle = None
        self.updateHighlightedCellStats()

    def configureAgentColorNames(self):
        return ["Disease", "Sex", "Tribes", "Decision Models"]

    def configureButtons(self, window):
        playButton = tkinter.Button(window, text="Play Simulation", command=self.doPlayButton)
        playButton.grid(row=0, column=2, sticky="sew")
        stepButton = tkinter.Button(window, text="Step Forward", command=self.doStepForwardButton, relief=tkinter.RAISED)
        stepButton.grid(row=1, column=2, sticky="nsew")

        agentColorButton = tkinter.Menubutton(window, text="Agent Coloring", relief=tkinter.RAISED)
        agentColorMenu = tkinter.Menu(agentColorButton, tearoff=0)
        agentColorButton.configure(menu=agentColorMenu)
        agentColorNames = self.configureAgentColorNames()
        agentColorNames.sort()
        agentColorNames.insert(0, "Default")
        self.lastSelectedAgentColor = tkinter.StringVar(window)
        self.lastSelectedAgentColor.set(agentColorNames[0])  # Default
        for name in agentColorNames:
            agentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.lastSelectedAgentColor, command=self.doAgentColorMenu, indicatoron=True)
        agentColorButton.grid(row=2, column=2, sticky="nsew")

        environmentColorButton = tkinter.Menubutton(window, text="Environment Coloring", relief=tkinter.RAISED)
        environmentColorMenu = tkinter.Menu(environmentColorButton, tearoff=0)
        environmentColorButton.configure(menu=environmentColorMenu)
        environmentColorNames = self.configureEnvironmentColorNames()
        environmentColorNames.sort()
        environmentColorNames.insert(0, "Default")
        self.lastSelectedEnvironmentColor = tkinter.StringVar(window)
        self.lastSelectedEnvironmentColor.set(environmentColorNames[0])  # Default
        for name in environmentColorNames:
            environmentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.lastSelectedEnvironmentColor, command=self.doEnvironmentColorMenu, indicatoron=True)
        environmentColorButton.grid(row=3, column=2, sticky="nsew")

        statsLabel = tkinter.Label(window, text="Timestep: - \nPopulation: - \nMetabolism: - \nMovement: - \nVision: - \nGini: - \nTrade Price: - \nTrade Volume: - ", font="Roboto 10", justify=tkinter.LEFT, anchor="nw")
        statsLabel.grid(row=4, column=2, sticky="nsew")
        cellLabel = tkinter.Label(window, text="Cell: - \nSugar: - \nSpice: - \nPollution: - \nSeason: - \n\nAgent: - \nAge: - \nVision: - \nMovement: - \nSugar: - \nSpice: - \nMetabolism: - ", font="Roboto 10", justify=tkinter.LEFT, anchor="nw")
        cellLabel.grid(row=5, column=2, sticky="nsew")

        self.widgets["playButton"] = playButton
        self.widgets["stepButton"] = stepButton
        self.widgets["agentColorButton"] = agentColorButton
        self.widgets["environmentColorButton"] = environmentColorButton
        self.widgets["agentColorMenu"] = agentColorMenu
        self.widgets["environmentColorMenu"] = environmentColorMenu
        self.widgets["statsLabel"] = statsLabel
        self.widgets["cellLabel"] = cellLabel

    def configureCanvas(self):
        canvasSize = min(self.screenWidth - self.infoColumnWidth - 2 * self.paddingColumnWidth, self.screenHeight)
        canvas = tkinter.Canvas(self.window, width=canvasSize, height=canvasSize)
        canvas.grid(row=0, column=0, rowspan=6, sticky="e")
        canvas.bind("<Button-1>", self.doClick)
        self.canvas = canvas

    def configureEnvironment(self):
        for i in range(self.sugarscape.environmentHeight):
            for j in range(self.sugarscape.environmentWidth):
                cell = self.sugarscape.environment.findCell(i, j)
                fillColor = self.lookupFillColor(cell)
                x1 = i * self.siteWidth # Upper right x coordinate
                y1 = j * self.siteHeight # Upper right y coordinate
                x2 = (i + 1) * self.siteWidth # Lower left x coordinate
                y2 = (j + 1) * self.siteHeight # Lower left y coordinate
                self.grid[i][j] = {"rectangle": self.canvas.create_rectangle(x1, y1, x2, y2, fill=fillColor, outline="", activestipple="gray50"), "color": fillColor}
        if self.highlightedCell != None:
            self.highlightCell(self.highlightedCell.x, self.highlightedCell.y)

    def configureEnvironmentColorNames(self):
        return ["Pollution"]

    def configureWindow(self):
        window = tkinter.Tk()
        self.window = window
        window.title("Sugarscape")
        # Do window sizing only after initial window object is created to get user's monitor dimensions
        if self.screenWidth < 0:
            self.screenWidth = math.ceil(window.winfo_screenwidth() * 0.75)
        if self.screenHeight < 0:
            self.screenHeight = math.ceil(window.winfo_screenheight() * 0.75)
        self.updateSiteDimensions()
        window.geometry(f"{self.screenWidth}x{self.screenHeight}")
        window.resizable(True, True)
        window.option_add("*font", "Roboto 10")
        self.configureButtons(window)
        self.configureCanvas()
        window.update()

        self.window.protocol("WM_DELETE_WINDOW", self.doWindowClose)
        self.window.bind("<Escape>", self.doWindowClose)
        self.window.bind("<space>", self.doPlayButton)
        self.window.bind("<Right>", self.doStepForwardButton)
        self.window.bind("<Configure>", self.resizeInterface)
        self.canvas.bind("<Button-1>", self.doClick)

        # Adjust for slight deviations from initially configured window size
        self.resizeInterface()
        window.update()

    def destroyCanvas(self):
        self.canvas.destroy()

    def doAgentColorMenu(self, *args):
        self.activeColorOptions["agent"] = self.lastSelectedAgentColor.get()
        self.doTimestep()

    def doClick(self, event):
        eventX = event.x
        eventY = event.y
        gridX = math.floor(eventX / self.siteWidth)
        gridY = math.floor(eventY / self.siteHeight)
        # Handle clicking just outside edge cells
        if gridX < 0:
            gridX = 0
        elif gridX > self.sugarscape.environmentWidth - 1:
            gridX = self.sugarscape.environmentWidth - 1
        if gridY < 0:
            gridY = 0
        elif gridY > self.sugarscape.environmentHeight - 1:
            gridY = self.sugarscape.environmentHeight - 1

        cell = self.sugarscape.environment.findCell(gridX, gridY)
        if cell == self.highlightedCell:
            self.clearHighlight()
        else:
            self.highlightedCell = cell
            self.highlightedAgent = cell.agent
            self.highlightCell(gridX, gridY)

        self.doTimestep()

    def doEnvironmentColorMenu(self):
        self.activeColorOptions["environment"] = self.lastSelectedEnvironmentColor.get()
        self.doTimestep()

    def doPlayButton(self, *args):
        self.sugarscape.toggleRun()
        self.widgets["playButton"].config(text="  Play Simulation  " if self.sugarscape.run == False else "Pause Simulation")
        self.doTimestep()

    def doStepForwardButton(self, *args):
        if self.sugarscape.end == True:
            self.sugarscape.endSimulation()
        elif len(self.sugarscape.agents) == 0:
            self.sugarscape.toggleEnd()
        else:
            self.sugarscape.doTimestep()
            self.doTimestep()

    def doTimestep(self):
        if self.stopSimulation == True:
            self.sugarscape.toggleEnd()
            return
        if self.screenHeight != self.window.winfo_height() or self.screenWidth != self.window.winfo_width():
            self.resizeInterface()
        for i in range(self.sugarscape.environmentHeight):
            for j in range(self.sugarscape.environmentWidth):
                cell = self.sugarscape.environment.findCell(i, j)
                fillColor = self.lookupFillColor(cell)
                if self.grid[i][j]["color"] != fillColor:
                    self.canvas.itemconfig(self.grid[i][j]["rectangle"], fill=fillColor, outline="")
                    self.grid[i][j] = {"rectangle": self.grid[i][j]["rectangle"], "color": fillColor}

        if self.highlightedAgent != None:
            if self.highlightedAgent.isAlive() == True:
                self.highlightedCell = self.highlightedAgent.cell
                self.highlightCell(self.highlightedCell.x, self.highlightedCell.y)
            else:
                self.clearHighlight()

        self.updateLabels()
        self.window.update()

    def doWindowClose(self, *args):
        # Indicate to per-timestep rendering to stop rendering
        self.stopSimulation = True
        self.window.destroy()
        self.sugarscape.toggleEnd()

    def updateHighlightedCellStats(self):
        cell = self.highlightedCell
        if cell != None:
            cellSeason = cell.season if cell.season != None else '-'
            cellStats = f"Cell: ({cell.x},{cell.y}) \nSugar: {cell.sugar}/{cell.maxSugar} \nSpice: {cell.spice}/{cell.maxSpice} \nPollution: {round(cell.pollution, 2)} \nSeason: {cellSeason} \n"
            agent = cell.agent
            if agent != None:
                agentStats = (f"Agent: {str(agent)} \nAge: {agent.age} \nVision: {round(agent.vision, 2)} \nMovement: {round(agent.movement, 2)} \n"
                            + f"Sugar: {round(agent.sugar, 2)} \nSpice: {round(agent.spice, 2)} \nMetabolism: {round(((agent.sugarMetabolism + agent.spiceMetabolism) / 2), 2)}")
            else:
                agentStats = "Agent: - \nAge: - \nVision: - \nMovement: - \nSugar: - \nSpice: - \nMetabolism: -"
            cellStats += f"\n{agentStats}"
        else:
            cellStats = "Cell: - \nSugar: - \nSpice: - \nPollution: - \nSeason: - \n\nAgent: - \nAge: - \nVision: - \nMovement: - \nSugar: - \nSpice: - \nMetabolism: - "
        
        label = self.widgets["cellLabel"]
        label.config(text=cellStats)

    def hexToInt(self, hexval):
        intvals = []
        hexval = hexval.lstrip('#')
        for i in range(0, len(hexval), 2):
            subval = hexval[i:i + 2]
            intvals.append(int(subval, 16))
        return intvals
    
    def highlightCell(self, x, y):
        x1 = x * self.siteWidth
        y1 = y * self.siteHeight
        x2 = (x + 1) * self.siteWidth
        y2 = (y + 1) * self.siteHeight

        if self.highlightRectangle != None:
            self.canvas.delete(self.highlightRectangle)

        self.highlightRectangle = self.canvas.create_rectangle(x1, y1, x2, y2, fill="", activefill="#88cafc", outline="black", width=5)

    def intToHex(self, intvals):
        hexval = "#"
        for i in intvals:
            subhex = "%0.2X" % i
            hexval = hexval + subhex
        return hexval

    def lookupFillColor(self, cell):
        agent = cell.agent
        if agent == None:
            if self.activeColorOptions["environment"] == "Pollution":
                return self.recolorByResourceAmount(cell, self.colors["pollution"])
            else:
                if cell.sugar > 0 and cell.spice == 0:
                    return self.recolorByResourceAmount(cell, self.colors["sugar"])
                elif cell.spice > 0 and cell.sugar == 0:
                    return self.recolorByResourceAmount(cell, self.colors["spice"])
                else:
                    return self.recolorByResourceAmount(cell, self.colors["sugarAndSpice"])
        elif agent.sex != None and self.activeColorOptions["agent"] == "Sex":
            return self.colors[agent.sex]
        elif agent.tribe != None and self.activeColorOptions["agent"] == "Tribes":
            return self.colors[agent.tribe]
        elif agent.decisionModel != None and self.activeColorOptions["agent"] == "Decision Models":
            return self.colors[agent.decisionModel]
        elif len(agent.diseases) > 0 and self.activeColorOptions["agent"] == "Disease":
            return self.colors["red"]
        elif len(agent.diseases) == 0 and self.activeColorOptions["agent"] == "Disease":
            return self.colors["blue"]
        return self.colors["noSex"]

    def recolorByResourceAmount(self, cell, fillColor):
        recolorFactor = 0
        if self.activeColorOptions["environment"] == "Pollution":
            # Since global max pollution changes at each timestep, set constant to prevent misleading recoloring of cells
            maxPollution = 20
            # Once a cell has exceeded the number of colors made possible with maxPollution, keep using the max color
            recolorFactor = min(1, cell.pollution / maxPollution)
        else:
            maxSugar = self.sugarscape.environment.globalMaxSugar
            maxSpice = self.sugarscape.environment.globalMaxSpice
            if maxSugar == 0 and maxSpice == 0:
                recolorFactor = 0
            elif cell.sugar > 0 and cell.spice == 0 and maxSugar > 0:
                recolorFactor = cell.sugar / maxSugar
            elif cell.spice > 0 and cell.sugar == 0 and maxSpice > 0:
                recolorFactor = cell.spice / maxSpice
            else:
                recolorFactor = (cell.sugar + cell.spice) / (maxSugar + maxSpice)
        subcolors = self.hexToInt(fillColor)
        i = 0
        for color in subcolors:
            color = int(color + (255 - color) * (1 - recolorFactor))
            subcolors[i] = color
            i += 1
        fillColor = self.intToHex(subcolors)
        return fillColor

    def resizeInterface(self, event=None):
        # Do not do resizing if capturing a user input event but the event does not come from the GUI window
        if event != None and (event.widget != self.window or (event.widget == self.window and (self.screenHeight == event.height and self.screenWidth == event.width))):
            return
        self.updateScreenDimensions()
        self.updateSiteDimensions()
        self.destroyCanvas()
        self.configureCanvas()
        self.configureEnvironment()

        # Adjust column and row weights
        self.window.columnconfigure(0, weight=1)  # Canvas column
        self.window.columnconfigure(1, weight=0, minsize=self.paddingColumnWidth)  # Padding column
        self.window.columnconfigure(2, weight=0, minsize=self.infoColumnWidth)  # Control column
        self.window.columnconfigure(3, weight=0, minsize=self.paddingColumnWidth)  # Padding column
        self.window.columnconfigure(4, weight=1)
        self.window.rowconfigure(0, weight=1)
        self.window.rowconfigure(5, weight=1)
        for row in range(1, 5):
            self.window.rowconfigure(row, weight=0)

    def updateLabels(self):
        stats = self.sugarscape.runtimeStats
        statsString = f"Timestep: {self.sugarscape.timestep} \nPopulation: {stats['population']} \nMetabolism: {stats['meanMetabolism']:.2f} \n" \
                      f"Movement: {stats['meanMovement']:.2f} \nVision: {stats['meanVision']:.2f} \nGini: {stats['giniCoefficient']:.2f} \n" \
                      f"Trade Price: {stats['meanTradePrice']:.2f} \nTrade Volume: {stats['tradeVolume']:.2f}"
        label = self.widgets["statsLabel"]
        label.config(text=statsString)
        if self.highlightedCell != None:
            cellString = self.updateHighlightedCellStats()
            label = self.widgets["cellLabel"]
            label.config(text=cellString)

    def updateScreenDimensions(self):
        self.screenHeight = self.window.winfo_height()
        self.screenWidth = self.window.winfo_width()

    def updateSiteDimensions(self):
        self.siteHeight = self.screenHeight / self.sugarscape.environmentHeight
        self.siteWidth = (self.screenWidth - self.infoColumnWidth - 2 * self.paddingColumnWidth) / self.sugarscape.environmentWidth
        self.siteHeight = self.siteWidth = min(self.siteHeight, self.siteWidth)
