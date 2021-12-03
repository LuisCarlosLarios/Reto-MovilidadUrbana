# **21/11/2021**

# * Angel Luna                        A01177358
# * Jesús David Guajardo Ovalle       A01283614
# * Sebastián Fernández del Valle     A01720716 
# * Luis Carlos Larios Cota           A00826904

# !pip install mesa

from mesa import Agent, Model 
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

# mathplotlib lo usamos para graficar/visualizar como evoluciona el autómata celular.
# %matplotlib inline
# import seaborn as sns
# import matplotlib
# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
# plt.rcParams["animation.html"] = "jshtml"
# matplotlib.rcParams['animation.embed_limit'] = 2**128

import numpy as np
import pandas as pd

import time
import datetime
import random

def get_grid(model):
  '''
  Esta es una función auxiliar que nos permite guardar el grid para cada uno de los agentes.
  '''
  grid = np.zeros((model.grid.width, model.grid.height))
  for cell in model.grid.coord_iter():
    cell_content, x, y = cell
    for obj in cell_content:
      if isinstance(obj, Carros):
        grid[x][y] = 1
      elif isinstance(obj, Celda):
        if (obj.estado == 0):
          grid[x][y] = 9
        else:
          grid[x][y] = 8
      elif isinstance(obj, Semaforo):
        if (obj.color == 5):
          grid[x][y] = 2
        elif (obj.color == 6):
          grid[x][y] = 3
        else:
          grid[x][y] = 4
  return grid

class Carros(Agent):
  '''
  '''
  def __init__(self, unique_id, model, dir, destino):
    super().__init__(unique_id, model)
    self.sig_pos = None
    self.dir = dir
  # 1 = Derecha
  # 2 = Abajo
    self.destino = destino
    self.movimientos = 0
    self.tipo = 'Carro'

  def step(self):
    vecinos = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=True)
    vecinos2 = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False)
    
    vecinoDerecha = vecinos[3]
    vecinoDerechaObj = vecinos2[-2]

    vecinoAbajo = vecinos[-1]
    vecinoAbajoObj = vecinos2[-1]

    check = 1
    # 0 = Alto
    # 1 = Pasa

    if (isinstance(vecinoDerechaObj, Semaforo) and self.dir == 1):
      vecinos3 = vecinoDerechaObj.model.grid.get_neighbors(vecinoDerechaObj.pos, moore=True, include_center=False)
      otroSemaforo = vecinos3[3]

      if vecinoDerechaObj.color == 7:
        if vecinoDerechaObj.ticks == 0:
          vecinoDerechaObj.color = 6
          otroSemaforo.color = 7
          otroSemaforo.ticks = 5
          check = 0
        else:
          #print('Rojo')
          check = 0
      elif vecinoDerechaObj.color == 5:
        #print('Amarillo')
        vecinoDerechaObj.color = 6
        otroSemaforo.color = 7
        otroSemaforo.ticks = 5
        check = 0

    if (isinstance(vecinoAbajoObj, Semaforo) and self.dir == 0):
      vecinos3 = vecinoAbajoObj.model.grid.get_neighbors(vecinoAbajoObj.pos, moore=True, include_center=False)
      otroSemaforo = vecinos3[7]

      if vecinoAbajoObj.color == 7:
        if vecinoAbajoObj.ticks == 0:
          vecinoAbajoObj.color = 6
          otroSemaforo.color = 7
          otroSemaforo.ticks = 5
          check = 0
        else:
          #print('Rojo')
          check = 0
      elif vecinoAbajoObj.color == 5:
        #print('Amarillo')
        vecinoAbajoObj.color = 6
        otroSemaforo.color = 7
        otroSemaforo.ticks = 5
        check = 0

    # maquina de estados
    if (self.dir == 1 and check == 1): 
      self.sig_pos = vecinoDerecha
    elif (self.dir == 0 and check == 1):
      self.sig_pos = vecinoAbajo
    else:
      self.sig_pos = self.pos
    # termina maquina de estados


  def advance(self):
    '''
    Define el nuevo estado calculado del método step.
    '''
    if (self.sig_pos == (self.destino, int(self.destino/2))): 
      self.sig_pos = (1, int(self.destino/2))
    if (self.sig_pos == (int(self.destino/2), self.destino)):
      self.sig_pos = (int(self.destino/2), 1)

    if self.pos != self.sig_pos:
      self.movimientos += 1
    self.model.grid.move_agent(self, self.sig_pos)


class Celda(Agent):
  # 1 = Calle
  # 0 = No calle
  def __init__(self, unique_id, model, estado):
    super().__init__(unique_id, model)
    self.pos = unique_id
    self.estado = estado
    self.tipo = 'Celda'


class Semaforo(Agent):
  # 5 = Amarillo
  # 6 = Verde
  # 7 = Rojo
  def __init__(self, unique_id, model, color, x, y, ticks):
    super().__init__(unique_id, model)
    self.pos = unique_id
    self.color = color
    self.x = x
    self.y = y
    self.ticks = ticks
    self.tipo = 'Semaforo'

  def step(self):
    vecinos = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)

    SemaforoAbajo = vecinos[3]
    if isinstance(SemaforoAbajo, Semaforo):
      if (self.color == 7 and self.ticks == 0 and SemaforoAbajo.color == 6):
        self.color = 5
        SemaforoAbajo.color = 5

    SemaforoDerecha = vecinos[7]
    if isinstance(SemaforoDerecha, Semaforo):
      if (self.color == 7 and self.ticks == 0 and SemaforoDerecha.color == 6):
        self.color = 5
        SemaforoDerecha.color = 5

    if (self.ticks > 0):
      self.ticks = self.ticks - 1

class Interseccion(Model):
  '''
    Define el modelo del programa.
  '''
  def __init__(self, M, N, num_agentes):
    self.num_agentes = num_agentes
    self.grid = MultiGrid(M, N, False)
    self.schedule = SimultaneousActivation(self)
    # SE DEFINE LOS MOVIMENTOS MAXIMOS DEL PROGRAMA
    self.movimientosMaximo = 100

    # Celdas
    num_calles = int(M+N-1)
    for (content, x, y) in self.grid.coord_iter():
      if (x==int(M/2) or y==int(N/2) and num_calles>0):
        a = Celda((x,y), self, 1)
        num_calles -= 1
      else:
        a = Celda((x,y), self, 0)
      self.grid.place_agent(a, (x, y))
      self.schedule.add(a)

    # Carros
    switch = 1
    for id in range(num_agentes):
      if (switch==1):
        r = Carros(id, self, 1, M-1)
        self.grid.place_agent(r, (int(M/2), 2))
        switch = 0
      else:
        r = Carros(id, self, 0, N-1)
        self.grid.place_agent(r, (1, int(N/2)))
        switch = 1
      self.schedule.add(r)

    # Semaforo
    x = int(M/2-1)
    y = int(N/2)
    s = Semaforo(100, self, 5, int(M/2), int(N/2-1), 0)
    self.grid.place_agent(s, (x, y))
    self.schedule.add(s)

    x = int(M/2)
    y = int(N/2-1)
    s = Semaforo(200, self, 5, int(M/2-1), int(N/2), 0)
    self.grid.place_agent(s, (x, y))
    self.schedule.add(s)
      
    self.datacollector = DataCollector(
      model_reporters={'Grid': get_grid},
      agent_reporters={'Id': lambda a: getattr(a, 'unique_id', None),
                       'Movimientos': lambda a: getattr(a, 'movimientos', None),
                       'Posicion': lambda a: getattr(a, 'sig_pos', None),
                       'Tipo': lambda a: getattr(a, 'tipo', None),
                       'Color': lambda a: getattr(a, 'color', None)}
    )
    
  def step(self):
    '''
        En cada paso el colector tomará la información que se definió y almacenará el grid para luego graficarlo.
    '''
    self.datacollector.collect(self)
    self.schedule.step()

