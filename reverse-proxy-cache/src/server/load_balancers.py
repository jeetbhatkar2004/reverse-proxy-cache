import random
from collections import deque

class LoadBalancer:
    def __init__(self, nodes):
        self.nodes = nodes

    def get_next_node(self):
        raise NotImplementedError

class RoundRobinLoadBalancer(LoadBalancer):
    def __init__(self, nodes):
        super().__init__(nodes)
        self.current = 0

    def get_next_node(self):
        node = self.nodes[self.current]
        self.current = (self.current + 1) % len(self.nodes)
        return node

class LeastConnectionsLoadBalancer(LoadBalancer):
    def get_next_node(self):
        return min(self.nodes, key=lambda node: node.active_connections)

class RandomLoadBalancer(LoadBalancer):
    def get_next_node(self):
        return random.choice(self.nodes)

class WeightedRoundRobinLoadBalancer(LoadBalancer):
    def __init__(self, nodes, weights):
        super().__init__(nodes)
        self.weights = weights
        self.current_weights = list(weights)
        self.current_index = 0

    def get_next_node(self):
        while True:
            self.current_index = (self.current_index + 1) % len(self.nodes)
            if self.current_weights[self.current_index] > 0:
                self.current_weights[self.current_index] -= 1
                return self.nodes[self.current_index]
            if self.current_index == 0:
                self.current_weights = list(self.weights)

class IPHashLoadBalancer(LoadBalancer):
    def get_next_node(self, ip_address):
        hash_value = hash(ip_address)
        return self.nodes[hash_value % len(self.nodes)]