#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

@author: vincent.deruaz, mathieu.rosser
'''

import math
import time
from random import randint
import pygame
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN, K_ESCAPE

def ga_solve(file=None, gui=True, maxtime=0):
	
	if file is None:
		cities = []
	else:
		cities = Parser(file).cities
	
	pvc = PVC(cities, maxtime)
		
	if gui:
		Gui(pvc)
	
	else:
		pvc.compute()
	
	cities_names = [c.name for c in pvc.ordered_cities]
	
	return pvc.total_distance, cities_names
	
class PVC():
	
	def __init__(self, cities, maxtime):
		self.cities = cities
		self.maxtime = maxtime
		
		self.total_distance = 0
		self.total_time = 0
		self.ordered_cities = list(self.cities)
		
		self.last_distances = []
		
	def compute(self, gui=None):
# 		print("compute")
# 		print(self.cities)
		
		self.start = time.clock()
		self.i = 0
		population = Population(self.ordered_cities)

		while not self.is_ended():
# 			print("x")
			population.update()
			
			self.ordered_cities = population.solutions[0].cities
			self.total_distance = population.solutions[0].distance()
						
			self.last_distances.append(self.total_distance)
			
			if gui:
				gui.draw()
			
# 		print(population)
		
	def is_ended(self):
		self.total_time = time.clock() - self.start
		
		if (self.maxtime is not None and self.maxtime > 0):
			return self.total_time >= self.maxtime
		
		length = len(self.last_distances)
				
		if length > 50:
			self.last_distances.pop(0)
			length -= 1
			
			print(self.last_distances)
			
			mean_dist = sum(self.last_distances) / length
			std_dev = math.sqrt(1 / length * sum([pow(x - mean_dist, 2) for x in self.last_distances]))

			print(std_dev)
			
			return std_dev <= 1e-11
		
		return False
		
		
# 		self.i += 1
# 		
# 		return self.i <= 100
		
class Population():
	
	def __init__(self, cities):
		basic_solution = Solution(list(cities))
		
		self.solutions = [basic_solution]
		
		# doublons ???
		for _ in range(10):
			s = basic_solution.clone()
			
			for _ in range(5):
				s.mutate()
			
			self.solutions.append(s)
			
		self.order_by_distance()
		
# 		print("test")
			
	def __repr__(self):
		return str(self.solutions)
	
	def order_by_distance(self):
		self.solutions.sort(key=Solution.distance)
		
	def update(self):
		
		# 1. Sélection (manquante ici!)
		# 2. Croisements et mutations, on essaye de garder quelques élites...
		
		elite = math.ceil(len(self.solutions) / 3)
		if elite % 2 != 0:
			elite += 1
		
		solutions_elite = [self.solutions[i] for i in range(elite)]
		
		j = -1
		
		for i in range(elite - 1):
			child1, child2 = solutions_elite[i].crossover(solutions_elite[i + 1])
			self.solutions[j] = child1
			self.solutions[j - 1] = child2
			
			j -= 2
		
# 		solution1, solution2 = self.solutions[0], self.solutions[1]
# 		solution3, solution4 = self.solutions[2], self.solutions[3]
# 		
# 		child1, child2 = solution1.crossover(solution2)
# 		child3, child4 = solution3.crossover(solution4)
# 		
# 		self.solutions[-1] = child1
# 		self.solutions[-2] = child2
# 		self.solutions[-3] = child3
# 		self.solutions[-4] = child4
		
		rate = 0
		for c in self.solutions:
			if rate % 5 == 0:
				c.mutate()
			rate += 1
			
		self.order_by_distance()
					

class Solution():
	DIVISOR_CROSSOVER = 3

	def __init__(self, cities):
		self.cities = cities
		
	def mutate(self):
		ind1, ind2 = self.random_index()
		
		self.cities[ind1], self.cities[ind2] = self.cities[ind2], self.cities[ind1]
		return self
	
	def clone(self):
		return Solution(list(self.cities))
		
	def random_index(self):
		ind = len(self.cities) - 1
		return randint(0, ind), randint(0, ind)
	
	def crossover(self, solution2):
		length = len(self.cities)
		ind_max = length - 1
		length_cross = math.floor(ind_max / Solution.DIVISOR_CROSSOVER)
		ind_start = randint(1, ind_max - length_cross)
# 		print(ind_start)
		ind_stop = ind_start + length_cross - 1
		
		new_cities1 = [None for _ in self.cities]
		new_cities2 = [None for _ in self.cities]
		
		for i in range(ind_start, ind_stop + 1):
			new_cities1[i] = solution2.cities[i]
			new_cities2[i] = self.cities[i]
			
# 		print(new_cities1)
		
		self.crossover_ox(solution2, new_cities1, ind_stop, length)
		self.crossover_ox(self, new_cities2, ind_stop, length)

		return Solution(new_cities1), Solution(new_cities2)
	
	def crossover_ox(self, solution, new_cities, ind_stop, length):
		j = ind_stop + 1
		for i in range(j, ind_stop + length):
			city = solution.cities[i % length]
			
			if new_cities[j % length] is None and city not in new_cities:
				new_cities[j % length] = city
				j += 1
			
			# code mort
			#while new_cities[j % length] is not None:
			#	j += 1

	
	def distance(self):
		distance = 0.0
		
		old_city = self.cities[-1]
		
		for city in self.cities:
			distance += self.distance_euclidean(city, old_city)
			old_city = city

		return distance
	
	def distance_euclidean(self, city1, city2):
		return math.hypot(city1.x - city2.x, city1.y - city2.y)

	def __repr__(self):
		return str(self.cities)

class Parser():
	def __init__(self, path):
		self.path = path
		
		self.cities = []
		
		with open(path) as file:
			
			for line in file:
				name, x, y = line.split()
				self.cities.append(City(name, int(x), int(y)))

class City():
	def __init__(self, name, x, y):
		self.name = name
		self.x = x
		self.y = y
		
	def pos(self):
		return (self.x, self.y)
	
	def __str__(self):
		return "%s (%d, %d)" %(self.name, self.x, self.y)
	
	def __repr__(self):
		return self.__str__()

class Gui():
	
	def __init__(self, pvc):		
# 		cities = pvc.cities
		self.pvc = pvc
		self.display_path = False
		
		screen_x = 500
		screen_y = 500
		
		self.city_color = [255,255,255] # blue
		self.city_radius = 2
		
		self.font_color = [255,255,255] # white
		
		pygame.init()
		window = pygame.display.set_mode((screen_x, screen_y))
		pygame.display.set_caption('Voyageur du commerce')
		
		self.screen = pygame.display.get_surface() 
		self.font = pygame.font.Font(None,30)
		self.font_cities = pygame.font.Font(None,18)		

		self.draw()
		
		collecting = True
		
		while collecting:
			for event in pygame.event.get():
				if event.type == QUIT:
					return
				elif event.type == KEYDOWN and event.key == K_RETURN:
					collecting = False
				elif event.type == MOUSEBUTTONDOWN:
					pos = pygame.mouse.get_pos()
					self.pvc.ordered_cities.append(City("v%i" % len(self.pvc.ordered_cities), pos[0], pos[1]))
					self.draw()
		
		self.display_path = True
		pvc.compute(self)
		
		self.screen.fill(0)
		self.draw()
		#text = self.font.render("Un chemin, pas le meilleur!", True, self.font_color)
		#textRect = text.get_rect()
		#self.screen.blit(text, textRect)
# 		pygame.display.flip()
		
		while True:
			event = pygame.event.wait()
			if event.type == KEYDOWN or event.type == QUIT: break

	def draw(self):
		self.screen.fill(0)
		for c in self.pvc.ordered_cities:
			pygame.draw.circle(self.screen, self.city_color, c.pos(), self.city_radius)
			
			label = self.font_cities.render("%s (%i,%i)" % (c.name, c.x, c.y), True, self.font_color)
			label_rect = label.get_rect()
			label_rect.centerx = c.x + label_rect.width / 1.6
			label_rect.centery = c.y
			self.screen.blit(label, label_rect)
		
		text = self.font.render("Nombre: %i Distance: %.3f Temps: %.3f" %(len(self.pvc.ordered_cities), self.pvc.total_distance, self.pvc.total_time), True, self.font_color)
		textRect = text.get_rect()
		self.screen.blit(text, textRect)
			
		if self.display_path:
			pygame.draw.lines(self.screen, self.city_color, True, [c.pos() for c in self.pvc.ordered_cities])
			
		pygame.display.flip()

if __name__ == '__main__':
	
	import argparse

	parser = argparse.ArgumentParser(description="Problème du voyageur de commerce avec algorithme génétique")
	
	parser.add_argument('--nogui', action="store_true", help="Ne pas afficher l'interface graphique")
	parser.add_argument('--maxtime', type=int, action="store", help="Arrêter la recherche après maxtime secondes")
	parser.add_argument("filename", type=str, default=None, nargs="?", help="Fichier contenant les villes à visiter")

	args = parser.parse_args()
	
	gui = not args.nogui
	maxtime = args.maxtime if args.maxtime is not None else 0
	file = args.filename
	
	print("Gui: %d"%gui)
	print("Maxtime: %d"%maxtime)
	print("File: %s" %file)
	print()

	total_distance, cities = ga_solve(file, gui, maxtime)
	
	print("Distance totale:\n\t %d" %total_distance)
	print("Villes à visiter dans l'ordre:\n\t %s" %str(cities))