from collections import deque
from pacman import Pacman
from nodes import *
from pellets import *

def depth_first_search(self, pacman, nodegroup, pellets):
    self.nodes = nodegroup
    self.pacman = pacman
    self.pellets = pellets
    self.visited = {}
    self.pelletLocation = None
    self.search = deque()

    self.pacman_node = self.nodes.getNodeFromPixels(pacman.position.asInt())

    self.search.append(self.pacman_node)
    while(self.pelletLocation == None):
        temp = self.search.popleft()
        self.visited[temp] = True
        temppellet = pellet(temp.position.asInt())
        for pellet in pellets:
            if pellet == temppellet:
                self.pelletLocation = pellet.position
        for n in temp.neighbors.keys():
            if temp.neighbors[n] is not None:
                if self.visited[temp.neighbors[n]] != True:
                    self.search.append(temp.neighbors[n])
                    
    return self.pelletLocation


