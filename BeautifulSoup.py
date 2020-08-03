from  urllib.request import urlopen  
import json
import time
import copy
import math
import csv
import requests
from bs4 import BeautifulSoup
import re
from urllib.request import HTTPError
import datetime
from multiprocessing import Process
import collections
from prettytable import PrettyTable
import multiprocessing

commos = {}
invert_commos = {}

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

def commo_brute(f_station_id, s_station_id, price, stations, table, dist):      
    min_supply, min_profit = [700, 20000]       
    sup = stations[f_station_id].ret_prices()[price].ret_supply()
    if (stations[f_station_id].ret_prices()[price].ret_buy_price() > 0 and sup > min_supply) and price in stations[s_station_id].ret_prices():
        profit_buy = (stations[s_station_id].ret_prices()[price].ret_sell_price() - stations[f_station_id].ret_prices()[price].ret_buy_price())
        if profit_buy > min_profit: 
            buy_system_id = stations[f_station_id].ret_id()
            buy_price = stations[f_station_id].ret_prices()[price].ret_buy_price()
            buy_dist = stations[f_station_id].ret_dist()
            sell_system_id = stations[s_station_id].ret_id()
            sell_price = stations[s_station_id].ret_prices()[price].ret_sell_price()
            #checked = check(stations[s_station_id].ret_id(), stations[s_station_id].ret_prices()[price].ret_commmodity_id())
            checked = 0
            sell_dist = stations[s_station_id].ret_dist()
            commodity_id = stations[f_station_id].ret_prices()[price].ret_commmodity_id()
            table.add_row([profit_buy, buy_system_id, buy_price, buy_dist, sell_system_id, sell_price, checked, sell_dist, commodity_id, sup, dist])

def count(name, stations, start, end):
    print('Process %s starting...' % name)
    counting_buy, counting_sell, max_dist, av = [0, 0, 20, 0]
    table = PrettyTable()
    table.field_names = ["Profit", "Buy Id", "Buy price", "Buy ls", "Sell Id", "Sell price", "Checked", "Sell ls", "Comm. Id", "Supply", "ly"]
    table.align["Buy Id"] = "l"
    table.align["Buy price"] = "l"
    table.align["Buy ls"] = "l"
    table.align["Sell Id"] = "l"
    table.align["Sell ls"] = "l"
    table.align["Supply"] = "l"
    table.align["ly"] = "l"
    for f_station_id in stations:
        if f_station_id > start and f_station_id <= end:
            counting_buy = counting_buy + 1
            print(counting_buy, "\r", end = "")
            for s_station_id in stations:
                if s_station_id > f_station_id:
                    dist = math.sqrt(((stations[s_station_id].ret_x() - stations[f_station_id].ret_x()) ** 2) + ((stations[s_station_id].ret_y() - stations[f_station_id].ret_y()) ** 2) + ((stations[s_station_id].ret_z() - stations[f_station_id].ret_z()) ** 2))
                    dist = round(dist, 2)
                    if dist < max_dist:
                        prices_ = stations[f_station_id].ret_prices()
                        _prices = stations[s_station_id].ret_prices()
                        for price_ in prices_:
                            counting_sell += 1 
                            commo_brute(f_station_id, s_station_id, price_, stations, table, dist)
                        for _price in _prices:
                            counting_sell += 1
                            commo_brute(s_station_id, f_station_id, _price, stations, table, dist)
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

class Consumer(multiprocessing.Process):
    
    def __init__(self, task_queue, result_queue):
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
                print ('%s: Exiting' % proc_name)
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
        errors, price_count = [0, 0]
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
                        price_count += 1    
                except AttributeError:
                    continue
        except AttributeError:
            errors += 1
        return self.station

if __name__ == '__main__':
    #--------
    #print("Downloading commos...")
    #url = urlopen("https://eddb.io/archive/v6/commodities.json")    
    #f = url.read()
    #open("eddb/commodities.json","wb").write(f) 

    #--------
    #print("Downloading systems...")
    #url = urlopen("https://eddb.io/archive/v6/systems_populated.json")    
    #f = url.read()
    #open("eddb/systems_populated.json","wb").write(f)

    #--------
    #print("Downloading stations...")
    #url = urlopen("https://eddb.io/archive/v6/stations.json")    
    #f = url.read()
    #open("eddb/stations.json","wb").write(f)

    #--------
    #print("Downloading prices...")
    #url = urlopen("https://eddb.io/archive/v6/listings.csv")    
    #f = url.read()
    #open("eddb/listings.csv","wb").write(f)

    #--------
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

    print("Parsing systems...")
    systems_data_iter = iter(systems_data)
    for item in systems_data_iter:
        system = System(item["name"], item["x"], item["y"], item["z"])
        systems[item["id"]] = system
    print("Known systems: ", len(systems))

    #commos_data_iter = iter(commos_data)
    #for item in commos_data_iter:
    #    commos[item["name"]] = item["id"]
    #invert_commos_data_iter = iter(commos_data)
    #for item in invert_commos_data_iter:
    #    invert_commos[item["id"]] = item["name"]

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
            elif item["distance_to_star"] > 2000:
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

    market_commos = {}
    market_commos_data_iter = iter(commos_data)
    for item in market_commos_data_iter:
        if item["min_buy_price"] != None and item["max_sell_price"] != None:
            market_commos[item["id"]] = 1
        else:
            market_commos[item["id"]] = 0 

#----------------------------------------------------------------------------------
    now = datetime.datetime.now()
    print("Started at", now.hour, ":", now.minute)
   # Establish communication queues
    tasks = multiprocessing.JoinableQueue()
    results = multiprocessing.Queue()

    # Start consumers
    num_consumers = 8
    print ('Creating %d consumers' % num_consumers)
    consumers = [ Consumer(tasks, results)
                  for i in range(num_consumers) ]
    for w in consumers:
        w.start()
    
    # Enqueue jobs
    num_jobs = len(stations)
    nums = num_jobs
    for item in stations:
        if nums:
            tasks.put(Task(stations[item], market_commos))
            nums -= 1
        else:
            break
    
    # Add a poison pill for each consumer
    for i in range(num_consumers):
        tasks.put(None)

    # Wait for all of the tasks to finish
    tasks.join()
    
    stations.clear()
    # Start printing results
    for i in range(num_jobs):
        result = results.get()
        stations[i] = result

#    for item in stations:
#        print ('Result:', item, stations[item].name) 

    now = datetime.datetime.now()
    print("ended at", now.hour, ":", now.minute)

#----------------------------------------------------------------------------------
    now = datetime.datetime.now()
    print("Started at", now.hour, ":", now.minute)

    [end] = collections.deque(stations, maxlen=1)
    print("End:", end)
    print("Finding middle: ", end = "")
    for item in range(int(math.floor(end/2)), end):
        if item in stations:
            print(item)
            middle = item
            break
    
    process1 = Process(target=count, args=("A", stations, 0, middle))
    process2 = Process(target=count, args=("B", stations, middle, end))

    process1.start()
    process2.start()

    process1.join()
    process2.join()




    #for i in systems[it].ret_stations():
    #                print(systems[it].ret_stations()[i].ret_name(), " id: ", systems[it].ret_stations()[i].ret_id(), " system_id: ", systems[it].ret_stations()[i].ret_system_id(), buy_price, sell_price)
    #                for k in systems[it].ret_stations()[i].ret_prices():
    #                    print("Commodity_id: ", systems[it].ret_stations()[i].ret_prices()[k].ret_commmodity_id(), "Sell_price: ", systems[it].ret_stations()[i].ret_prices()[k].ret_sell_price())
