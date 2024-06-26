import pygame
from pygame.locals import *
from vector import Vector2
from constants import *
from entity import Entity
from sprites import PacmanSprites
from random import randint

class Pacman(Entity):
    def __init__(self, node):
        Entity.__init__(self, node)
        self.name = PACMAN
        self.color = YELLOW
        self.direction = LEFT
        #self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)

        self.directionMethod = self.goalDirection

        self.goal = self.position

    def setPosition(self):
        self.position = self.node.position.copy()

    # def update(self, dt):
    #     self.position += self.directions[self.direction] * self.speed * dt

    #     if self.overshotTarget():
    #         self.node = self.target
    #         directions = self.validDirections()
    #         direction = self.directionMethod(directions)

    #         if not self.disablePortal:
    #             if self.node.neighbors[PORTAL] is not None:
    #                 self.node = self.node.neighbors[PORTAL]
            
    #         if self.position == self.goal:
    #             self.direction = STOP
    #         else:
                    
    #             self.target = self.getNewTarget(direction)
    #             if self.target is not self.node:
    #                 self.direction = direction
    #             else:
    #                 self.target = self.getNewTarget(self.direction)
                
    #         self.setPosition()

    def update(self, dt):
        self.position += self.directions[self.direction] * self.speed * dt

        if self.overshotTarget():
            self.node = self.target
            directions = self.validDirections()
            direction = self.directionMethod(directions)
            if not self.disablePortal:
                if self.node.neighbors[PORTAL] is not None:
                    self.node = self.node.neighbors[PORTAL]
            self.target = self.getNewTarget(direction)
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)
            
            self.setPosition()

    def randomDirection(self, directions):
        return directions[randint(0, len(directions))]

    def goalDirection(self, directions):
        distances = []
        for direction in directions:
           # self.node.position
            vec = self.node.position + self.directions[direction] * TILEWIDTH - self.goal
            distances.append(vec.magnitudeSquared())
        index = distances.index(min(distances))
        return directions[index]
    
    def getValidKey(self):
        key_pressed = pygame.key.get_pressed()
        if key_pressed[K_UP]:
            return UP
        if key_pressed[K_DOWN]:
            return DOWN
        if key_pressed[K_LEFT]:
            return LEFT
        if key_pressed[K_RIGHT]:
            return RIGHT
        return STOP

    def eatPellets(self, pelletList):
        for pellet in pelletList:
            if self.collideCheck(pellet):
                return pellet
        return None
    
    def collideGhost(self, ghost):
        return self.collideCheck(ghost)

    def collideCheck(self, other):
        d = self.position - other.position
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        if dSquared <= rSquared:
            return True
        return False
    
    def reset(self):
        Entity.reset(self)
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
    
    def die(self):
        self.alive = False
        self.direction = STOP


