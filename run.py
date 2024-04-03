import pygame
from pygame.locals import *
from constants import *
from pacman import Pacman
from nodes import NodeGroup
from pellets import *
from ghosts import GhostGroup
from pauser import Pause
from text import TextGroup
from sprites import LifeSprites
from sprites import MazeSprites
from collections import deque

import numpy as np
import time 
import random

class GameController(object):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREENSIZE, 0, 32)
        self.background = None
        self.clock = pygame.time.Clock()
        self.pause = Pause(True)
        self.level = 0
        self.lives = 5
        self.score = 0
        self.textgroup = TextGroup()
        self.lifesprites = LifeSprites(self.lives)
        self.t0 = time.time()
        self.t1 = time.time()

    def setBackground(self):
        self.background = pygame.surface.Surface(SCREENSIZE).convert()
        self.background.fill(BLACK)
    
    def startGame(self):
        self.setBackground()
        self.mazesprites = MazeSprites("./maze/maze1.txt", "./maze/maze1_rotation.txt")
        self.background = self.mazesprites.constructBackground(self.background, self.level%5)
        self.nodes = NodeGroup("./maze/maze1.txt")

        self.nodes.setPortalPair((0,17), (27,17))

        homekey = self.nodes.createHomeNodes(11.5,14)
        self.nodes.connectHomeNodes(homekey, (12,14), LEFT)
        self.nodes.connectHomeNodes(homekey, (15,14), RIGHT)

        self.pacman = Pacman(self.nodes.getNodeFromTiles(15, 26))
        self.pacman_start_node = self.pacman.position

        self.pellets = PelletGroup("./maze/maze1.txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)

        #self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 0+14))
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))
        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(0+11.5, 3+14))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(4+11.5, 3+14))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(2+11.5,3+14))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, LEFT, self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, RIGHT, self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.nodes.denyAccessList(12, 14, UP, self.ghosts)
        self.nodes.denyAccessList(15, 14, UP, self.ghosts)
        self.nodes.denyAccessList(12, 26, UP, self.ghosts)
        self.nodes.denyAccessList(15, 26, UP, self.ghosts)

        print(len(self.pellets.pelletList))
    
    def update(self):
        dt = self.clock.tick(30) / 1000.0
        self.textgroup.update(dt)
        self.pellets.update(dt)
        if not self.pause.paused:
            # if(self.pacman.position == self.pacman.goal):
            #     print("Goal Changed")
            self.pacman_new_goal = self.a_star(self.pacman, self.nodes, self.pellets)
            self.pacman.goal = self.pacman_new_goal
            
            print(self.pacman.goal)
            #print(self.pacman.position)

            self.pacman.update(dt)
            self.score -= 1

            self.ghosts.update(dt)
            self.checkPelletEvents()
            self.checkGhostEvents()
        afterPauseMethod = self.pause.update(dt)
        if afterPauseMethod is not None:
            afterPauseMethod()
        self.checkEvents()
        self.render()
    
    def updateScore(self, points):
        self.score += points
        self.textgroup.updateScore(self.score)
    
    def checkEvents(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    if self.pacman.alive:
                        self.pause.setPause(playerPaused=True)
                        if not self.pause.paused:
                            self.textgroup.hideText()
                            self.showEntities()
                        else:
                            self.textgroup.showText(PAUSETXT)
                            self.hideEntities()
    
    def render(self):
        self.screen.blit(self.background, (0,0))
        #self.nodes.render(self.screen)
        self.pellets.render(self.screen)
        self.pacman.render(self.screen)
        self.ghosts.render(self.screen)
        self.textgroup.render(self.screen)

        for i in range(len(self.lifesprites.images)):
            x = self.lifesprites.images[i].get_width() * i
            y = SCREENHEIGHT - self.lifesprites.images[i].get_height()
            self.screen.blit(self.lifesprites.images[i], (x, y))

        pygame.display.update()
    
    def checkPelletEvents(self):
        pellet = self.pacman.eatPellets(self.pellets.pelletList)
        if pellet:
            self.pellets.numEaten += 1
            self.updateScore(pellet.points)
            #if self.pellets.numEaten == 30:
            #    self.ghosts.inky.startNode.allowAccess(RIGHT, self.ghosts.inky)
            #if self.pellets.numEaten == 70:
            #    self.ghosts.clyde.startNode.allowAccess(LEFT, self.ghosts.clyde)
            self.pellets.pelletList.remove(pellet)
            if pellet.name == POWERPELLET:
                self.ghosts.startFreight()
            if self.pellets.isEmpty():
                self.hideEntities()
                self.score += 1000
                self.pause.setPause(pauseTime=3,func=self.nextLevel)
    
    def checkGhostEvents(self):
        for ghost in self.ghosts:
            if self.pacman.collideGhost(ghost):
                if ghost.mode.current is FREIGHT:
                    self.pacman.visible = False
                    ghost.visible = False
                    self.updateScore(ghost.points)
                    self.textgroup.addText(str(ghost.points), WHITE, ghost.position.x, ghost.position.y, 8, time=1)
                    self.ghosts.updatePoints()
                    self.pause.setPause(pauseTime=1, func=self.showEntities)
                    ghost.startSpawn()
                    self.nodes.allowHomeAccess(ghost)
                elif ghost.mode.current is not SPAWN:
                    if self.pacman.alive:
                        self.lives -= 1
                        self.lifesprites.removeImage()
                        self.pacman.die()
                        self.ghosts.hide()
                        if self.lives <= 0:
                            self.pause.setPause(pauseTime=3, func=self.restartGame)
                        else:
                            self.pause.setPause(pauseTime=3, func=self.resetLevel)
    
    def showEntities(self):
        self.pacman.visible = True
        self.ghosts.show()
    
    def hideEntities(self):
        self.pacman.visible = False
        self.ghosts.hide()
    
    def nextLevel(self):
        #self.showEntities()
        #self.level += 1
        self.pause.paused = True
        #self.startGame()
        #self.textgroup.updateLevel(self.level)
    
    def restartGame(self):
        self.lives = 5
        self.level = 0
        self.pause.paused = True
        self.startGame()
        self.score = 0
        self.textgroup.updateScore(self.score)
        self.textgroup.updateLevel(self.level)
        self.textgroup.showText(READYTXT)
        self.lifesprites.resetLives(self.lives)
    
    def resetLevel(self):
        self.pause.paused = True
        self.pacman.reset()
        self.ghosts.reset()
        self.textgroup.showText(READYTXT)

    def depth_first_search(self, pacman, nodegroup, pellets):
        self.nodes = nodegroup
        self.pacman = pacman
        self.pellets = pellets
        self.visited = {}
        self.pelletLocation = self.pacman_start_node
        self.search = deque()
        self.pos = pacman.position.asTuple()

        self.pacman_node = self.nodes.getNodeFromPixels(self.pos[0],self.pos[1])

        self.search.append(self.pacman_node)
        while(len(pellets.pelletList) != 0):
            if self.search:
                temp = self.search.pop()
            else:
                break
            self.visited[temp.position.asTuple()] = True
            
            temppellet = Pellet(1,1)
            temppellet.position = Vector2(temp.position.asTuple()[0],temp.position.asTuple()[1])

            #print("Temp Pellet:" + str(temppellet.position))
            for pellet in pellets.pelletList:
                if pellet.position == temppellet.position:
                    self.pelletLocation = pellet.position
            for n in temp.neighbors.keys():
                if temp.neighbors[n] is not None:
                    if self.visited.get(temp.neighbors[n].position.asTuple()) != True:
                        self.search.append(temp.neighbors[n])      

        return self.pelletLocation

    def breadth_first_search(self, pacman, nodegroup, pellets):
        self.nodes = nodegroup
        self.pacman = pacman
        self.pellets = pellets
        self.visited = {}
        self.pelletLocation = pacman.position
        self.search = deque()
        self.pos = pacman.position.asTuple()

        self.pacman_node = self.nodes.getNodeFromPixels(self.pos[0],self.pos[1])

        self.search.append(self.pacman_node)
        while(self.pelletLocation == pacman.position):
            if self.search:
                temp = self.search.popleft()
            else:
                break
            #print(temp.position)
            self.visited[temp.position.asTuple()] = True
            
            temppellet = Pellet(1,1)
            temppellet.position = Vector2(temp.position.asTuple()[0],temp.position.asTuple()[1])

            #print("Temp Pellet:" + str(temppellet.position))

            for pellet in pellets.pelletList:
                if pellet == temppellet:
                    print("Pellet found!")
                    self.pelletLocation = pellet.position
            for n in temp.neighbors.keys():
                if temp.neighbors[n] is not None:
                    if self.visited.get(temp.neighbors[n].position.asTuple()) != True:
                        self.search.append(temp.neighbors[n])      

        return self.pelletLocation

    def a_star(self, pacman, nodegroup, pellets):
        self.nodes = nodegroup
        self.pacman = pacman
        self.pellets = pellets
        self.visited = {}
        self.pellet_distance = {}
        self.pelletLocation = pacman.position
        self.search = deque()
        self.pos = pacman.position.asTuple()

        #self.pacman_node = self.pacman.position
        
        #Evulation function of how many pellets are nearby

        def evaluation(a_pellet, pelletList, nodeGroup):
            pellet = a_pellet
            nodes = nodeGroup
            pellets = pelletList
            score = 0

            pellet_node = nodes.getNodeFromPixels(pellet.position.asTuple()[0],pellet.position.asTuple()[1])
            
            if pellet_node != None:
                for n in pellet_node.neighbors.keys():
                    if pellet_node.neighbors[n] is not None:
                        tempTuple = pellet_node.neighbors[n].position.asTuple()
                        tempPellet = Pellet(1,1)
                        tempPellet.position = Vector2(tempTuple[0], tempTuple[1])
                        for an_pellet in pellets:
                            if tempPellet == an_pellet:
                                score += 10
            return score
        
        if(len(pellets.pelletList) != 0):
            self.pellet_distance = {}
            for pellet in pellets.pelletList:
                distance = pellet.position - self.pacman.position
                distance = distance.magnitudeSquared()
                eval_score = evaluation(pellet, self.pellets.pelletList, self.nodes)
                self.pellet_distance[pellet.position.asTuple()] = distance/100 - eval_score
                print(distance/100 + eval_score)
            temp = min(self.pellet_distance, key=self.pellet_distance.get)
            self.pelletLocation = Vector2(temp[0], temp[1])

        return self.pelletLocation

if __name__ == "__main__":
    game = GameController()
    game.startGame()

    while True:
        game.update()