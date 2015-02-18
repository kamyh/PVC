#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Algorithme génétique pour résolution du problème du voyageur de commerce - PVC

Résoud un PVC, soit à partir d'un fichier ou d'une interface graphique avec mise à jour visuelle ou non (gui)
La résolution s'arrête lorsqu'une stagnation est constatée ou après un temps maximum

@author: vincent.deruaz, mathieu.rosser
'''

import math
import time
import random
import pygame
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN, K_ESCAPE

def ga_solve(file=None, gui=True, maxtime=0):
	'''
		Résolution d'un PVC
		@param file: 	fichier de villes à charger
		@param gui: 	affiche l'interface graphique
		@param maxtime: temps maximum de calcul
		@return: 		la distance totale calculée, la liste des villes dans l'ordre de passage
	'''
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
	''' 
		Classe résolvant un PVC, à partir d'une liste de villes, dans un temps maximum ou jusqu'à stagnation 
		Résultats: total_distance, total_time, ordered_cities
	'''
	
	def __init__(self, cities, maxtime):
		self.cities = cities
		self.maxtime = maxtime
		
		self.total_distance = 0
		self.total_time = 0
		self.ordered_cities = list(self.cities)
		
		self.last_distances = []
		
	def compute(self, gui=None):	
		''' résoud un PVC à partir des données courantes '''
		self.start = time.clock()
		self.population = Population(self.ordered_cities)

		while not self.is_ended():
			self.population.update()
			
			self.ordered_cities = self.population.solutions[0].cities
			self.total_distance = self.population.solutions[0].distance()
							
			self.last_distances.append(self.total_distance)
			
			if gui:
				gui.draw()
					
	def is_ended(self):
		''' vérifie se calcul est terminé par stagnation ou temps '''
		self.total_time = time.clock() - self.start
		
		if (self.maxtime is not None and self.maxtime > 0):
			return self.total_time >= self.maxtime
		
		length = len(self.last_distances)
		
# 		print(length)
		if length > 4 * self.population.size:	# TODO: changer 200, varier selon le nb de villes par exp
			self.last_distances.pop(0)
			length -= 1

			mean_dist = sum(self.last_distances) / length
			std_dev = math.sqrt(1 / length * sum([pow(x - mean_dist, 2) for x in self.last_distances]))

# 			print(std_dev)
			return std_dev <= 1e-10	# vérifier epsylon
		
		return False

		
class Population():
	''' 
		Classe représentant une population de solutions
		La population évolue par sélection, croisement et mutation
	'''
	# TODO: taille ? ajuster selon nb de villes ?
	SIZE = 100	# paire
	
	def __init__(self, cities):
		self.size = min(4 * len(cities), 50)
		basic_solution = Solution(list(cities))
		
		self.solutions = [basic_solution]
		
		# TODO: doublons ???
		for _ in range(self.size - 1):
			s = basic_solution.clone()
			
			s.randomize()
			
# 			for _ in range(50):
# 				s.mutate(True)
			
			self.solutions.append(s)
			
		self.order_by_distance()
					
	def __repr__(self):
		return str(self.solutions)
	
	def order_by_distance(self):
		self.solutions.sort(key=Solution.distance)
		
		while len(self.solutions) > self.size:
			self.solutions.pop()
		
	def update(self):
		''' mise à jour de la population par sélection, croisement et mutation '''
		# 1. Sélection (manquante ici!)
		# 2. Croisements et mutations, on essaye de garder quelques élites...
				
# 		elite = self.size // 20
# 		if elite % 2 != 0:
# 			elite += 1
			
		taux_elite = 0.20
		elite = int(self.size * taux_elite)
		
		# TODO: optimiser
		
		new_solutions = self.solutions[:elite]
		
# 		for i in range(elite):
# 			new_solutions.append(new_solutions[i].clone().mutate(True))
# 			
# 			if i < elite - 1:
# 				child1, child2 = self.solutions[i].crossover(self.solutions[i + 1], True)
# 				new_solutions.append(child1.mutate(True))
# 				new_solutions.append(child2.mutate(True))
		
		while len(new_solutions) < self.size:
# 			a, b = self.random_solution_index()
			#print("a, b = %d, %d" %(a, b))
			a = self.roulette_selection()
			b = self.roulette_selection()

			#child1, child2 = self.solutions[a].crossover(self.solutions[b])
			
# 			child1, child2 = a.crossover(b)
			child1 = a.crossover_greedy(b)
			child2 = b.crossover_greedy(a)
			
			#if child1 not in new_solutions:
			new_solutions.append(child1)
				
			#if child2 not in new_solutions:
			new_solutions.append(child2)
			
		for s in new_solutions:
			s.mutate()

		self.solutions = new_solutions
		
		self.order_by_distance()
		
		""" mutation elite """	
# 		for i in range(elite):
# 			self.solutions.append(self.solutions[i].clone().mutate(True))
		
		""" croisement élite """
# 		j = -1
# 		
# 		for i in range(0, elite - 1, 2):
# 			child1, child2 = solutions_elite[i].crossover(solutions_elite[i + 1])
# 			self.solutions.append(child1)
# 			self.solutions.append(child2)
# 		
# 			j -= 2
		
		""" nouveaux croisements / mutations """
# 		while len(self.solutions) < 2 * Population.SIZE:
# 			a = randint(0, Population.SIZE - 1)
# 			b = randint(0, Population.SIZE - 1)
# 			
# 			child1, child2 = self.solutions[a].crossover(self.solutions[b])
# 			if child1 is not None:
# 				self.solutions.append(child1)
# 				self.solutions.append(child2)

		""" ajout croisement/mutation """
# 		for _ in range(0, Population.SIZE - 1, 2):
# 			a = randint(0, Population.SIZE - 1)
# 			b = randint(0, Population.SIZE - 1)
# 			
# 			child1, child2 = self.solutions[a].crossover(self.solutions[b])
# # 			self.solutions[i] = child1.mutate()
# # 			self.solutions[i + 1] = child2.mutate()
# 			self.solutions.append(child1.mutate())
# 			self.solutions.append(child2.mutate())

# 		for i in range(elite, 2 * Population.SIZE):
# 			self.solutions[i].mutate()
		

		""" mutation complète """
# 		for c in self.solutions:
# 			c.mutate()

		""" croisement élite - remplacement """
# 		j = -1
# 		
# 		for i in range(0, elite - 1, 2):
# 			child1, child2 = solutions_elite[i].crossover(solutions_elite[i + 1])
# 			self.solutions[j] = child1
# 			self.solutions[j - 1] = child2
# 			
# 			j -= 2	
	
	def random_solution_index(self):
		good_index = random.randint(0, 100) < 0
		# TODO: utile ?
		max_index = self.size - 1 if not good_index else self.size // 4
		#print("MAX=%d" %max_index)
		return random.randint(0, max_index), random.randint(0, max_index)

	def roulette_selection(self):
		max_dist = self.solutions[-1].distance()
		
		s = 0

		for c in self.solutions:
			#print(c.distance())
			s += int(abs(c.distance() - max_dist))
			
		r = random.randint(0, s)
		
# 		print("R=%d" %r)
		
		s = 0
		selection = self.solutions[0]
		
		for c in self.solutions:			
			s += int(abs(c.distance() - max_dist))
			
			if s >= r:
				#print("test R=%d, S=%d D=%d" %(r, s, c.distance()))
				selection = c
				break
			
# 		print("S = %d" %selection.distance())
			
		return selection


class Solution():
	'''
		Classe représentant une solution de chemin entre des villes
		La solution peut muter ou se croiser avec une autre pour produire des enfants
	'''
	# TODO: taille
	DIVISOR_CROSSOVER = 5

	def __init__(self, cities):
		self.cities = cities
		self.divisor = len(cities) // 2
		self._distance = None
		#print(self.divisor)
		
	def randomize(self):
		random.shuffle(self.cities)
		
	def mutate(self, force_mutation=False):
		''' effectue une mutation de la solution en échangeant deux villes dans le chemin '''
		# TODO: taux ?
		if not force_mutation and random.randint(0, 100) >= 10:
			print("notmutate")
			return self
		
		print("mutate")
		
		ind1, ind2 = self.random_index()
		self.cities[ind1], self.cities[ind2] = self.cities[ind2], self.cities[ind1]

		self._distance = None
		
		return self
	
	def clone(self):
		return Solution(list(self.cities))
		
	def random_index(self):
		ind = len(self.cities) - 1
		a, b = 0, 0
		
		while a == b:
			a = random.randint(0, ind)
			b = random.randint(0, ind)
			
		return a, b 
	
	def crossover(self, solution2, force_crossover=False):
		''' effectue un croisement OX entre la solution courante et la solution2, génèrant deux fils '''
		# TODO: taux ?
		if not force_crossover and random.randint(0, 100) >= 50:
			print("notcross")
			return self.clone(), solution2.clone()
			#return None, None
		
		print("cross")
		
		length = len(self.cities)
		ind_max = length - 1
		length_cross = math.floor(ind_max / self.divisor)
		ind_start = random.randint(1, ind_max - length_cross)
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
		''' implémentation du croisement OX entre une solution et le fils généré en partie '''
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
		''' calcule la distance totale du chemin représenté par la solution ''' 
		if self._distance is None:
			distance = 0.0
			
			old_city = self.cities[-1]
			
			for city in self.cities:
				distance += self.distance_euclidean(city, old_city)
				old_city = city
				
			self._distance = distance

		return self._distance
	
	def distance_euclidean(self, city1, city2):
		''' calcule la distance entre 2 villes de la solution '''
		return math.hypot(city1.x - city2.x, city1.y - city2.y)

	def __repr__(self):
		return str(self.cities)
	
	def crossover_greedy(self, solution2):

		fa = True
		fb = True
		
		t = random.choice(self.cities)
		
		x = self.cities.index(t)
		y = solution2.cities.index(t)
		
		g = [t]
		
		n = len(self.cities)
		
		while fa == True or fb == True:
			x = (x - 1) % n
			y = (y + 1) % n
			
			if fa == True:
				if self.cities[x] not in g:
					g.insert(0, self.cities[x])
				else:
					fa = False
					
			if fb == True:
				if solution2.cities[y] not in g:
					g.append(solution2.cities[y])
				else:
					fb = False
					
					
		if len(g) < len(self.cities):
			l = list(self.cities)
			random.shuffle(l)
			
			for c in l:
				if c not in g:
					g.append(c)
		
		return Solution(g)
		

class Parser():
	''' 
		Classe effectuant la lecture d'une liste de villes 
	'''
	
	def __init__(self, path):
		self.path = path
		
		self.cities = []
		
		with open(path) as file:
			
			for line in file:
				name, x, y = line.split()
				self.cities.append(City(name, int(x), int(y)))

class City():
	'''
		Classe représentant une ville, avec son nom et sa position (X,Y)
	'''
	
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
	'''
		Classe gérant l'interface graphique, avec dessin des villes, ajout de villes par clic et résolution du PVC
		Reçoit un objet PVC en paramètres, avec une possible liste de villes chargées depuis un fichier
		Lors de la résolution du PVC, le meilleur chemin reliant les villes est dessiné
	'''
	
	def __init__(self, pvc):		
		''' initialise la GUI, l'affiche, attend l'ajout de villes par l'utilisateur et effectue le calcul du PVC '''
		self.pvc = pvc
		self.display_path = False
		
		screen_x = 500
		screen_y = 500
		
		self.city_color = [255,255,255]
		self.city_radius = 2
		
		self.font_color = [255,255,255]
		
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
		''' dessine les villes dans la GUI et le meilleur chemin calculé lors du calcul PVC '''
		# prévenir le freeze de la GUI
		for event in pygame.event.get():
			if event.type == QUIT:
				exit(0)

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
	'''
		Programme principal exécutable en ligne de commande avec les paramètres suivants:
			DeruazRosser.py [--nogui] [--maxtime s] [filename]
		Parse les paramètres, exécute la résolution du PVC selon les paramètres et affiche les résultats
	'''
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
