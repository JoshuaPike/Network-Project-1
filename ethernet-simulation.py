import simpy
import math
import numpy as np
import matplotlib.pyplot as plt
import random
import sys


# First  define some global variables. You should change values
class G:
    RANDOM_SEED = 33
    # SIM_TIME = 1000   # This should be large
    SIM_TIME = 100000
    SLOT_TIME = 1
    # N = 10
    N = 30
    # ARRIVAL_RATES = [0.001, 0.002, 0.003, 0.006, 0.012, 0.024]  # Check the submission guidelines
    ARRIVAL_RATES = [0.003, 0.006, 0.009, 0.012, 0.015, 0.018, 0.021, 0.024, 0.026, 0.03]
    RETRANMISSION_POLICIES = ["pp", "op", "beb", "lb"]
    # RETRANMISSION_POLICIES = ["pp", "op", "beb"]
    LONG_SLEEP_TIMER = 1000000000

        
class Server_Process(object):
    def __init__(self, env, dictionary_of_nodes, retran_policy, slot_stat):
        self.env = env
        self.dictionary_of_nodes = dictionary_of_nodes 
        self.retran_policy = retran_policy 
        self.slot_stat = slot_stat
        self.current_slot = 0
        # self.server_busy = False 
        self.action = env.process(self.run())
            
    def run(self):
        print("Server process started")
        while True:
            # sleep for slot time
            yield self.env.timeout(G.SLOT_TIME)
        
            # Code to determine what happens to a slot and 
            # then update node variables accordingly based 
            # on the algorithm
            if self.retran_policy == "pp": # We have p-persistant ALOHA "pp" p=0.5
                slot_retrans = []
                num_retrans = 0
                for i in range(0, G.N):
                    if len(self.dictionary_of_nodes[i].buffer) != 0:
                        if random.random() <= 0.5:
                            slot_retrans.append(1)
                            num_retrans += 1
                        else:
                            slot_retrans.append(0)
                    else:
                        slot_retrans.append(0)
        

                if num_retrans == 1:
                    self.slot_stat.addNumber(1)
                    node_id = slot_retrans.index(1)
                    # pop packet out of buffer for this node
                    self.dictionary_of_nodes[node_id].buffer.pop(0)
                else:
                    self.slot_stat.addNumber(0)
                # print(str(len(self.slot_stat.dataset)))

            elif self.retran_policy == "op": # p= 1/N
                slot_retrans = []
                num_retrans = 0
                for i in range(0, G.N):
                    if len(self.dictionary_of_nodes[i].buffer) != 0:
                        if random.random() <= (1/G.N):
                            slot_retrans.append(1)
                            num_retrans += 1
                        else:
                            slot_retrans.append(0)
                    else:
                        slot_retrans.append(0)
                
                
                if num_retrans == 1:
                    self.slot_stat.addNumber(1)
                    node_id = slot_retrans.index(1)
                    # pop packet out of buffer for this node
                    self.dictionary_of_nodes[node_id].buffer.pop(0)
                else:
                    self.slot_stat.addNumber(0)

            elif self.retran_policy == "beb": # Binary Exponential Backoff "beb"
                slot_retrans = []
                num_retrans = 0
                for i in range(0, G.N):
                    cur_node = self.dictionary_of_nodes[i]
                    if len(cur_node.buffer) != 0:
                        if cur_node.slots_to_wait == 0:
                            slot_retrans.append(1)
                            num_retrans += 1
                        else: # if it still has to wait decrease slots_to_wait
                            cur_node.slots_to_wait -= 1
                            slot_retrans.append(0)
                    else:
                        slot_retrans.append(0)


                if num_retrans == 1: # If only one node attempts in a slot
                    self.slot_stat.addNumber(1)
                    node_id = slot_retrans.index(1)
                    self.dictionary_of_nodes[node_id].buffer.pop(0)
                    self.dictionary_of_nodes[node_id].num_reattempts = 0
                else: # multiple attempted to trans... set slots_to_wait using distribution 0 <= r <= 2^k where k = min(n, 10), increase num_reattempts
                    self.slot_stat.addNumber(0)
                    for i in range(0, G.N): # iterate thru all nodes
                        if slot_retrans[i] == 1: # if the node attempted retrans
                            self.dictionary_of_nodes[i].num_reattempts += 1
                            k = min([self.dictionary_of_nodes[i].num_reattempts, 10])
                            self.dictionary_of_nodes[i].slots_to_wait = random.randint(0, 2**k)

            else: # Linear Backoff "lb"
                slot_retrans = []
                num_retrans = 0
                for i in range(0, G.N):
                    cur_node = self.dictionary_of_nodes[i]
                    if len(cur_node.buffer) != 0:
                        if cur_node.slots_to_wait == 0:
                            slot_retrans.append(1)
                            num_retrans += 1
                        else: # if it still has to wait decrease slots_to_wait
                            cur_node.slots_to_wait -= 1
                            slot_retrans.append(0)
                    else:
                        slot_retrans.append(0)


                if num_retrans == 1: # If only one node attempts in a slot
                    self.slot_stat.addNumber(1)
                    node_id = slot_retrans.index(1)
                    self.dictionary_of_nodes[node_id].buffer.pop(0)
                    self.dictionary_of_nodes[node_id].num_reattempts = 0
                else: # multiple attempted to trans... set slots_to_wait using distribution 0 <= r <= 2^k where k = min(n, 10), increase num_reattempts
                    self.slot_stat.addNumber(0)
                    for i in range(0, G.N): # iterate thru all nodes
                        if slot_retrans[i] == 1: # if the node attempted retrans
                            self.dictionary_of_nodes[i].num_reattempts += 1
                            k = min([self.dictionary_of_nodes[i].num_reattempts, 1024])
                            self.dictionary_of_nodes[i].slots_to_wait = random.randint(0, k)
            
            
            
            
                    
        
class Node_Process(object): 
    def __init__(self, env, id, arrival_rate):
        
        self.env = env
        self.id = id
        self.arrival_rate = arrival_rate
        
        # Other state variables
        # self.previous_time = 0
        self.buffer = [] # Buffer for containing packets
        self.total_packets = 0 # total number of packets this node has seen
        self.num_reattempts = 0
        self.slots_to_wait = 0

        self.action = env.process(self.run())
        

    def run(self):
        # packet arrivals 
        print("Arrival Process Started:", self.id)
        
        # Code to generate the next packet and deal with it
        while True:
             # Infinite loop for generating packets
            yield self.env.timeout(random.expovariate(self.arrival_rate))
            
            # self.server_process.sum_time_length += (self.env.now - self.prevous_time)*len(self.buffer)
            # self.prevous_time = self.env.now
            
            #create and enque new packet
            self.total_packets += 1
            arrival_time = self.env.now  
            new_packet = Packet(self.total_packets,arrival_time)
            # self.server_process.len += 1
            #print(self.server_process.len)
            self.buffer.append(new_packet)
            # print('Packet added to node: ' + str(self.id))
        

class Packet:
    def __init__(self, identifier, arrival_time):
        self.identifier = identifier
        self.arrival_time = arrival_time


class StatObject(object):    
    def __init__(self):
        self.dataset =[]

    def addNumber(self,x):
        self.dataset.append(x)




def main():
    # command line arguments
    if len(sys.argv) != 3:
        sys.exit('Invalid arguments, must select a retransmission algorithm (pp, op, beb, or lb) and a arrival rate')
    if sys.argv[1] not in G.RETRANMISSION_POLICIES:
        sys.exit('Algorithm specified not possible... select pp, op, beb, or lb')
    retran_policy = sys.argv[1]
    arrival_rate = float(sys.argv[2])

    print("Simiulation Analysis of Random Access Protocols")
    random.seed(G.RANDOM_SEED)
    fignum = 1
    # throughput_list = []
    throughput = 0
    env = simpy.Environment()
    slot_stat = StatObject()
    dictionary_of_nodes  = {} # I chose to pass the list of nodes as a 
                              # dictionary since I really like python dictionaries :)
            
    for i in list(range(0,G.N)):
        node = Node_Process(env, i, arrival_rate)
        dictionary_of_nodes[i] = node
    server_process = Server_Process(env, dictionary_of_nodes,retran_policy,slot_stat)
    env.run(until=G.SIM_TIME)
            
    # code to determine throughput
    sum = 0
    for i in slot_stat.dataset:
        sum += i
    throughput = sum / len(slot_stat.dataset)
    # throughput_list.append(throughput)
    print('Throughput = ' + str(round(throughput, 2)))

    # code to plot 
    # title = ""
    # plot_file = ""
    # if retran_policy == "pp":
    #     title = 'Throughtput vs. $\lambda$ for p-Persistent: $p = 0.5$'
    #     plot_file = 'pp_plot.png'
    # elif retran_policy == "op":
    #     title = 'Throughtput vs. $\lambda$ for p-Persistent: $p = \frac{1}{N}$'
    #     plot_file = 'op_plot.png'
    # elif retran_policy == "beb":
    #     title = 'Throughtput vs. $\lambda$ for Binary Exponential Backoff$'
    #     plot_file = 'beb_plot.png'
    # else: 
    #     title = 'Throughtput vs. $\lambda$ for Linear Backoff$'
    #     plot_file = 'lb_plot.png'
    # plt.figure(fignum)
    # plt.title(title)
    # # plt.title('$\gamma = 0.99$ | initial replay size = 15000 | buffer size = 80000')
    # plt.plot(G.ARRIVAL_RATES, throughput_list, linewidth = 1)
    # plt.xlabel('$\lambda$')
    # plt.ylabel('Throughput')
    # plt.grid()
    # plt.savefig(plot_file)
    # plt.show()
    
if __name__ == '__main__': main()