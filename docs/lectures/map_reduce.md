
### Core concepts

#### 1. Distributed Filesystems (DFS)
To process massive datasets with MapReduce, you first need a way to store them spanning multiple machines.  
- **Blocks**: Files are split into large fixed-size chunks (e.g., 128MB).  
- **Replication**: Each block is replicated (usually 3x) across different nodes for fault tolerance.  
- **NameNode/Master**: Stores metadata (file directory tree and the mapping of file blocks to DataNodes).  
- **DataNode/Worker**: Stores the actual data blocks.  

#### 2. Data Locality
*Moving computation is cheaper than moving data.*
Instead of pulling data to a central processing server, the MapReduce framework schedules the **Map** task on the node where the data already resides (or as close as possible).

#### 3. Shared-Nothing Architecture
- Nodes do not share memory or disk storage.  
- They communicate only via the network.  
- This makes the system linearly scalable; adding more nodes adds more processing power and storage without complex locking mechanisms.

#### 4. Fault Tolerance
In a cluster of thousands of machines, failure is the norm, not the exception.
- **Worker Failure**: The Master detects a worker node is unresponsive (heartbeats stop). It re-schedules the tasks of that worker on other nodes that have a distinct replica of the data.        
- **Stragglers**: If a machine is slow (but not dead), the Master can launch a "Speculative Execution" (backup copy) of the task on another machine. The result from whoever finishes first is taken.     

## Complete MapReduce Execution Pipeline

### Job Submission & Planning (Before Everything)

- Client submits job (jar + config).
- Framework:
    - Computes number of **input splits**
    - Determines number of **map tasks**
    - Determines number of **reduce tasks**
    - Initializes metadata structures
- Schedules tasks close to data (data locality).
---

### Input Splits

#### Logical View
The input dataset is logically divided into splits.
Each split generates one Map task.
#### Formal Input to Mapper
[  <k_1, v_1>  ]

- ( k_1 ) = input key (e.g., byte offset)
- ( v_1 ) = input value (e.g., line of text)

#### Systems Perspective
- Splits usually match HDFS block size (e.g., 128MB).
- Map tasks are scheduled on nodes that physically contain the data.
- Reading is sequential and streaming.


---

###  Map Phase

#### Logical View

User defines:
map(k_1, v_1) => list(<k_2, v_2>)
Mapper processes records independently.

#### Example (WordCount)
map(offset, line) => (word, 1)

---

### 2.1 Map-Side Buffering (Hidden but Critical)

Mapper does **NOT immediately write output to disk.**
Intermediate pairs are stored in an **in-memory circular buffer**.
- Size controlled by:
    ```
    mapreduce.task.io.sort.mb
    ```
    
The buffer stores:
- Serialized key-value data
- Metadata (partition, offsets)
---

### 2.2 Spill Phase (When Buffer Fills)

When buffer reaches threshold (~80% full):
1. Records are **sorted by key**
2. Partitioned by reducer
3. Optionally passed through **Combiner**
4. Written to local disk as a spill file

This produces:

```
spill_1
spill_2
spill_3
...
```

Each spill file is:

- Sorted
- Partitioned
---

### 2.3 Combiner (Optional Optimization)

If defined:

combine(k_2, list(v_2)) => list(<k_2, v_2>)

Executed:
- During spill
- Or during merge
Constraints:
- Must be associative
- Must be commutative
Purpose:
- Reduce intermediate data size
- Reduce network traffic

---

### 2.4 Map-Side Merge Phase

If multiple spill files exist:
- Framework performs multi-way external merge sort.
- Produces ONE final map output file.

This file is:
- Sorted by key
- Partitioned by reducer
- Indexed (offsets for each partition)

Now mapper is complete.

---

### 3 Shuffle and Sort Phase

This is fully handled by the framework.

But it is NOT “magic”.
It has multiple sub-phases:

---

#### 3.1 Partitioning

Each intermediate key ( k_2 ) is assigned:

partition = hash(k_2)\mod R  

Where:
- ( R ) = number of reducers

Each reducer is responsible for one partition.

---

#### 3.2 Copy Phase (Network Transfer)

Each reducer:
- Contacts all mappers
- Fetches its partition
This is:
- Parallel
- Over network
- Often compressed

This stage is usually the biggest bottleneck.

---

#### 3.3 Reduce-Side Buffering

Reducer receives segments:  
- Small segments → memory  
- Large segments → disk  
If memory fills:  
- Segments spill to disk  
---

#### 3.4 Reduce-Side Merge Phase

Reducer performs multi-way external merge:

```
segment1
segment2
segment3
...
```

Merged into one sorted stream.  

Now framework guarantees:


<k_2, list(v_2)>

Grouped and sorted by key.

---

### 4️Reduce Phase

#### Logical View

User defines:
reduce(k_2, list(v_2)) => list(<k_3, v_3>)

Reducer processes one key at a time.
#### Important Property

Reducer sees values as an **iterator**, not full list in memory.
Streaming execution:
```
for key in sorted_keys:
    process values
```

Memory-efficient.

---

### 5 Output Phase

Reducer writes:
<k_3, v_3>

to HDFS.

Properties:
- One output file per reducer
- Written sequentially
- Replicated (e.g., 3 copies)
- Durable

Unlike map output, reduce output survives failures.

---

# Failure Handling (Cross-Cutting Concern)

#### If Map Fails:
- Task is re-executed.   
- Intermediate output recomputed.

#### If Reducer Fails:
- Restarted.
- Refetches partitions.

#### Why It Works:

- Deterministic tasks
- Side-effect free user code
- Intermediate output recomputable    

---

# Complete Expanded Version (Compact Structured Form)

```
#### The Phases

0. Job Setup:
   - Job submitted
   - Input splits computed
   - Tasks scheduled (data locality)

1. Input Splits:
   - Logical division of input into splits
   - Each split → one Map task
   - Mapper Input: <k1, v1>

2. Map Phase:
   - User function:
       map(k1, v1) → list(<k2, v2>)
   - Output written to in-memory buffer

2.1 Buffering & Spill:
   - Buffer fills
   - Records sorted by key
   - Partitioned by reducer
   - Optional Combiner applied
   - Written to local disk as spill files

2.2 Map-Side Merge:
   - Multiple spills merged
   - Final sorted, partitioned map output produced

3. Shuffle and Sort:
   - Partition: hash(k2) % R
   - Reducers fetch partitions over network
   - Reduce-side buffering
   - External merge sort
   - Framework groups values:
       <k2, list(v2)>

4. Reduce Phase:
   - User function:
       reduce(k2, list(v2)) → list(<k3, v3>)
   - Streaming execution per key

5. Output:
   - Results written to HDFS
   - One file per reducer
   - Durable storage
```

---

---

### Hadoop Terminology

#### Daemons (Services)
1. **NameNode**: Master of the filesystem (HDFS). Keeps the directory tree and knows where all blocks are.
2. **DataNode**: Worker of the filesystem. Stores the actual blocks on its HDD.
3. **ResourceManager (YARN)**: The master arbitrator of all cluster resources.
4. **NodeManager (YARN)**: The per-machine agent dealing with containers on a single node.

#### Job Components
- **Job**: A full execution unit (Mapper + Reducer + Config).
- **Task**: An individual slice of work (Map Task or Reduce Task) running on one machine.
- **Driver**: The code that submits the job and configures it.
- **Partitioner**: Decides which Reducer gets which key (usually `hash(key) % num_reducers`).
- **Combiner**: A "Mini-Reducer" running locally after the Map phase to reduce network traffic (e.g., pre-summing counts).