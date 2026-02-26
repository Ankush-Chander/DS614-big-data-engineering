# 2-node distributed cluster


* **Node 1 → NameNode + ResourceManager + DataNode**
* **Node 2 → DataNode + NodeManager**
* Replication factor = **2** (so blocks replicate across machines)


## Assumptions
- You have single node cluster already set up on both nodes using [Single node cluster setup](../non_sudoer_hadoop_single_node_cluster)
- Node1 hostname: `node1`
- Node2 hostname: `node2`
- Both users have Hadoop in `$HOME/hadoop`
- Both machines can SSH to each other

---

## High-Level Change

From:

```
Node1 → Complete standalone cluster
Node2 → Complete standalone cluster
```

To:

```
node1:
  NameNode
  DataNode
  ResourceManager
  NodeManager

node2:
  DataNode
  NodeManager
```

---
## STEP 0 - Take config backup in case restoring back to single node cluster (On both nodes)
```bash
cp -r $HADOOP_HOME/etc/hadoop $HADOOP_HOME/etc/hadoop_backup
```


## STEP 1 — Clean Both Nodes (Important)

On **both nodes**:

Stop everything:

```bash
stop-dfs.sh
stop-yarn.sh
```

Remove old metadata:

```bash
rm -rf $HOME/hadoop-data/dfs/*
```

We must reformat the cluster because metadata must be shared from a single NameNode.

---

## STEP 2 — Decide Master Node

Let:

* **node1 → Master**
* **node2 → Worker**

Find hostnames:

```bash
hostname
```

Or use IPs if hostnames don’t resolve.

If needed, add entries in `~/.bashrc` (temporary):

```bash
export HADOOP_MASTER=node1
```

---

## STEP 3 — Configure SSH Between Nodes

From **node1**, ensure passwordless SSH to node2:

```bash
ssh node2
```

If password prompts → copy key:

```bash
ssh-copy-id node2
```

Test again:

```bash
ssh node2
```

Also test reverse:

```bash
ssh node1
```

This is required because `start-dfs.sh` uses SSH to start daemons remotely.

---

## STEP 4 — Modify Configuration (On BOTH Nodes)

Now we update configs to make them distributed.

---

### core-site.xml (Both nodes)

Change:

```xml
<property>
  <name>fs.defaultFS</name>
  <value>hdfs://node1:9000</value>
</property>
```

IMPORTANT:

* Replace `localhost`
* Use `node1` (master hostname or IP)

---

### hdfs-site.xml (Both nodes)

Change replication to **2**:

```xml
<property>
  <name>dfs.replication</name>
  <value>2</value>
</property>
```

Keep name/data directories local (do NOT share directories).

On node1:

```
dfs.namenode.name.dir → node1 local path
dfs.datanode.data.dir → node1 local path
```

On node2:

```
dfs.datanode.data.dir → node2 local path
```

Node2 does NOT need namenode directory actively used (but harmless if present).

---

### workers file (VERY IMPORTANT)

Edit:

```
$HADOOP_HOME/etc/hadoop/workers
```

On **node1**, set:

```
node1
node2
```

On **node2**, it doesn’t matter much, but keep same for consistency.

This tells Hadoop where to start DataNodes.

---

### yarn-site.xml (Both nodes)

Add ResourceManager host:

```xml
<property>
  <name>yarn.resourcemanager.hostname</name>
  <value>node1</value>
</property>
```

Keep shuffle service.

---

## STEP 5 — Format ONLY ON MASTER (node1)

⚠ IMPORTANT: Format only once, and only on node1.

On node1:

```bash
hdfs namenode -format
```

DO NOT format on node2.

---

## STEP 6 — Start Cluster From node1

On node1:

```bash
start-dfs.sh
start-yarn.sh
```

These scripts will SSH into node2 and start DataNode + NodeManager there.

---

## STEP 7 — Verify Processes

### On node1:

```bash
jps
```

Should show:

```
NameNode
DataNode
ResourceManager
NodeManager
```

### On node2:

```bash
jps
```

Should show:

```
DataNode
NodeManager
```

---

## STEP 8 — Verify Replication

Upload a file:

```bash
hdfs dfs -mkdir /test
hdfs dfs -put somefile.txt /test
```

Now check block placement:

```bash
hdfs fsck /test/somefile.txt -files -blocks -locations
```

You should see:

```
Block replica on node1
Block replica on node2
```

---

## 🔥 Final Architecture

```
                node1
      -------------------------
      NameNode
      DataNode
      ResourceManager
      NodeManager
      -------------------------
                 |
                 |  Replication pipeline
                 |
      -------------------------
                node2
      DataNode
      NodeManager
      -------------------------
```