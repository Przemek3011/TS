#!/usr/bin/python3.8

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random
from copy import deepcopy


def version3():
    G = nx.Graph()
    G.add_nodes_from(range(20))

    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4),          # ciąg liniowy
        (4, 5), (5, 6), (6, 7), (7, 8), (8, 9),  # kontynuacja w prawo
        (9, 10), (10, 11), (11, 12), (12, 13),   # łuk dolny
        (13, 14), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), # dół do końca

        # dodatkowe łączniki dla spójności i redundancji
        (0, 5), (5, 10), (10, 15), (15, 19),
        (2, 7), (7, 12), (12, 17),
        (4, 14), (6, 16)
    ]

    G.add_edges_from(edges)
    return G

def version2():
    G = nx.disjoint_union(nx.cycle_graph(6), nx.cycle_graph(14))
    for i in range(3):
        G.add_edge(i, i + 3)
    for i in range(6):
        G.add_edge(i, 2 * i + 6)
    return G

def version1():
    G = nx.disjoint_union(nx.cycle_graph(9), nx.cycle_graph(11))
    for i in range(9):
        G.add_edge(i, i + 10)
    return G

def assign_flow(graph, matrix):
    nx.set_edge_attributes(graph, 0, "a")
    nodes = nx.number_of_nodes(graph)
    for i in range(nodes):
        for j in range(nodes):
            path = nx.shortest_path(graph, i, j)
            for n in range(len(path) - 1):
                graph[path[n]][path[n + 1]]["a"] += matrix[i][j]

def assign_capacity(graph):
    nx.set_edge_attributes(graph, 0, "c")
    for i, j in graph.edges:
        a = graph[i][j]["a"]
        # Przepustowość w bitach/s = losowa przepustowosc + minimum 100 Mbps
        graph[i][j]["c"] = max(2 * a * random.randint(7_000,11_000), 100_000_000) 

def T(graph, matrix_sum, m):
    
   # Obliczamy T = 1/matrix_sum * sum( a(e)/( (c(e)/m) - a(e) ) ).
   # Jeśli a(e) >= c(e)/m dla którejś krawędzi, T=None.
    total = 0
    for i, j in graph.edges:
        a = graph[i][j]["a"]
        c = graph[i][j]["c"]
        if a >= c / m:
            return None
        total += a / (c/m - a)
    return total / matrix_sum

def reliability(graph, matrix, T_max, p, m, iterations=1000):
    
   # Szacujemy prawdopodobieństwo Pr[T < T_max].
   # - w każdej iteracji (iterations) i w kolejnych intervals
   #   losujemy krawędzie, które się psują (z prawd. 1-p).
   # - jeśli graf się rozspójni => T=None
   # - inaczej ponownie przydzielamy flow i liczymy T
   # - liczymy % przypadków T < T_max
    
    successful_trials = 0
    matrix_sum = sum(sum(row) for row in matrix)
    base_t = T(graph, matrix_sum, m)

    for _ in range(iterations):
        trial_graph = deepcopy(graph)
            # krawędzie, które padną (1-p)
        broken = [e for e in nx.edges(trial_graph) if random.random() > p]
        if broken:
            trial_graph.remove_edges_from(broken)
            if not nx.is_connected(trial_graph):
                continue
            assign_flow(trial_graph, matrix)
            t = T(trial_graph, matrix_sum, m)
        else:
            t = base_t
        if (t is None) or (t >= T_max):
            continue
        successful_trials += 1

    return successful_trials / (iterations )

def fast_assign_flow(graph, i, j, change):
    
    #Wzrost natężenia na ścieżce i->j o 'change'.
    
    path = nx.shortest_path(graph, i, j)
    for n in range(len(path) - 1):
        graph[path[n]][path[n + 1]]["a"] += change

def test1(graph, matrix, T_max, p, m, iterations, step):
    
    #W test1 zwiększamy natężenie (macierz N) => rośnie ruch.
    #W każdej iteracji wybieramy parę (i,j), dodajemy 'step' i ponownie liczymy reliability.
    
    test_graph = deepcopy(graph)
    test_matrix = [row[:] for row in matrix]  # kopia macierzy
    results = [reliability(test_graph, test_matrix, T_max, p, m)]

    for _ in range(iterations):
        while True:
            i, j = random.randint(0, 19), random.randint(0, 19)
            if i != j:
                break
        test_matrix[i][j] += step
        fast_assign_flow(test_graph, i, j, step)
        results.append(reliability(test_graph, test_matrix, T_max, p, m))
    return results

def test2(graph, matrix, T_max, p, m, iterations):
    
    #W test2 zwiększamy przepustowość c(e) na każdej krawędzi 
    
    test_graph = deepcopy(graph)
    results = [reliability(test_graph, matrix, T_max, p, m)]
    for _ in range(iterations):
        for i, j in test_graph.edges:
            test_graph[i][j]["c"] += 1000000
        results.append(reliability(test_graph, matrix, T_max, p, m))
    return results

def test3(graph, matrix, T_max, p, m, iterations):
    
    #W test3 dodajemy nowe krawędzie do grafu, każda z nowo dodanych krawędzi
    #ma c(e) = średnia dotychczasowa. Po dodaniu krawędzi ponownie przydzielamy flow.
    
    test_graph = deepcopy(graph)
    results = [reliability(test_graph, matrix, T_max, p, m)]
    caps = nx.get_edge_attributes(test_graph, "c").values()
    new_cap = sum(caps) / len(caps)
    non_edges = list(nx.non_edges(test_graph))

    for _ in range(iterations):
        if not non_edges:
            break
        i, j = random.sample(non_edges, 1)[0]
        non_edges.remove((i, j))
        test_graph.add_edge(i, j)
        test_graph[i][j]["a"] = 0
        test_graph[i][j]["c"] = max(new_cap, 100_000_000)  # co najmniej 100 Mbps
        assign_flow(test_graph, matrix)
        results.append(reliability(test_graph, matrix, T_max, p, m))
    return results



def main():
    G_base = version3()         

    N_base = [
        [0 if i == j else random.randint(100, 500) for j in range(20)]
        for i in range(20)
    ]
    G1, G2, G3 = (deepcopy(G_base) for _ in range(3))
    N1, N2, N3 = ([row[:] for row in N_base] for _ in range(3))

    for G, N in ((G1, N1), (G2, N2), (G3, N3)):
        assign_flow(G, N)
        assign_capacity(G)

    draw_graph(G_base)

    p, T_max, m = 0.98, 0.05, 8000 

    res1 = test1(G1, N1, T_max, p, m, iterations=20, step=2000)
    plot_results(res1, "Test 1 wzrost ruchu", marker='o')
    print("Test 1:", res1)

    res2 = test2(G2, N2, T_max, p, m, iterations=20)
    plot_results(res2, "Test 2 wzrost przepustowości", marker='s')
    print("Test 2:", res2)

    res3 = test3(G3, N3, T_max, p, m, iterations=20)
    plot_results(res3, "Test 3 dodawanie krawędzi", marker='^')
    print("Test 3:", res3)


def draw_graph(G):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, font_color="w")
    plt.title("Graf bazowy (2 cykle + mosty)")
    plt.show()

def plot_results(series, title, marker):
    plt.figure()
    plt.plot(series, marker=marker)
    plt.title(title)
    plt.xlabel("Iteracja")
    plt.ylabel("Niezawodność")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()