
# Replication in OpenSearch

## **Objectives**

By the end of this lab, students should be able to:

1. Set up a **2-node cluster** using OpenSearch without root access

2. Understand how **distributed systems form clusters**

3. Observe and reason about:

    - **Primary shards**

    - **Replica shards**

    - **Data distribution and fault tolerance**

---

## **Prerequisites**

- Two Linux environments (can be:

  - Two separate machines, or

  - One machine with two separate processes simulating nodes)

- Access only to **home directory** (no sudo/root)

- Java runtime available (or ability to use a bundled runtime)

- Basic familiarity with:

  - Running background processes

  - Editing configuration files

  - Sending HTTP requests (curl or equivalent)

---

## **Part 1.1: Installing OpenSearch Locally**

Run OpenSearch without system-wide installation.

**Steps:**

1. Download the OpenSearch distribution archive (tarball, not package manager) from [here](https://opensearch.org/downloads/).

2. Extract it into your home directory.

3. Inspect the directory structure:

    - `config/`

    - `data/`

    - `logs/`

    - `bin/`

4. Identify:

    - The main configuration file

    - The startup script

---

## **Part 1.2: Installing OpenSearch Dashboard Locally**

1. Download the OpenSearch distribution archive (tarball, not package manager) from [here](https://opensearch.org/downloads/).
2. Extract it into your home directory.

## **Part 2: Configuring Node 1**

Run the first node of your cluster.

**Steps:**

1. Duplicate the extracted folder into a separate directory for Node 1.
2. Follow [installation guide](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/tar)
3. Edit configuration:
    - Assign a **cluster name**
    - Assign a **node name**

    ```yaml
    cluster.name: ds614-lab
    node.name: node-1
    node.roles: [cluster_manager, data]
    network.host: [IP_ADDRESS] # "localhost" if both nodes on same machine, private ip if on different machines
    http.port: 9200
    transport.port: 9300

    ```

    - Configure:
        - Network host (local machine)
        - Port (default or custom)
4. Configure discovery settings:
    - Define this node as part of a cluster (even if single node for now)
5. Set a **data directory inside your home folder**
6. Start the node
7. Verify:
    - Node is running at this url: [](http://localhost:9200)
    - It responds to HTTP requests
    - Cluster health is available [](http://localhost:9200/_cat/health)
    - Check nodes url: [](http://localhost:9200/_cat/nodes)

---

## **Part 2.1: Configuring OpenSearch Dashboard**

1. Edit the configuration file `config/opensearch_dashboards.yml`:
    - Set `opensearch.hosts` to point to your OpenSearch node(s)
    - Set `server.port` to a unique port (different from OpenSearch nodes)
    - Disable security plugin

    ```yaml
    opensearch_security.enabled: false
    ```

2. Start OpenSearch Dashboard
3. Verify:
    - Dashboard is running
    - It responds to HTTP requests
    - Cluster health is available

## **Part 3: Configuring Node 2**

Join a second node to form a cluster.

**Steps:**

1. Create a second copy of OpenSearch directory for Node 2

2. Modify configuration:

    - Different **node name**
    - Different **port**
    - Same **cluster name** as Node 1

3. Configure **discovery/seed hosts**:
    - Node 2 should know about Node 1
    - Set in each node config file(opensearch.yml)

    ```yaml
    discovery.seed_hosts: ["localhost:9300"] # other nodes transport port
    ```

    - Set in each node config file(opensearch.yml)

    ```yaml
    cluster.initial_cluster_manager_nodes: ["node-1", "node-2"] # on both nodes
    ```

4. Ensure:
    - Unique data directory
    - Clear data directories
5. Restart both nodes
6. Verify:
    - Both nodes appear in the same cluster
    - Cluster size = 2 nodes

---

## **Checkpoint 1 (Conceptual)**

Answer:

- What information allows nodes to discover each other?
- Why must node names and ports differ?
- What happens if both nodes use the same data directory?

---

## **Part 4: Creating an Index with Controlled Sharding**

Understand how data is partitioned.

### **Steps**

1. Create an index with:
    - A fixed number of **primary shards** (e.g., 2 or more)
    - **0 replicas**

2. Insert sample documents (at least 20–50 records)
3. Query:
    - Index statistics
    - Shard allocation

---

### **Observation Tasks**

- How many shards are created?
- Where are they located?
- Does each node store data?

---

## **Part 5: Adding Replication**

### **Goal**

Understand redundancy and fault tolerance.

### **Steps**

1. Update the index:

    - Increase number of **replica shards**

2. Observe:

    - Redistribution of shards across nodes

3. Check:

    - Cluster health status

---

### **Observation Tasks**

- What changes after adding replicas?

- Are replicas placed on the same node as primaries?

- Why or why not?

---

## **Checkpoint 2 (Conceptual)**

Answer:

- Difference between **primary shard** and **replica shard**

- Why replication improves availability but increases storage cost

- What happens if replication factor > number of nodes?

---

## **Part 6: Failure Simulation**

### **Goal**

Observe fault tolerance behavior.

### **Steps**

1. Stop one node manually

2. Observe:

    - Cluster health

    - Shard status

3. Query data:

    - Check if reads still work

4. Restart the stopped node

5. Observe:

    - Rebalancing

    - Recovery process

---

### **Observation Tasks**

- What happens to primary shards when a node goes down?

- How does OpenSearch maintain availability?

- What is the cluster health during failure?

---

## **Checkpoint 3 (Deep Thinking)**

- Can a cluster function with:

  - 1 node + replicas configured?

- Why does OpenSearch avoid placing replicas on the same node?

- What is the minimum number of nodes needed for true fault tolerance?

---

## **Part 7: Optional Exploration (Advanced)**

- Change number of shards and observe redistribution

- Explore:

  - Shard rebalancing when nodes join/leave

  - Cluster health states: green, yellow, red

- Try uneven shard configurations and analyze imbalance

---

## **Submission Requirements**

Students must submit:

1. **Screenshots / logs** showing:

    - 2-node cluster running

    - Index creation

    - Shard distribution

2. **Short answers** to all checkpoints

3. **One-page reflection**:

    - What surprised you?

    - What design trade-offs did you observe?

---
