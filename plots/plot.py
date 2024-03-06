import getopt
import json
import os
import re
import sys

datacols = []

def parseDataset(path, dataset, totalTimesteps):
    encodedDir = os.fsencode(path) 
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not filename.endswith('.json'):
            continue
        filePath = path + filename
        fileDecisionModel = re.compile(r"([A-z]*)\d*\.json")
        model = re.search(fileDecisionModel, filename).group(1)
        if model not in dataset:
            continue
        log = open(filePath)
        rawJson = json.loads(log.read())
        dataset[model]["runs"] += 1
        i = 1
        print("Reading log {0}".format(filePath))
        for item in rawJson:
            if item["timestep"] > totalTimesteps:
                break
            if item["timestep"] > dataset[model]["timesteps"]:
                dataset[model]["timesteps"] += 1

            for entry in item:
                if entry in ["agentWealths", "agentTimesToLive", "agentTimesToLiveAgeLimited", "agentTotalMetabolism"]:
                    continue
                if entry not in datacols:
                    datacols.append(entry)
                if entry not in dataset[model]["meanMetrics"]:
                    dataset[model]["meanMetrics"][entry] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["meanMetrics"][entry][i-1] += item[entry]
            i += 1
        if rawJson[-1]["population"] == 0:
            dataset[model]["died"] += 1
        elif rawJson[-1]["population"] < rawJson[0]["population"]:
            dataset[model]["worse"] += 1
    return dataset

def findMeans(dataset):
    print("Finding mean values across {0} timesteps".format(totalTimesteps))
    for model in dataset:
        for column in datacols:
            for i in range(len(dataset[model]["meanMetrics"][column])):
                dataset[model]["meanMetrics"][column][i] = dataset[model]["meanMetrics"][column][i] / dataset[model]["runs"]
    return dataset

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:p:t:o:h"
    longOptions = ("conf=", "outf=", "path=", "help")
    options = {"config": None, "path": None, "outfile": None}
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        exit(0)
    for currArg, currVal in args:
        if currArg in ("-c", "--conf"):
            if currVal == "":
                print("No config file provided.")
                printHelp()
            options["config"] = currVal
        elif currArg in ("-o", "--outf"):
            options["outfile"] = currVal
            if currVal == "":
                print("No data output file path provided.")
                printHelp()
        elif currArg in ("-p", "--path"):
            options["path"] = currVal
            if currVal == "":
                print("No dataset path provided.")
                printHelp()
        elif currArg in ("-h", "--help"):
            printHelp()
    flag = 0
    if options["path"] == None:
        print("Dataset path required.")
        flag = 1
    if options["config"] == None:
        print("Configuration file path required.")
        flag = 1
    if options["outfile"] == None:
        print("Data output file path required.")
        flag = 1
    if flag == 1:
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython parselogs.py --path /path/to/data --conf /path/to/config > results.dat\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-o,--outf\tUse the specified path to data output file.\n\t-p,--path\tUse the specified path to find dataset JSON files.\n\t-h,--help\tDisplay this message.")
    exit(0)

def printSummaryStats(dataset):
    print("Model population performance:\n{0:^30} {1:^5} {2:^5} {3:^5}".format("Decision Model", "Died", "Worse", "Better"))
    for model in dataset:
        formattedModel = formatModels(model)
        better = dataset[model]["runs"] - (dataset[model]["died"] + dataset[model]["worse"])
        print("{0:^30}: {1:^5} {2:^5} {3:^5}".format(formattedModel, dataset[model]["died"], dataset[model]["worse"], better))

def printRawData(dataset, totalTimesteps, outfile):
    file = open(outfile, 'w')
    columnHeads = "timestep"
    for model in dataset:
        for metric in ["pop", "mttl", "strv", "comd", "welt", "maad"]:
            columnHeads += " {0}_{1}".format(model, metric)
    columnHeads += '\n'
    file.write(columnHeads)

    for i in range(totalTimesteps + 1):
        line = str(i)
        for model in dataset:
            line += " {0} {1} {2} {3} {4} {5}".format(dataset[model]["meanMetrics"]["population"][i], dataset[model]["meanMetrics"]["agentMeanTimeToLive"][i],
                                                  dataset[model]["meanMetrics"]["agentStarvationDeaths"][i], dataset[model]["meanMetrics"]["agentCombatDeaths"][i],
                                                  dataset[model]["meanMetrics"]["agentWealthTotal"][i], dataset[model]["meanMetrics"]["meanAgeAtDeath"][i])
        line += '\n'
        file.write(line)
    file.close()

def generatePlots(config, modelFormattings, outfile, pointInterval):
    if "population" in config["plots"]:
        generatePopulationPlot(modelFormattings, outfile, pointInterval)
    if "meanttl" in config["plots"]:
        generateMeanTimeToLivePlot(modelFormattings, outfile, pointInterval)
    if "wealth" in config["plots"]:
        generateTotalWealthPlot(modelFormattings, outfile, pointInterval)
    if "wealthNormalized" in config["plots"]:
        generateTotalWealthNormalizedPlot(modelFormattings, outfile, pointInterval)
    if "starvationCombat" in config["plots"]:
        generateStarvationAndCombatPlot(modelFormattings, outfile, pointInterval)
    if "meanAgeAtDeath" in config["plots"]:
        generateMeanAgeAtDeathPlot(modelFormattings, outfile, pointInterval)

def generatePopulationPlot(modelFormattings, outfile, pointInterval):
    print("Generating population plot script")
    plot = open("population.plg", 'w')
    writePlotConfig(plot, "Population", "population.pdf")
    writePlotLines(plot, modelFormattings, "\'{model}_pop\'", pointInterval)
    plot.close()
    os.system(f"gnuplot -c population.plg {outfile}")

def generateMeanAgeAtDeathPlot(modelFormattings, outfile, pointInterval):
    print("Generating mean age at death plot script")
    plot = open("mean_age_at_death.plg", 'w')
    writePlotConfig(plot, "Mean Age at Death", "mean_age_at_death.pdf")
    writePlotLines(plot, modelFormattings, "\'{model}_maad\'", pointInterval)
    plot.close()
    os.system(f"gnuplot -c mean_age_at_death.plg {outfile}")

def generateMeanTimeToLivePlot(modelFormattings, outfile, pointInterval):
    print("Generating mean time to live plot script")
    plot = open("meanttl.plg", 'w')
    writePlotConfig(plot, "Mean Time to Live", "meanttl.pdf")
    writePlotLines(plot, modelFormattings, "\'{model}_mttl\'", pointInterval)
    plot.close()
    os.system(f"gnuplot -c meanttl.plg {outfile}")

def generateTotalWealthPlot(modelFormattings, outfile, pointInterval):
    print("Generating total wealth plot script")
    plot = open("wealth.plg", 'w')
    writePlotConfig(plot, "Total Wealth", "wealth.pdf")
    writePlotLines(plot, modelFormattings, "\'{model}_welt\'", pointInterval)
    plot.close()
    os.system(f"gnuplot -c wealth.plg {outfile}")

def generateTotalWealthNormalizedPlot(modelFormattings, outfile, pointInterval):
    print("Generating total wealth normalized plot script")
    plot = open("wealth_normalized.plg", 'w')
    writePlotConfig(plot, "Total Wealth / Population", "wealth_normalized.pdf")
    writePlotLines(plot, modelFormattings, "(column('{model}_welt')/column('{model}_pop'))", pointInterval)
    plot.close()
    os.system(f"gnuplot -c wealth_normalized.plg {outfile}")

def generateStarvationAndCombatPlot(modelFormattings, outfile, pointInterval):
    print("Generating starvation and combat deaths plot script")
    plot = open("deaths.plg", 'w')
    writePlotConfig(plot, "Deaths / Population", "deaths.pdf")
    writePlotLines(plot, modelFormattings, "((column('{model}_strv') + column('{model}_comd'))/column('{model}_pop'))", pointInterval)
    plot.close()
    os.system(f"gnuplot -c deaths.plg {outfile}")

def writePlotConfig(file, yLabel, outfile):
    config = f"set xlabel \"Timestep\"\n"
    config += f"set ylabel \"{yLabel}\"\n"
    config += "set lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\n"
    config += "set key outside above\n"
    config += f"set term pdf font \"Times,20\"\nset output \"{outfile}\"\n\n"
    
    file.write(config)

def writePlotLines(file, modelFormattings, plotVariable, pointInterval):
    lines = "plot "
    for formatting in modelFormattings:
        model = formatting["model"]
        formattedModel = formatting["formattedModel"]
        lineColor = formatting["lineColor"]
        pointType = formatting["pointType"]
        currentPlotVariable = plotVariable.format(model = model)

        lines += (
            f'ARGV[1] using \'timestep\':{currentPlotVariable} '
            f'with linespoints pointinterval {pointInterval} '
            f'pointsize 0.75 lc \'{lineColor}\' '
            f'lt 1 dt 1 pt {pointType} title \'{formattedModel}\', \\\n'
        )

    lines = lines.rstrip(', \\\n')
    file.write(lines)

def formatModels(models):
    if '_' in models:
        return getAbbreviations(models.split('_'))
    elif models == "none" or models == "rawSugarscape":
        return "Raw Sugarscape"
    elif "bentham" in models:
        return "Utilitarian (" + getUppercase(models) + ")"
    elif "egoistic" in models:
        return "Egoist (" + getUppercase(models) + ")"
    elif "altruistic" in models:
        return "Altruist (" + getUppercase(models) + ")"
    else:
        return "Error getting name"

def getAbbreviations(models):
    abbreviations = []
    for model in models:
        abbreviation = model[0] + getUppercase(model)
        abbreviations.append(abbreviation)
    return ', '.join(abbreviations)

def getUppercase(model):
    return ''.join(char for char in model if char.isupper())

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    config = options["config"]
    outfile = options["outfile"]
    configFile = open(config)
    config = json.loads(configFile.read())["dataCollectionOptions"]
    configFile.close()
    totalTimesteps = config["plotTimesteps"]
    models = config["decisionModels"]
    # Flatten nested lists to get same model representation as in filename
    for i in range(len(models)):
        # models[i] = formatModels(models[i])
        if isinstance(models[i], list):
            models[i] = '_'.join(models[i])

    lineColors = ["magenta", "cyan", "gold", "red", "green", "blue"]
    pointTypes = [0, 1, 2, 4, 6, 8]
    if len(models) > len(lineColors):
        print("Warning: More decision models than available colors. Some models will use the same color.")
    
    modelFormattings = []
    for i, model in enumerate(models):
        formattedModel = formatModels(model)
        lineColor = lineColors[i % len(lineColors)]
        pointType = pointTypes[i % len(pointTypes)]
        modelFormattings.append({
            "model": model,
            "formattedModel": formattedModel,
            "lineColor": lineColor,
            "pointType": pointType
        })

    dataset = {}
    for model in models:
        dataset[model] = {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}}

    if not os.path.exists(path):
        print("Path {0} not recognized.".format(path))
        printHelp()

    dataset = parseDataset(path, dataset, totalTimesteps)
    dataset = findMeans(dataset)
    printRawData(dataset, totalTimesteps, outfile)
    generatePlots(config, modelFormattings, outfile, totalTimesteps / 10)
    printSummaryStats(dataset)
    exit(0)
