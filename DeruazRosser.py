#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Algorithme génétique pour résolution du problème du voyageur de commerce - PVC

Résoud un PVC, soit à partir d'un fichier ou d'une interface graphique avec mise à jour visuelle ou non (gui)
	Recherche un chemin optimisé entre N villes

Fonction de fitness/évaluation: 
	Distance totale du chemin de chaque solution
	
Sélection mise en place:
	Elitisime: sélection de N meilleures solutions selon taille de population, 30% au maximum
	Roulette: sélection pour nouvelle population, donnant plus de probabilité de choix aux solutions courtes
	
Croisement:
	Utilisé: Greedy Subtour Crossover (GSX), issu du document anglais donné en cours
	Aussi développé initialement mais désactivé: OX, issu du document français donné en cours
	Taux plutôt élevé
	
Mutation:
	Echange aléatoire de deux villes dans le chemin
	Taux faible

Réalisé avec python v3.3 et pygame v1.9.2a0

@date: février 2015
@author: vincent.deruaz, mathieu.rosser
'''

import math
import time
import random
import pygame
import argparse
import itertools
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN

def ga_solve(file=None, gui=True, maxtime=0):
	'''
		Résolution d'un PVC
		@param file: 	fichier de villes à charger
		@param gui: 	affiche l'interface graphique
		@param maxtime: temps maximum de calcul
		@return: 		la distance totale calculée, la liste des villes dans l'ordre de passage
	'''
	
	# init villes
	if file is None:
		cities = []
	else:
		cities = Parser(file).cities
	
	# objet de résolution PVC
	pvc = PVC(cities, maxtime)
	
	# affichage ou calcul
	if gui:
		Gui(pvc)
	else:
		pvc.compute()
	
	# résultats
	cities_names = [c.name for c in pvc.ordered_cities]
	return pvc.total_distance, cities_names
	

class PVC():
	''' 
		Classe résolvant un PVC, à partir d'une liste de villes, dans un temps maximum ou jusqu'à stagnation 
		Le temps maximum est géré par chronométrage des traitements
		La stagnation est déterminée en stockant les N derniers meilleurs résultats (distances minimum)
			et en calculant l'écart-type pour ces distances. On s'arrêt si l'écart-type est plus petit qu'un epsylon.
		Résultats en sortie: total_distance, total_time, ordered_cities
	'''
	
	# Facteur du nombre d'évolutions (selon taille) de la population avant d'évaluer la condition de stagnation 
	FACTOR_END_SIZE = 10
	
	# Epsylon de marge pour la condition de stagnation : si l'écart-type est <= EPSYLON, on a une stagnation
	STD_EPSYLON = 1e-10
	
	def __init__(self, cities, maxtime):
		''' initialise la résolution du PVC avec les villes à rejoindre '''
		
		self.cities = cities
		self.maxtime = maxtime
		
		self.total_distance = 0
		self.total_time = 0
		self.ordered_cities = list(self.cities)
		
		self.last_distances = []
		
	def compute(self, gui=None):	
		''' résoud un PVC à partir des données courantes : génération population, évolution, gestion de l'arrêt '''
		
		self.start = time.clock()
		self.population = Population(self.ordered_cities)

		# évolution de la population jusqu'à la fin
		while not self.is_ended():
			# sélection, croisement et mutation de la population
			self.population.update()
			# récupération des résultats courants
			self.ordered_cities = self.population.solutions[0].cities
			self.total_distance = self.population.solutions[0].distance()
			
			# pour condition de fin
			self.last_distances.append(self.total_distance)
			
			# màj GUI
			if gui:
				gui.draw()
					
	def is_ended(self):
		''' vérifie si le calcul est terminé par stagnation ou temps '''
		
		self.total_time = time.clock() - self.start
		
		# arrêt selon temps
		if (self.maxtime is not None and self.maxtime > 0):
			return self.total_time >= self.maxtime
		
		length = len(self.last_distances)
		
		# vérification de la population de fin par stagnation si au moins N derniers calculs
		if length > PVC.FACTOR_END_SIZE * self.population.size:
			# calcul de la moyenne et de l'écart-type avec les N dernières meilleures distances
			mean_dist = sum(self.last_distances) / length
			std_dev = math.sqrt(1 / length * sum([pow(x - mean_dist, 2) for x in self.last_distances]))

			# arrêt par stagnation si epsylon atteint sur l'écart-type
			if std_dev <= PVC.STD_EPSYLON:
				return True
			
			# sinon reset des derniers calculs, on recalcule dans N évolutions
			else:
				self.last_distances = []
		
		return False


		
class Population():
	''' 
		Classe représentant une population de solutions
		La population évolue par sélection, croisement et mutation
		La sélection utilise un certain nombre d'élites (en fonction de la taille de population, 30% au maximum)
		La sélection est faite par la suite avec l'algorithme de roulette (les solutions les + courtes ont + de chance d'être prises)
		Le croisement effectué est le croisement greedy selon un certain taux (cf classe Solution)
		La mutation effectuée est un échange aléatoire de deux villes selon un certain taux (cf classe Solution)
	'''
	
	# Taux d'élites possible, entre 0.0 et 1.0
	ELITE_RATE = 0.3
		
	def __init__(self, cities):
		''' génération de la population initiale aléatoirement '''
		
		self.size = 50 #min(4 * len(cities), 50)	# taille de la population
		basic_solution = Solution(list(cities))	# solution originale
		
		self.solutions = [basic_solution]
		
		# génération des solutions restantes: copie de l'originale et ordonnancement aléatoire
		for _ in range(self.size):
			s = basic_solution.clone()
			s.randomize()
			self.solutions.append(s)
		
		# tri initial
		self.order_by_distance_and_shrink()
						
	def order_by_distance_and_shrink(self):
		''' tri de la population par distance, de la plus courte à la plus longue, et limite sa taille '''
		
		self.solutions.sort(key=Solution.distance)
		
		# limite la taille de la population
		self.solutions = self.solutions[:self.size]
		
	def update(self):
		''' mise à jour de la population par sélection, croisement et mutation '''
		
		# sélection des élites
		elite_rate = Population.ELITE_RATE# min(self.size / 100, Population.ELITE_RATE) #0.3 if self.size >= 30 else 0.2
		elite = max(int(self.size * elite_rate), 1)
				
		new_solutions = self.solutions[:elite]
		
		# création de la nouvelle population par croisement (selon taux) de l'ancienne population
		# la sélection dans l'ancienne population se fait par roulette
		
		used = []
		
		while len(new_solutions) <= self.size:
			a = self.roulette_selection()
			b = self.roulette_selection()
			
# 			if a in used:
# 				print("in = %d" %len(used))
			
			used.append(a)
			used.append(b)
			
			force = a in used or b in used
# 			if force:
# 				print("force")
			
			#child1, child2 = a.crossover_ox(b)
			child1 = a.crossover_greedy(b, force)
			child2 = b.crossover_greedy(a, force)
						
			new_solutions.append(child1)
			new_solutions.append(child2)
			
# 		print("FIN=%d VS %d" %(len(used), len(new_solutions)))
# 		exit()
		# mutation dans la population (selon taux)
		for s in new_solutions:
			s.mutate_swap()

		# mise à jour de la population
		self.solutions = new_solutions
		self.order_by_distance_and_shrink()
	
	def roulette_selection(self):
		''' sélection aléatoire par roulette d'une solution, les solutions les plus courtes ayant le plus de probabilité d'être choisie '''
		
		# distance maximum
# 		max_dist = self.solutions[-1].distance()
		min_dist = self.solutions[0].distance()
		
		# calcul de la somme
		s = 0
		for c in self.solutions:
			#s += int(abs(c.distance() - max_dist))
			s += min_dist / c.distance()
		
# 		print(s)
		# choix nb aléatoire
		#r = random.randint(0, s)
		r = random.uniform(0, s)
# 		print("R=%d" %r)
		
		# recherche de la sélection selon nb aléatoire
		s = 0
		selection = self.solutions[0]
		
		for c in self.solutions:		
			#s += int(abs(c.distance() - max_dist))
			s += min_dist / c.distance()
			
			if s >= r:
# 				print("D=%d" %c.distance())
				selection = c
				break
			
		return selection

	def __repr__(self):
		return str(self.solutions)


class Solution():
	'''
		Classe représentant une solution de chemin entre des villes
		La solution mute et se croise avec une autre pour produire des enfants, selon des taux respectifs
		La mutation échange aléatoirement deux villes dans le chemin
		Le croisement effectue un Greedy Subtour Crossover (GSX), issu du document arob98.pdf
		Le croisement OX (document GA.pdf) a aussi été implémenté dans un premier temps
		La distance calculée de la solution est gardée en mémoire après un calcul (reset en cas de changement, mutation)
	'''
	
	# Taux de mutation en pourcent
	# Plus efficace avec de petits taux, sinon cela créé des instabilités
	MUTATION_RATE = 10
	
	# Taux de croiseement en pourcent
	# Plus efficace avec un grand taux, sinon cela créé de la stagnation
	CROSSOVER_RATE = 75

	def __init__(self, cities):
		''' initialisation de la solution '''
		
		self.cities = cities
		self._distance = None	# distance interne stockée après calcul
				
	def mutate_swap(self):
		''' effectue une mutation de la solution (swap selon taux) en échangeant deux villes dans le chemin '''

		# taux de mutation
		if random.randint(0, 100) >= Solution.MUTATION_RATE:
			return self
		
		old_distance = self.distance()
		
		# échange de 2 villes
		for _ in range(3):
			ind1, ind2 = self.random_index()
			self.cities[ind1], self.cities[ind2] = self.cities[ind2], self.cities[ind1]
			
			self._distance = None
			if self.distance() < old_distance:
				break
			
			else:
				self.cities[ind1], self.cities[ind2] = self.cities[ind2], self.cities[ind1]


		#self._distance = None # reset distance stockée
		
		return self
		
	def crossover_greedy(self, solution2, force=False):
		''' effectue un croisement selon l'algorithme Greedy Subtour Crossover (GSX) et taux '''
		
		# taux de croisement
		if not force and random.randint(0, 100) >= Solution.CROSSOVER_RATE:
			return self.clone()

		fa = True
		fb = True
		
		t = random.choice(self.cities)	# ville
		
		x = self.cities.index(t)
		y = solution2.cities.index(t)
		
		g = [t]		# nouveau chemin de la solution croisée
		
		n = len(self.cities)
		
		# croisement
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
					
		# complétion
		if len(g) < len(self.cities):
			l = list(self.cities)
			random.shuffle(l)
			
			for c in l:
				if c not in g:
					g.append(c)
					
		# solution issue du croisement
		return Solution(g)
	
	def crossover_ox(self, solution2):
		''' effectue un croisement OX entre la solution courante et la solution2, génèrant deux fils '''
		
		# taux
		if random.randint(0, 100) >= Solution.CROSSOVER_RATE:
			return self.clone(), solution2.clone()
				
		length = len(self.cities)
		ind_max = length - 1
		length_cross = math.floor(ind_max / 2)	# longueur de la moitié de longueur de solution
		# indices début/fin du croisement
		ind_start = random.randint(1, ind_max - length_cross)
		ind_stop = ind_start + length_cross - 1
		
		# croisement des enfants pour la partie début->fin
		new_cities1 = [None for _ in self.cities]
		new_cities2 = [None for _ in self.cities]
		
		for i in range(ind_start, ind_stop + 1):
			new_cities1[i] = solution2.cities[i]
			new_cities2[i] = self.cities[i]
			
		# complétion du reste des enfants et solutions
		self._crossover_ox(solution2, new_cities1, ind_stop, length)
		self._crossover_ox(self, new_cities2, ind_stop, length)

		return Solution(new_cities1), Solution(new_cities2)
	
	def _crossover_ox(self, solution, new_cities, ind_stop, length):
		''' implémentation du croisement OX entre une solution et le fils généré en partie '''
		
		j = ind_stop + 1
		for i in range(j, ind_stop + length):
			city = solution.cities[i % length]
			
			if new_cities[j % length] is None and city not in new_cities:
				new_cities[j % length] = city
				j += 1
				
	def clone(self):
		''' copie profonde d'une solution '''
		return Solution(list(self.cities))

	def randomize(self):
		''' réorganisation aléatoire des villes de la solution '''
		random.shuffle(self.cities)

	def distance(self):
		''' calcule la distance totale du chemin représenté par la solution ''' 
		
		# calcul de la distance si non effectué
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
		
	def random_index(self):
		''' retourne deux indices aléatoires dans la liste des villes '''
		
		ind = len(self.cities) - 1
		a, b = 0, 0
		
		while a == b:
			a = random.randint(0, ind)
			b = random.randint(0, ind)
			
		return a, b

	def __repr__(self):
		return str(self.cities)



class Parser():
	''' 
		Classe effectuant la lecture d'une liste de villes 
	'''
	
	def __init__(self, path):
		''' lit le fichier path ligne par ligne et créé les villes avec leurs noms et leurs positions x;y '''
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
		''' création d'une ville avec un nom et une position x;y '''
		self.name = name
		self.x = x
		self.y = y
		
	def pos(self):
		''' retourne la position d'une ville '''
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
		self.display_path = False	# affichage du meilleur chemin
		
		screen_x = 500
		screen_y = 500
		
		self.city_color = [255,255,255]
		self.city_radius = 2
		
		self.title_color = [255, 255, 0]
		
		pygame.init()
		pygame.display.set_mode((screen_x, screen_y))
		pygame.display.set_caption('Voyageur du commerce')
		
		self.screen = pygame.display.get_surface() 
		self.font = pygame.font.Font(None,30)
		self.font_cities = pygame.font.Font(None,18)		

		self.draw()
		
		collecting = True
		
		# entrée à la souris des villes ou attente de lancement
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
		
		# calcul du PVC
		self.display_path = True
		pvc.compute(self)
		
		# attente finale
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
		
		# dessin des villes
		for c in self.pvc.ordered_cities:
			pygame.draw.circle(self.screen, self.city_color, c.pos(), self.city_radius)
			
			label = self.font_cities.render("%s (%i,%i)" % (c.name, c.x, c.y), True, self.city_color)
			label_rect = label.get_rect()
			label_rect.centerx = c.x + label_rect.width / 1.6
			label_rect.centery = c.y
			self.screen.blit(label, label_rect)
		
		# dessin du titre : info sur les villes et le calcul PVC
		text = self.font.render("Nombre: %i Distance: %.3f Temps: %.3f" %(len(self.pvc.ordered_cities), self.pvc.total_distance, self.pvc.total_time), True, self.title_color)
		textRect = text.get_rect()
		self.screen.blit(text, textRect)
			
		# affichage du meilleur chemin calculé
		if self.display_path:
			pygame.draw.lines(self.screen, self.city_color, True, [c.pos() for c in self.pvc.ordered_cities])
			
		pygame.display.flip()

if __name__ == '__main__':
	'''
		Programme principal exécutable en ligne de commande avec les paramètres suivants:
			DeruazRosser.py [--nogui] [--maxtime s] [filename]
		Parse les paramètres, exécute la résolution du PVC selon les paramètres et affiche les résultats
	'''
	
	# paramètres
	parser = argparse.ArgumentParser(description="Problème du voyageur de commerce avec algorithme génétique")
	
	parser.add_argument('--nogui', action="store_true", help="Ne pas afficher l'interface graphique")
	parser.add_argument('--maxtime', type=int, action="store", help="Arrêter la recherche après maxtime secondes")
	parser.add_argument("filename", type=str, default=None, nargs="?", help="Fichier contenant les villes à visiter")

	args = parser.parse_args()
	
	gui = not args.nogui
	maxtime = args.maxtime if args.maxtime is not None else 0
	file = args.filename
	
	print("Résolution du problème du voyageur du commerce - Vincent Déruaz, Mathieu Rosser")
	print("Gui: %d"%gui)
	print("Maxtime: %d"%maxtime)
	print("File: %s" %file)
	print()

	# résolution PVC
	total_distance, cities = ga_solve(file, gui, maxtime)
	
	print("Distance totale:\n\t %d" %total_distance)
	print("Villes à visiter dans l'ordre:\n\t %s" %str(cities))
