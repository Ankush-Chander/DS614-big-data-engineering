# User-Space Pseudo-Distributed Hadoop Setup
This tutorial assumes:

* ❌ No `sudo`
* ❌ Cannot create users/groups
* ❌ Cannot write outside `$HOME`
* ✅ Can run user processes
* ✅ Can write inside `$HOME`
* ✅ SSH client works (server must already exist on machine)

---

## End Goal

Single-node Hadoop cluster in **your home directory**:

* **HDFS**

  * NameNode (metadata)
  * DataNode (block storage)
* **YARN**

  * ResourceManager
  * NodeManager
* **MapReduce**

Everything will live under:

```bash
$HOME/hadoop # Hadoop executables/config files
$HOME/hadoop-data # HDFS and YARN data
```

---

## Prerequisites (NO sudo version)

### Check Java (existing installation expected)

You cannot install Java. So verify it exists:

```bash
java -version
```

If Java is available, find its path:

```bash
readlink -f $(which java)
```

Example output:

```
/usr/lib/jvm/java-11-openjdk-amd64/bin/java
```

Then set:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

Add this to your `~/.bashrc`.

If Java is NOT available → you must request your sysadmin to install it.

---

### SSH (No installation)

You cannot install `openssh-server`.

Check if SSH works:

```bash
ssh localhost
```

If it connects → good.

If it asks for password → we configure passwordless login.

---

### Setup Passwordless SSH (User-level only)

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh

ssh-keygen -t rsa -P "" -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test
ssh localhost
```

If login succeeds without password → ready.

---

## Download Hadoop (Inside HOME)

```bash
cd $HOME

wget https://dlcdn.apache.org/hadoop/common/stable/hadoop-3.4.2.tar.gz

tar -xvzf hadoop-3.4.2.tar.gz

rm hadoop-3.4.2.tar.gz
mv hadoop-3.4.2 hadoop
```

Now Hadoop is here:

```bash
$HOME/hadoop
```

Set environment variables in `~/.bashrc`:

```bash
export HADOOP_HOME=$HOME/hadoop
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64   # adjust to your path
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```

Reload:

```bash
source ~/.bashrc
```

---

## Hadoop Configuration (Home-directory only)

We will store ALL Hadoop data inside:

```bash
$HOME/hadoop-data
```

Create directories:

```bash
mkdir -p $HOME/hadoop-data/tmp
mkdir -p $HOME/hadoop-data/dfs/name
mkdir -p $HOME/hadoop-data/dfs/data
```

---

### Edit `hadoop-env.sh`

File:

```
$HADOOP_HOME/etc/hadoop/hadoop-env.sh
```

Set:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64  # adjust to your path
```

---

### core-site.xml

Replace contents with:

```xml
<configuration>

<property>
  <name>hadoop.tmp.dir</name>
  <value>/home/YOUR_USERNAME/hadoop-data/tmp</value>
</property>

<property>
  <name>fs.defaultFS</name>
  <value>hdfs://localhost:9000</value>
</property>

</configuration>
```

Replace `YOUR_USERNAME` with output of:

```bash
whoami
```

---

### hdfs-site.xml

```xml
<configuration>

<property>
  <name>dfs.replication</name>
  <value>1</value>
</property>

<property>
  <name>dfs.namenode.name.dir</name>
  <value>file:///home/YOUR_USERNAME/hadoop-data/dfs/name</value>
</property>

<property>
  <name>dfs.datanode.data.dir</name>
  <value>file:///home/YOUR_USERNAME/hadoop-data/dfs/data</value>
</property>

</configuration>
```
Replace `YOUR_USERNAME` with output of:

```bash
whoami
```

---

### mapred-site.xml

Edit:

```xml
<configuration>

<property>
  <name>mapreduce.framework.name</name>
  <value>yarn</value>
</property>
<property>
  <name>yarn.app.mapreduce.am.env</name>
  <value>HADOOP_MAPRED_HOME=/home/YOUR_USERNAME/hadoop</value>
</property>
<property>
  <name>mapreduce.map.env</name>
  <value>HADOOP_MAPRED_HOME=/home/YOUR_USERNAME/hadoop</value>
</property>
<property>
  <name>mapreduce.reduce.env</name>
  <value>HADOOP_MAPRED_HOME=/home/YOUR_USERNAME/hadoop</value>
</property>
</configuration>
```
Replace `YOUR_USERNAME` with output of:

```bash
whoami
```
---

### yarn-site.xml

```xml
<configuration>

<property>
  <name>yarn.nodemanager.aux-services</name>
  <value>mapreduce_shuffle</value>
</property>

</configuration>
```

---

## Format and Start Hadoop

⚠ Do this only once:

```bash
hdfs namenode -format
```

Start services:

```bash
$HADOOP_HOME/sbin/start-dfs.sh
$HADOOP_HOME/sbin/start-yarn.sh
```

Check processes:

```bash
jps
```

You should see:

```
NameNode
DataNode
ResourceManager
NodeManager
```

---

## Web UI

| Service  | URL                                            |
| -------- | ---------------------------------------------- |
| NameNode | [http://localhost:9870](http://localhost:9870) |
| YARN     | [http://localhost:8088](http://localhost:8088) |

---

## Prepare Test Data (Home-only)

Create local test directory:

```bash
mkdir -p $HOME/gutenberg
cd $HOME/gutenberg

$HADOOP_HOME/bin/wget https://www.gutenberg.org/cache/epub/5000/pg5000.txt
```

Create larger file:

```bash
for i in {1..100}; do cat pg5000.txt; done > pg5000_100.txt
```

---

## Load Data to HDFS

```bash
hdfs dfs -mkdir -p /user/$USER/gutenberg

hdfs dfs -put $HOME/gutenberg/* /user/$USER/gutenberg

hdfs dfs -ls /user/$USER/gutenberg
```

---

## Investigate Blocks

Check block size:

```bash
hdfs getconf -confKey dfs.blocksize
```

Check blocks:

```bash
hdfs fsck /user/$USER/gutenberg/pg5000_100.txt -files -blocks -locations
```

---

## Run WordCount

```bash
hadoop jar \
$HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.4.2.jar \
wordcount \
/user/$USER/gutenberg/pg5000.txt \
/user/$USER/output
```

View result:

```bash
hdfs dfs -cat /user/$USER/output/part-r-00000 | head
```

---

Everything is now **user-space only**.


---

## Common Issues (Non-sudo environment)

1. SSH not working → ask admin to enable sshd
2. Port already in use → change ports in config
3. JAVA_HOME wrong → NameNode fails
4. Firewall blocking localhost UI

---

## Sort based on count

Excellent — now we’ll extend your **home-directory Hadoop setup** with:

 ✅ A second MapReduce job
> ✅ Written in **Python (streaming mode)**
> ✅ That sorts output by **count (descending)**
> ✅ And saves final sorted results in HDFS

We’ll use **Hadoop Streaming**, which lets you plug in any executable (Python, Bash, etc.) as mapper/reducer.


---

### Goal

Input:

```
word \t count
```

Output:

```
count \t word
```

Sorted by count (descending).

We’ll chain:

1. WordCount (already done)
2. Python Streaming Job → sort by count

---

#### 1. Verify WordCount Output

Your previous job created:

```bash
/user/$USER/output
```

Check it:

```bash
hdfs dfs -cat /user/$USER/output/part-r-00000 | head
```

It looks like:

```
A 32
AND 15
THE 1002
```

---

#### 2. Create Python Mapper & Reducer

Create a directory:

```bash
mkdir -p $HOME/streaming-sort
cd $HOME/streaming-sort
```

---

##### Mapper: swap.py

This mapper swaps (word, count) → (count, word)

```python
#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    
    word, count = line.split()
    
    # Emit: count as key, word as value
    print(f"{int(count):010d}\t{word}")
```

Why `:010d`?

Zero padding ensures proper lexical sorting:

```
0000000010
0000000100
```

Without padding, Hadoop sorts lexicographically (wrong order).

Make executable:

```bash
chmod +x swap.py
```

---

##### Reducer: identity_reduce.py

Reducer just prints sorted input.

```python
#!/usr/bin/env python3
import sys

for line in sys.stdin:
    print(line.strip())
```

Make executable:

```bash
chmod +x identity_reduce.py
```

---

#####  Run Hadoop Streaming Job

Hadoop provides streaming jar:

```bash
$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.4.2.jar
```

Run:

```bash
hadoop jar \
$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.4.2.jar \
-input /user/$USER/output \
-output /user/$USER/sorted-output \
-mapper $HOME/streaming-sort/swap.py \
-reducer $HOME/streaming-sort/identity_reduce.py \
-file $HOME/streaming-sort/swap.py \
-file $HOME/streaming-sort/identity_reduce.py
```

If output directory exists:

```bash
hdfs dfs -rm -r /user/$USER/sorted-output
```

Then rerun.

---

##### View Sorted Output

```bash
hdfs dfs -cat /user/$USER/sorted-output/part-00000 | head
```

You’ll see:

```
0000000001 a
0000000001 ability
0000000002 above
...
```

⚠ This is ascending order (default Hadoop sort).

---

#####  Sort in Descending Order

We need a custom comparator.

Add this option:

```bash
-D mapreduce.job.output.key.comparator.class=org.apache.hadoop.mapreduce.lib.partition.KeyFieldBasedComparator \
-D mapreduce.partition.keycomparator.options=-r
```

Full command:

```bash
hadoop jar \
$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.4.2.jar \
-D mapreduce.job.output.key.comparator.class=org.apache.hadoop.mapreduce.lib.partition.KeyFieldBasedComparator \
-D mapreduce.partition.keycomparator.options=-r \
-input /user/$USER/output \
-output /user/$USER/sorted-output-desc \
-mapper $HOME/streaming-sort/swap.py \
-reducer $HOME/streaming-sort/identity_reduce.py \
-file $HOME/streaming-sort/swap.py \
-file $HOME/streaming-sort/identity_reduce.py
```

---

##### Final Output

```bash
hdfs dfs -cat /user/$USER/sorted-output-desc/part-00000 | head
```

Now you’ll see:

```
0000001023 the
0000000897 and
0000000784 of
...
```

---


## Conceptual Pipeline

```
Raw Text
   ↓
WordCount (Java)
   ↓
(word, count)
   ↓
Streaming Mapper (swap)
   ↓
(count, word)
   ↓
Shuffle & Sort (Hadoop)
   ↓
Sorted Output
```

---
