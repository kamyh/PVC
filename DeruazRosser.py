#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

@author: vincent.deruaz, mathieu.rosser
'''

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
		
	return pvc.total_distance, pvc.ordered_cities
	
class PVC():
	def __init__(self, cities, maxtime):
		self.cities = cities
		self.maxtime = maxtime
		
		self.total_distance = 0
		self.ordered_cities = []
		
	def compute(self):
		pass

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

class Gui():
	
	def __init__(self, pvc):
	
		import pygame
		from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN, K_ESCAPE
		
		cities = pvc.cities
		
		screen_x = 500
		screen_y = 500
		
		city_color = [255,255,255] # blue
		city_radius = 2
		
		font_color = [255,255,255] # white
		
		pygame.init() 
		window = pygame.display.set_mode((screen_x, screen_y)) 
		pygame.display.set_caption('Voyageur du commerce') 
		screen = pygame.display.get_surface() 
		font = pygame.font.Font(None,30)
		font_cities = pygame.font.Font(None,18)
		
		def draw(cities):
				screen.fill(0)
				for c in cities: 
					pygame.draw.circle(screen,city_color,c.pos(),city_radius)
					
					label = font_cities.render("%s (%i,%i)" % (c.name, c.x, c.y), True, font_color)
					label_rect = label.get_rect()
					label_rect.centerx = c.x + label_rect.width / 1.6
					label_rect.centery = c.y
					screen.blit(label, label_rect)
					
				text = font.render("Nombre: %i" % len(cities), True, font_color)
				textRect = text.get_rect()
				screen.blit(text, textRect)
				pygame.display.flip()
		

		draw(cities)
		
		collecting = True
		
		while collecting:
			for event in pygame.event.get():
				if event.type == QUIT:
					return
				elif event.type == KEYDOWN and event.key == K_RETURN:
					collecting = False
				elif event.type == MOUSEBUTTONDOWN:
					pos = pygame.mouse.get_pos()
					cities.append(City("v%i" % len(cities), pos[0], pos[1]))
					draw(cities)
					
		screen.fill(0)
		pygame.draw.lines(screen,city_color,True, [c.pos() for c in cities])
		text = font.render("Un chemin, pas le meilleur!", True, font_color)
		textRect = text.get_rect()
		screen.blit(text, textRect)
		pygame.display.flip()
		
		while True:
			event = pygame.event.wait()
			if event.type == KEYDOWN: break



if __name__ == '__main__':
	
	import argparse

	parser = argparse.ArgumentParser(description="Problème du voyageur de commerce avec algorithme génétique")
	
	parser.add_argument('--nogui', action="store_true", help="Ne pas afficher l'interface graphique")
	parser.add_argument('--maxtime', type=int, action="store", help="Arrêter la recherche après maxtime secondes")
	parser.add_argument("filename", type=str, default=None, nargs="?", help="Fichier contenant les villes à visiter")

	args = parser.parse_args()
	
	gui = not args.nogui
	maxtime = args.maxtime
	file = args.filename
	
	print("Gui: %d"%gui)
	print("Maxtime: %d"%maxtime)
	print("File: %s" %file)
	print()

	total_distance, cities = ga_solve(file, gui, maxtime)
	
	print("Distance totale:\n\t %d" %total_distance)
	print("Villes à visiter dans l'ordre:\n\t %s" %str(cities))
