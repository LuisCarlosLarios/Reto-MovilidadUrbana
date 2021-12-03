# **21/11/2021**

# * Angel Luna                        A01177358
# * Jesús David Guajardo Ovalle       A01283614
# * Sebastián Fernández del Valle     A01720716 
# * Luis Carlos Larios Cota           A00826904

from agentes import Interseccion
import time
import datetime

# Install pyngrok to propagate the http server
# pip install pyngrok --quiet

# Load the required packages
from pyngrok import ngrok
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import os
import numpy as np

# MAS module, for example, MESA
from agentes import Interseccion

# Start ngrok
ngrok.install_ngrok()
# Terminate open tunnels if exist
ngrok.kill()
# Open an HTTPs tunnel on port 8585 for http://localhost:8585
port = os.environ.get("PORT", 8585)
server_address = ("", port)
public_url = ngrok.connect(port="8585", proto="http", options={"bind_tls": True})
print("\n" + "#" * 94)
print(f"## Tracking URL: {public_url} ##")
print("#" * 94, end="\n\n")
ngrok.kill()

############################### MESA ###############################
M = 15 #DEBEN SER IGUALES E IMPARES M Y N
N = 15 #DEBEN SER IGUALES E IMPARES M Y N
num_agentes = 2 #NO MOVER
tiempo_maximo = 0.04

model = Interseccion(M, N, num_agentes)
############################### MESA ###############################

# The way how agents are updated (per step/iteration)
def updateFeatures():
    features = []
    # SE DETIENE DEPENEDIENDO DE LOS MOVIMIENTOS Y NO DEL TIMEPO PORQUE SI NO SE ACABARIA MUY RAPIDO.
    start_time = time.time()

    if model.movimientosMaximo != 0:
        model.step()
        print(model.datacollector.get_model_vars_dataframe().to_string())
        features = model.datacollector.get_agent_vars_dataframe()
        model.movimientosMaximo = model.movimientosMaximo - 1
    else:
        features = None

    return features

# Post the information in `features` for each iteration
def featuresToJSON(info_list):
    # info_list SOLO CONTIENE LOS ULTIMO CUATRO ELEMENTOS DEL DATA FRAME.

    #import pdb; pdb.set_trace()
    featureDICT = []
    for index, row in info_list.iterrows():
        # SE OBTIENE SOLAMENTE CARROS Y SEMAFOROS YA QUE ESTO SON LOS QUE CAMBIAN DE ESTADO O POSICION.
        if row.Tipo == "Carro" or row.Tipo == "Semaforo":
            # SE OBTIENE EL MOVIMIENOT DEL CARRO Y EL COLOR DEL SEMAFORO.
            feature = {
                "id" : row.Id,
                "movimientos" : row.Movimientos,
                "posicion" : row.Posicion,
                "tipo" : row.Tipo,
                "color" : row.Color
            }
            featureDICT.append(feature)
    return json.dumps(featureDICT)

# This is the server. It controls the simulation.
# Server run (do not change it)
class Server(BaseHTTPRequestHandler):
    
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", 
                     str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])

        #post_data = self.rfile.read(content_length)
        post_data = json.loads(self.rfile.read(content_length))
        
        # If you have issues with the encoder, toggle the following lines: 
        #logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     #str(self.path), str(self.headers), post_data.decode('utf-8'))
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), json.dumps(post_data))

        # Here, magick happens 
        # --------------------       
        features = updateFeatures()
        #print(features)

        self._set_response()
        
        # SOLO SE OBTIENEN LOS ULTIMO CUATRO ELEMENTOS.
        resp = "{\"data\":" + featuresToJSON(features.iloc[-4:]) + "}"
        #print(resp)

        self.wfile.write(resp.encode('utf-8'))

# Server run (do not change it)
def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    public_url = ngrok.connect(port).public_url
    logging.info("ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}\"".format(
        public_url, port))

    logging.info("Starting httpd...\n") # HTTPD is HTTP Daemon!
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:   # CTRL + C stops the server
        pass

    httpd.server_close()
    logging.info("Stopping httpd...\n")

run(HTTPServer, Server)

