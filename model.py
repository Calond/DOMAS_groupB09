from Legend import *
import random
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import numpy as np
import math
from Car import CarAgent
from TrafficLight import TrafficLightAgent
SPAWNNUMBER = 4

def lightconnection(lightmatrix, trafficlightlist, intersections):
    # Creates a np array where all 0's are connections between traffic lights (what traffic light sends car to
    # what trafic light).
    for trafficlightfrom in trafficlightlist:
        direction = trafficlightfrom[0][1:3]
        intersection = int(trafficlightfrom[0][3])
        if direction in ["NL", "WD", "SR"]:
            goestointersection = intersection - 1
            if (
                goestointersection > -1
                and (intersection % int(math.sqrt(intersections))) != 0
            ):
                for trafficlightto in trafficlightlist:
                    direction = trafficlightto[0][1]
                    intersection = int(trafficlightto[0][3])
                    if intersection == goestointersection and direction == "W":
                        lightmatrix[
                            int(trafficlightfrom[1]), int(trafficlightto[1])
                        ] = int(0)
        if direction in ["EL", "ND", "WR"]:
            goestointersection = intersection - int(math.sqrt(intersections))
            if goestointersection >= 0:
                for trafficlightto in trafficlightlist:
                    direction = trafficlightto[0][1]
                    intersection = int(trafficlightto[0][3])
                    if intersection == goestointersection and direction == "N":
                        lightmatrix[
                            int(trafficlightfrom[1]), int(trafficlightto[1])
                        ] = int(0)
        if direction in ["SL", "ED", "NR"]:
            goestointersection = intersection + 1
            if goestointersection % int(math.sqrt(intersections)) != 0:
                for trafficlightto in trafficlightlist:
                    direction = trafficlightto[0][1]
                    intersection = int(trafficlightto[0][3])
                    if intersection == goestointersection and direction == "E":
                        lightmatrix[
                            int(trafficlightfrom[1]), int(trafficlightto[1])
                        ] = int(0)
        if direction in ["WL", "SD", "ER"]:
            goestointersection = intersection + int(math.sqrt(intersections))
            if goestointersection < intersections:
                for trafficlightto in trafficlightlist:
                    direction = trafficlightto[0][1]
                    intersection = int(trafficlightto[0][3])
                    if intersection == goestointersection and direction == "S":
                        lightmatrix[
                            int(trafficlightfrom[1]), int(trafficlightto[1])
                        ] = int(0)
    return lightmatrix


def readroadmap():
    # Reads the generatedmap.txt and converts it into a list of lists, which can be used to locate traffic lights
    # and car spawns.
    filepath = "Generatedmap.txt"
    roadmap = []
    spawns = []
    lights = []
    run = 0
    with open(filepath, "r") as roadmapfile:
        text = roadmapfile.readlines()
        header = text[0:4]
        cellsperlane = int(float(header[0].split("=")[1].strip()))
        gridsize = int(float(header[1].split("=")[1].strip()))
        streetlength = int(float(header[2].split("=")[1].strip()))
        intersections = int(float(header[3].split("=")[1].strip()))
        text = text[4:]
        height = len(text[0].split(","))
        numberoflights = 0
        for y, line in enumerate(text):
            road = line.strip().split(",")
            roadmap.append(road)
            for x, tile in enumerate(road):
                if tile.startswith("C"):  # C indicates car spawn
                    spawns.append([[x, y], tile])
                if tile.startswith("T"):  # T indicates traffic light
                    numberoflights += 1
                    lights.append([[x, y], tile])
                    run += 1
    return (
        roadmap,
        spawns,
        lights,
        height,
        cellsperlane,
        intersections,
        streetlength,
        gridsize,
    )


class Intersection(Model):
    """
    Here the model is initialized. The Generatedmap.txt is read in order to locate traffic lights and car spawns.
    Cars and traffic lights are spawned here.
    """

    def __init__(self):
        # self.tactic = "Standard"
        self.tactic = "Offset"
        self.offset = 3
        # self.tactic = "Lookahead"
        # self.tactic = "GreenWave"
        self.schedule = RandomActivation(self)
        [
            self.roadmap,
            self.spawns,
            self.lights,
            self.height,
            self.cellsperlane,
            self.intersections,
            streetlength,
            gridsize,
        ] = readroadmap()
        self.width = self.height
        self.gridsize = gridsize
        self.streetlength = streetlength
        self.grid = MultiGrid(self.width, self.height, True)
        self.running = True
        self.tlightmatrix = np.empty((len(self.lights), len(self.lights)))
        self.tlightmatrix[:] = np.nan
        self.trafficlightlist = []
        self.carID = 0
        self.lightcombinations = [
            ["SR", "SD", "SL", "WR"],
            ["ER", "ED", "EL", "SR"],
            ["NR", "ND", "NL", "ER"],
            ["WR", "WD", "WL", "NR"],
        ]

        self.intersectionmatrix = []  # matrix with intersectionnumbers in the right index
        lastnumber = 0
        for i in range(int(math.sqrt(self.intersections))):
            tempmaptrix = []
            for j in range(int(math.sqrt(self.intersections))):
                tempmaptrix.append(j + lastnumber)
            lastnumber = tempmaptrix[-1] +1
            self.intersectionmatrix.append(tempmaptrix)
        self.intersectionmatrix = np.array(self.intersectionmatrix)

        for i, light in enumerate(self.lights):  # Initializes traffic lights
            intersectionnumber = int(light[1][3])
            intersectiony = np.where(self.intersectionmatrix == intersectionnumber)[0]
            intersectionx = np.where(self.intersectionmatrix == intersectionnumber)[1]
            direction = light[1][1]
            lane = light[1][2]
            location = light[0]
            xlocation = int(location[0])
            ylocation = self.height - 1 - int(location[1])
            trafficlight = TrafficLightAgent(
                f"{xlocation},{ylocation},{light[1][1:3]}",
                self,
                "red",
                direction,
                lane,
                i,
                intersectionnumber,
                self.tactic,
                self.offset,
                [intersectionx, intersectiony],
            )
            self.trafficlightlist.append([light[1], i])
            self.schedule.add(trafficlight)
            self.grid.place_agent(trafficlight, (xlocation, ylocation))

        self.tlightmatrix = lightconnection(
            self.tlightmatrix, self.trafficlightlist, self.intersections
        )

        # Place legend
        self.grid.place_agent(LegendCarIcon("Caricon", self), (65, 68))
        self.grid.place_agent(LegendGreenTlightIcon("GreenTlighticon", self), (65, 69))
        self.grid.place_agent(LegendRedTlightIcon("RedTlighticon", self), (65, 70))

    def step(self):
        """
        Step function that will randomly place cars based on the spawn chance
        and will visit all the agents to perform their step function.
        """

        possible_spawns = [] #reset the list if it is was not empty
        '''
        gets all the empty spawning points where cars can spawn and adds them to the list
        '''
        for spawn in self.spawns:
            location = spawn[0]
            cell_contents = self.grid.get_cell_list_contents([location])
            if not cell_contents:
                possible_spawns.append(spawn)


        '''
        gets a random integer which is between 0 and SPAWNNUMBER that is the number of cars that are spawn.
        For each spawn it will grab an empty spawn place and spawns a car there then remove the spawn place from the list, so there wont spawn a car on top of it.
        '''
        number_of_spawns = random.randint(0, SPAWNNUMBER)
        while number_of_spawns > 0:
            number_of_spawns -= 1
            if possible_spawns:
                spawn = random.choice(possible_spawns)
                possible_spawns.remove(spawn)
                location = spawn[0]
                xlocation = int(location[0])
                ylocation = self.height - 1 - int(location[1])
                direction = spawn[1][1]
                lane = spawn[1][2]
                car = CarAgent(
                f"car{self.carID}", self, 50, direction, lane, [xlocation, ylocation], self.streetlength)
                self.carID += 1
                self.schedule.add(car)
                self.grid.place_agent(car, (xlocation, ylocation))


        self.schedule.step()
