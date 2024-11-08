cpp
复制
#include <iostream>
#include <vector>
#include <queue>
#include <limits>

using namespace std;

const int INF = numeric_limits<int>::max();

// 边的结构体
struct Edge {
    int to;
    int weight;
};

// 图的结构体
struct Graph {
    int numNodes;
    vector<vector<Edge>> adjacencyList;
};

// Dijkstra算法
int dijkstra(const Graph& graph, int start, int end, const vector<bool>& exclude) {
    vector<int> dist(graph.numNodes, INF); // 记录起始节点到每个节点的最短路径估计值
    dist[start] = 0;

    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;
    pq.push({0, start});

    while (!pq.empty()) {
        int u = pq.top().second;
        int uDist = pq.top().first;
        pq.pop();

        if (u == end) {
            // 达到终点节点
            return dist[u];
        }

        if (uDist > dist[u]) {
            // 当前节点已经有更短的路径
            continue;
        }

        // 遍历邻居节点
        for (const Edge& edge : graph.adjacencyList[u]) {
            int v = edge.to;
            int weight = edge.weight;

            // 检查是否满足限制条件
            if (exclude[v]) {
                continue;
            }

            // 更新路径估计值
            if (dist[u] + weight < dist[v]) {
                dist[v] = dist[u] + weight;
                pq.push({dist[v], v});
            }
        }
    }

    return -1; // 无法到达终点节点
}

int main() {
    int n, m, s, e, t;
    cin >> n >> m >> s >> e >> t;

    Graph graph;
    graph.numNodes = n;
    graph.adjacencyList.resize(n);

    // 读取边的信息
    for (int i = 0; i < m; i++) {
        int u, v, w;
        cin >> u >> v >> w;
        graph.adjacencyList[u].push_back({v, w});
        graph.adjacencyList[v].push_back({u, w});
    }

    // 创建节点排除列表，初始时全部为false
    vector<bool> exclude(n, false);

    // 从s到e的最小路径估计值
    int sToEWeight = dijkstra(graph, s, e, exclude);
    
    // 将节点e标记为排除，不参与后续的最短路径计算
    exclude[e] = true;

    // 从e到t的最小路径估计值
    int eToTWeight = dijkstra(graph, e, t, exclude);

    // 如果s到e和e到t都存在路径，则计算总的最小路径估计值
    int minWeight = (sToEWeight != -1 && eToTWeight != -1) ? (sToEWeight + eToTWeight) : -1;
    cout << "Minimum weight from s to t: " << minWeight << endl;

    return 0;
}