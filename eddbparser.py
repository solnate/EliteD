  
from  urllib.request import urlopen  
import json
import time
from time import time
import copy
import math
import csv
import requests
from bs4 import BeautifulSoup
import re
from urllib.request import HTTPError
import datetime
from multiprocessing import Process, current_process
import collections
from prettytable import PrettyTable
import multiprocessing
import os

def download_files():

    if not os.path.exists('eddb/commodities.json'):
        print("Downloading commos...")
        url = urlopen("https://eddb.io/archive/v6/commodities.json")    
        f = url.read()
        open("eddb/commodities.json","wb").write(f) 

    if not os.path.exists('eddb/systems_populated.json'):
        print("Downloading systems...")
        url = urlopen("https://eddb.io/archive/v6/systems_populated.json")    
        f = url.read()
        open("eddb/systems_populated.json","wb").write(f)

    if not os.path.exists('eddb/stations.json'):
        print("Downloading stations...")
        url = urlopen("https://eddb.io/archive/v6/stations.json")    
        f = url.read()
        open("eddb/stations.json","wb").write(f)

    if not os.path.exists('eddb/listings.csv'):
        print("Downloading prices...")
        url = urlopen("https://eddb.io/archive/v6/listings.csv")    
        f = url.read()
        open("eddb/listings.csv","wb").write(f)

def read_file(filename):
    with open(filename, encoding='utf-8') as input_file:
        text = input_file.read()
    return text

def download(system_id):
    url = 'https://eddb.io/station/market/%d' % (system_id)
    r = requests.get(url)
    with open('download/temp{}.html'.format(system_id), 'w', encoding='utf-8') as output_file:
        output_file.write(r.text)

def check(system_id, commo_id):
    page_link = 'https://eddb.io/station/market/%d' % (system_id)
    page_response = requests.get(page_link, timeout=5)
    soup = BeautifulSoup(page_response.content, "html.parser")
    _list = soup.find('div', {'class': 'table-wrap'})
    items = _list.find_all('tr')
    for item in items:       
        try:
            _link = item.find('a').get('href')
            if _link == '/commodity/{}'.format(commo_id):
                _price = item.find('span', {'class': 'number better', 'class': 'number worse', 'class': 'number'})
                price = _price.text.replace(",", "")
                break
            else:
                price = 0
        except AttributeError :
            continue
    return int(price)

def multiproc(flag, stations):
    if flag == '1':
        with open('eddb/result/res.json', 'r', encoding='utf-8') as f:
            read_systems = json.loads(f.read())

        for station in stations:
            id = str(stations[station].ret_id())
            for item in read_systems[id]['prices']:
                price = Price(
                    id, item, 
                    read_systems[id]['prices'][item]['supply'], 
                    read_systems[id]['prices'][item]['buy price'], 
                    read_systems[id]['prices'][item]['sell price']
                )  
                stations[station].add_price(price, item)

        return 0      

    now = datetime.datetime.now()
    print("Started at", now.hour, ":", now.minute)

    tasks = multiprocessing.JoinableQueue()
    results = multiprocessing.Queue()

    num_consumers = 8
    print ('Creating %d consumers' % num_consumers)
    consumers = [ Consumer(tasks, results, flag)
                  for i in range(num_consumers) ]
    for w in consumers:
        w.start()
    
    num_jobs = len(stations)
    nums = num_jobs
     
    for item in stations:
        if nums:
            tasks.put(Task(stations[item], market_commos))

        else:
            break

        nums -= 1

    for i in range(num_consumers):
        tasks.put(None)

    tasks.join()
    
    for i in range(num_jobs):
        result = results.get()
        stations[result.ret_id()] = result

    json_stations = dict()
    for station in stations:
        json_stations[station] = stations[station].ret_json()

    now = int(time())
    dir = f'eddb/result/{now}'
    if not os.path.isdir(dir):
        os.makedirs(dir)

    with open(f'{dir}/res.json', 'w', encoding='utf-8') as f:
        json.dump(json_stations, f, ensure_ascii=False, indent=4)

    with open(f'eddb/result/res.json', 'w', encoding='utf-8') as f:
        json.dump(json_stations, f, ensure_ascii=False, indent=4)

    now = datetime.datetime.now()
    print("ended at", now.hour, ":", now.minute)

def commo_brute(f_station_id, s_station_id, price, stations, table, dist, cur_dist):      
    min_supply, min_profit = [700, 20000]       
    sup = stations[f_station_id].ret_prices()[price].ret_supply()
    if (stations[f_station_id].ret_prices()[price].ret_buy_price() > 0 and sup > min_supply) and price in stations[s_station_id].ret_prices():
        profit_buy = (stations[s_station_id].ret_prices()[price].ret_sell_price() - stations[f_station_id].ret_prices()[price].ret_buy_price())
        if profit_buy > min_profit: 
            buy_system_id = stations[f_station_id].ret_id()
            buy_price = stations[f_station_id].ret_prices()[price].ret_buy_price()
            buy_dist = stations[f_station_id].ret_name()
            sell_system_id = stations[s_station_id].ret_id()
            sell_price = stations[s_station_id].ret_prices()[price].ret_sell_price()
            #checked = check(stations[s_station_id].ret_id(), stations[s_station_id].ret_prices()[price].ret_commmodity_id())
            sell_dist = stations[s_station_id].ret_name()
            commodity_id = stations[f_station_id].ret_prices()[price].ret_commmodity_id()
            table.add_row([profit_buy, buy_system_id, buy_price, buy_dist, sell_system_id, sell_price, sell_dist, commodity_id, sup, dist, cur_dist])

def count(name, stations, coor):
    print('Process %s starting...' % name)
    counting_buy, counting_sell, max_dist, av = [0, 0, 20, 0]
    table = PrettyTable()
    table.field_names = ["Profit", "Buy Id", "Buy price", "Buy name", "Sell Id", "Sell price", "Sell name", "Comm. Id", "Supply", "ly", "to me"]
    table.align["Buy Id"] = "l"
    table.align["Buy price"] = "l"
    table.align["Buy ls"] = "l"
    table.align["Sell Id"] = "l"
    table.align["Sell ls"] = "l"
    table.align["Supply"] = "l"
    table.align["ly"] = "l"
    for f_station_id in stations:
        counting_buy = counting_buy + 1
        print(counting_buy, "\r", end = "")
        for s_station_id in stations:
            if s_station_id > f_station_id:
                dist = math.sqrt(
                    ((stations[s_station_id].ret_x() - stations[f_station_id].ret_x()) ** 2) + 
                    ((stations[s_station_id].ret_y() - stations[f_station_id].ret_y()) ** 2) + 
                    ((stations[s_station_id].ret_z() - stations[f_station_id].ret_z()) ** 2)
                )
                dist = round(dist, 2)

                cur_dist = math.sqrt(
                    ((coor[0] - stations[f_station_id].ret_x()) ** 2) + 
                    ((coor[1] - stations[f_station_id].ret_y()) ** 2) + 
                    ((coor[2] - stations[f_station_id].ret_z()) ** 2)
                    )
                cur_dist = round(cur_dist, 2)

                if dist < max_dist:
                    prices_ = stations[f_station_id].ret_prices()
                    _prices = stations[s_station_id].ret_prices()
                    for price_ in prices_:
                        counting_sell += 1 
                        commo_brute(f_station_id, s_station_id, price_, stations, table, dist, cur_dist)
                    for _price in _prices:
                        counting_sell += 1
                        commo_brute(s_station_id, f_station_id, _price, stations, table, dist, cur_dist)
    print(table)
    print("Systems checked:", counting_buy, "to", counting_sell)
    now = datetime.datetime.now()
    print(name, "ended at", now.hour, ":", now.minute) 

class System:
    def __init__(self, name, x, y, z):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.stations = dict()

    def ret_name(self):
        return self.name
    
    def ret_x(self):
        return self.x

    def ret_y(self):
        return self.y

    def ret_z(self):
        return self.z

    def add_stations(self, station, station_id):
        self.stations[station_id] = station

    def system_add_price(self, station_id, price, commodity_id):
        self.stations[station_id].add_price(price, commodity_id)

    def ret_stations(self):
        return self.stations

    def ret_count_stations(self):
        return len(self.stations)
    
    def ret_station_by_id(self, station_id):
        return self.stations[int(station_id)]

class Station:
    def __init__(self, name, id, system_id, dist, x, y, z):
        self.name = name
        self.id = id
        self.system_id = system_id
        self.dist = dist
        self.prices = dict()
        self.flag = 0
        self.x = x
        self.y = y
        self.z = z

    def ret_json(self):
        return {
            'name': self.name,
            'id': self.id,
            'system_id': self.system_id,
            'dist': self.dist,
            'prices': self.ret_json_prices(),
            'x': self.x,
            'y': self.y,
            'z': self.z
        }

    def __str__(self):
        return str(self.name) + str(self.id)

    def ret_name(self):
        return self.name 

    def ret_id(self):
        return self.id 

    def ret_system_id(self):
        return self.system_id 
    
    def ret_prices(self):
        return self.prices

    def ret_json_prices(self):
        json_prices = dict()
        for item in self.prices:
            print(item, "\r", end = "")
            json_prices[item] = self.prices[item].ret_json()

        return json_prices
    
    def add_price(self, price, commodity_id):
        self.prices[int(commodity_id)] = price
        self.flag = 1

    def ret_dist(self):
        return self.dist
    
    def is_price(self):
        return self.flag

    def ret_x(self):
        return self.x

    def ret_y(self):
        return self.y

    def ret_z(self):
        return self.z

class Price:
    def __init__(self, station_id, commodity_id, supply, buy_price, sell_price):
        self.station_id = int(station_id)
        self.commodity_id = int(commodity_id)
        self.supply = int(supply)
        self.buy_price = int(buy_price)
        self.sell_price = int(sell_price)

    def ret_station_id(self):
        return self.station_id 

    def ret_commmodity_id(self):
        return self.commodity_id 

    def ret_buy_price(self):
        return self.buy_price 

    def ret_sell_price(self):
        return self.sell_price

    def ret_supply(self):
        return self.supply 

    def ret_json(self):
        return {
            'supply': self.supply,
            'buy price': self.buy_price,
            'sell price': self.sell_price
        }

class Consumer(multiprocessing.Process):
    
    def __init__(self, task_queue, result_queue, flag):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.numbs = 0

    def run(self):
        proc_name = self.name
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                # print ('%s: Exiting' % proc_name)
                self.task_queue.task_done()
                break
            self.numbs += 1
            print ('%s: %s' % (proc_name, self.numbs), "\r", end = "")
            answer = next_task()
            self.task_queue.task_done()
            self.result_queue.put(answer)
        return

class Task(object):
    def __init__(self, station, market_commos):
        self.station = station
        self.market_commos = market_commos

    def __call__(self):
        page_link = 'https://eddb.io/station/market/%d' % (self.station.id)
        page_response = requests.get(page_link, timeout=5)
        soup = BeautifulSoup(page_response.content, "html.parser")
        _list = soup.find('div', {'class': 'table-wrap'})
        try:
            items = _list.find_all('tr')
            for item in items:
                try:       
                    _link = item.find('a').get('href')
                    _name = item.find('td')
                    _prices = item.find_all('span', {'class': 'number better', 'class': 'number worse', 'class': 'number'})
                    if self.market_commos[int(_link[11:])]:
                        if len(_prices) == 5:
                            price = Price(self.station.id, _link[11:], _prices[4].text.replace(",", ""), _prices[1].text.replace(",", ""), _prices[0].text.replace(",", ""))       
                        elif len(_prices) == 4:
                            price = Price(self.station.id, _link[11:], _prices[3].text.replace(",", ""), 0, _prices[0].text.replace(",", "")) 
                        self.station.add_price(price, int(_link[11:]))     
                except AttributeError:
                    continue
        except AttributeError:
            pass
        return self.station

if __name__ == '__main__':
    download_files()

    print("Opening systems...")
    with open('eddb/systems_populated.json', 'r') as f_systems:
        systems_data = json.load(f_systems)

    #--------
    print("Opening stations...")
    with open('eddb/stations.json', 'r') as f_stations:
        stations_data = json.load(f_stations)

    #--------
    print("Opening commos...")
    with open('eddb/commodities.json', 'r') as f_commos:
        commos_data = json.load(f_commos)

    #--------
    print("Opening prices...")
    listings = open('eddb/listings.csv', 'r')
    reader_prices = csv.DictReader(listings)

    print("Parsing started--->")
    systems = dict()
    stations = dict()
#---------------------------------------------------------------------------------------   
    print("Parsing systems...")
    systems_data_iter = iter(systems_data)
    for item in systems_data_iter:
        system = System(item["name"], item["x"], item["y"], item["z"])
        systems[item["id"]] = system

    print("Known systems: ", len(systems))
#---------------------------------------------------------------------------------------
    print("Parsing stations...")
    fleet_carriers, errors, another, too_dist, planetary = [0, 0, 0, 0, 0]
    error_id = []
    stations_data_iter = iter(stations_data)
    for item in stations_data_iter: 
        try:
            if item["type"] == "Fleet Carrier":
                fleet_carriers += 1

            elif item["is_planetary"] == True:
                planetary += 1

            elif item["distance_to_star"] > 1500:
                too_dist += 1

            elif item["max_landing_pad_size"] == "L":
                x = systems[item["system_id"]].ret_x()
                y = systems[item["system_id"]].ret_y()
                z = systems[item["system_id"]].ret_z()
                station = Station(item["name"], item["id"], item["system_id"], int(item["distance_to_star"]), x, y, z)
                stations[item["id"]] = station
                    
            else:
                another += 1

        except TypeError:
            errors += 1
            error_id.append(item["id"])
        
    print("Not enough information for", errors, "systems") 
    #print(error_id)
    print("Planetary: ", planetary)
    print("Known carriers: ", fleet_carriers)
    print("Too dist: ", too_dist)
    print("Another: ", another)
    print("Known stations(L): ", len(stations))
#--------------------------------------------------------------------------------------- 
    market_commos = {}
    market_commos_data_iter = iter(commos_data)
    for item in market_commos_data_iter:
        if item["min_buy_price"] != None and item["max_sell_price"] != None:
            market_commos[item["id"]] = 1
        else:
            market_commos[item["id"]] = 0 
#--------------------------------------------------------------------------------------- 
    multiproc('1', stations)
#---------------------------------------------------------------------------------------
    # print(stations[4107].ret_json_prices())
    my_id = input('Your station: ')
    now = datetime.datetime.now()
    print("Started at", now.hour, ":", now.minute)

    tempst = stations.copy()
    stations.clear()
    for k in sorted(tempst.keys()):
        stations[k] = tempst[k]

    res1 = dict(list(stations.items())[len(stations)//2:])
    res2 = dict(list(stations.items())[:len(stations)//2])

    coor = [systems[int(my_id)].ret_x(), systems[int(my_id)].ret_y(), systems[int(my_id)].ret_z()]

    process1 = Process(target=count, args=("A", res1, coor))
    process2 = Process(target=count, args=("B", res2, coor))

    process1.start()
    process2.start()

    process1.join()
    process2.join()
    
