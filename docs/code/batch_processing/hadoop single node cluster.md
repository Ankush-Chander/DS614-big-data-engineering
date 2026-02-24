# Endgoal

Set up a single node hadoop cluster  
- **HDFS** → storage layer  
    - NameNode = metadata manager  
	- DataNode = block storage  
- **YARN** → resource manager  
    - ResourceManager  
    - NodeManager  
- **MapReduce** → compute engine  


# Prerequisites

Hadoop is a Java-based framework, so the Java Development Kit (JDK) is a mandatory requirement. It allows Hadoop to run its jar files and daemons.
1. Install JAVA
```bash
if ! command -v java &> /dev/null; then
    sudo apt install default-java
else
    echo "Java is already installed"
fi
```


2. Install SSH

Hadoop uses SSH (Secure Shell) to manage its nodes. Even in a single-node setup (pseudo-distributed mode), Hadoop requires SSH to start and stop its daemons locally.

```bash
# install ssh
if ! dpkg -s openssh-server >/dev/null 2>&1; then
    sudo apt install openssh-server openssh-client
else
    echo "OpenSSH Server is already installed"
fi
```

# User/group configuration

It is best practice to run Hadoop under a dedicated user account. This ensures process isolation and prevents permission conflicts with other system users or root. We create a `hadoop` group and an `hduser` for this purpose.
```bash
if ! getent group hadoop >/dev/null; then
    sudo groupadd hadoop
else
    echo "Group 'hadoop' already exists"
fi

# add hduser to hadoop group
if ! id -u hduser >/dev/null 2>&1; then
    sudo adduser --ingroup hadoop hduser
else
    echo "User 'hduser' already exists"
fi

# switch to hduser
su - hduser

# configure ssh
# We generate an SSH key pair for the hduser and add the public key to authorized_keys.
# This enables password-less login to localhost, which allows Hadoop scripts to start daemons automatically without user intervention.
ssh-keygen -t rsa -P "" -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

#verify passwordless login
ssh localhost


```

# Hadoop download

We download the stable release of Hadoop, extract it to `/usr/local/`, and change the ownership to `hduser`. This directory will serve as the `HADOOP_HOME`.

```bash
# Execute as normal user
if [ ! -d "/usr/local/hadoop" ]; then
    cd /usr/local
    sudo wget -c https://dlcdn.apache.org/hadoop/common/stable/hadoop-3.4.2.tar.gz
    sudo tar -xvf hadoop-3.4.2.tar.gz
    sudo mv hadoop-3.4.2 hadoop
    sudo chown -R hduser:hadoop hadoop
else
    echo "Hadoop is already installed at /usr/local/hadoop"
fi

```

# Hadoop configuration

### Update $HOME/.bashrc

We verify existing environment or set new environment variables in `.bashrc` so that the shell knows where to find Hadoop commands (`/bin` and `/sbin`) and the Java runtime. This simplifies running commands from any directory.
```bash
# $HOME/.bashrc
# Set Hadoop-related environment variables
export HADOOP_HOME=/usr/local/hadoop

# Set JAVA_HOME (we will also configure JAVA_HOME directly for Hadoop later on)
export JAVA_HOME=/usr/lib/jvm/default-java

# Some convenient aliases and functions for running Hadoop-related commands
unalias fs &> /dev/null
alias fs="hadoop fs"
unalias hls &> /dev/null
alias hls="fs -ls"

# If you have LZO compression enabled in your Hadoop cluster and
# compress job outputs with LZOP (not covered in this tutorial):
# Conveniently inspect an LZOP compressed file from the command
# line; run via:
#
# $ lzohead /hdfs/path/to/lzop/compressed/file.lzo
#
# Requires installed 'lzop' command.
#
lzohead () {
    hadoop fs -cat $1 | lzop -dc | head -1000 | less
}

# Add Hadoop bin/ directory to PATH
export PATH=$PATH:$HADOOP_HOME/bin
```

## Update hadoop configs

We must explicitly set `JAVA_HOME` in `hadoop-env.sh` to ensure Hadoop allows access to the correct Java installation, regardless of the shell's current environment state.
```bash
# set this line in etc/hadoop/hadoop-env.sh
export JAVA_HOME=/usr/lib/jvm/default-java
```

Edit `etc/hadoop/core-site.xml`

This file contains configuration settings for Hadoop Core, such as I/O settings that are common to HDFS and MapReduce.
- `hadoop.tmp.dir`: Specifies the base directory for temporary files.
- `fs.default.name`: Points to the NameNode (the master node of HDFS) URI.

```xml 
<property>
  <name>hadoop.tmp.dir</name>
  <value>/app/hadoop/tmp</value>
  <description>A base for other temporary directories.</description>
</property>

<property>
  <name>fs.default.name</name>
  <value>hdfs://localhost:54310</value>
  <description>The name of the default file system.  A URI whose
  scheme and authority determine the FileSystem implementation.  The
  uri's scheme determines the config property (fs.SCHEME.impl) naming
  the FileSystem implementation class.  The uri's authority is used to
  determine the host, port, etc. for a filesystem.</description>
</property>
```


Edit `etc/hadoop/mapred-site.xml`
```xml
<property>
  <name>mapreduce.framework.name</name>
  <value>yarn</value>
</property>
<property>
    <name>mapreduce.application.classpath</name>
    <value>$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*</value>
</property>
```
Edit `etc/hadoop/yarn-site.xml`

```xml
<property>
  <name>yarn.nodemanager.aux-services</name>
  <value>mapreduce_shuffle</value>
</property>
<property>
    <name>yarn.nodemanager.env-whitelist</name>
    <value>JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_HOME,PATH,LANG,TZ,HADOOP_MAPRED_HOME</value>
</property>

```

Edit `etc/hadoop/hdfs-site.xml`

This file holds configuration settings for the HDFS daemons (NameNode, DataNode, etc.).
- `dfs.replication`: We set this to `1` because we are running on a single node. The default is 3, but we don't have other nodes to replicate data to.
```xml
<property>
  <name>dfs.replication</name>
  <value>1</value>
  <description>Default block replication.
  The actual number of replications can be specified when the file is created.
  The default is used if replication is not specified in create time.
  </description>
</property>
```
## Setup HDFS directory

We need to manually create the directory we defined in `hadoop.tmp.dir` and assign the correct permissions so the `hduser` can write to it.
```bash
# Filesystem related setup
sudo mkdir -p /app/hadoop/tmp
sudo chown hduser:hadoop /app/hadoop/tmp
# ...and if you want to tighten up security, chmod from 755 to 750...
sudo chmod 750 /app/hadoop/tmp
```


## Prepare data

We will download some sample text files (books from Project Gutenberg) to test our Hadoop cluster.
1. Download files to the local /tmp directory.
2. Create a directory inside the HDFS system.
3. Copy the files from the local filesystem into HDFS.
4. Verify blocks and storage.

```bash
# on host machine
sudo mkdir -p /tmp/gutenberg
cd /tmp/gutenberg
sudo wget -c https://www.gutenberg.org/cache/epub/20417/pg20417.txt https://www.gutenberg.org/cache/epub/5000/pg5000.txt https://www.gutenberg.org/cache/epub/4300/pg4300.txt

# create a big file by concatenating pg5000.txt 100 times
sudo bash -c 'for i in {1..100}; do cat pg5000.txt; done > pg5000_100.txt'

# check if files downloaded correctly
ls  /tmp/gutenberg
```

## Start Hadoop

Now that configuration is complete, we initialize and start the cluster.
- `namenode -format`: Initializes the DFS filesystem structure. This should only be done once.
- `start-all.sh`: Starts all Hadoop daemons.
- `jps`: Checks running Java processes to verify everything started correctly.

```bash
## Formatting the HDFS filesystem via the NameNode
./bin/hadoop namenode -format

## start hadoop cluster
./sbin/start-all.sh

## test all nodes started
jps
```


## Load data to HDFS
```bash
###############################
# to be run as hduser
sudo su - hduser
# create directory on data node
hdfs dfs -mkdir -p /usr/hduser/gutenberg

# copy files from host to datanode
hdfs dfs -copyFromLocal /tmp/gutenberg /usr/hduser

# check if files copied successfully
hdfs dfs -ls  /usr/hduser/gutenberg

```

## Investigate Data/metadata
```bash
# data to be found at
ls -lh /app/hadoop/tmp/dfs/data

# metadata to be found at
ls -lh /app/hadoop/tmp/dfs/name

# get size of block
hdfs getconf -confKey dfs.blocksize 
# returns 134217728 (128MB)

# blocks info of file
hdfs fsck /usr/hduser/gutenberg/pg5000.txt -files -blocks -locations

# block info of the big file
hdfs fsck /usr/hduser/gutenberg/pg5000_100.txt -files -blocks -locations
```


## Web UI

| Service         | URL                                             |
| --------------- | ----------------------------------------------- |
| NameNode        | [http://localhost:9870](http://localhost:9870/) |
| ResourceManager | [http://localhost:8088](http://localhost:8088/) |
## Cluster stats

Finally, we perform a health check report to verify the status of the HDFS nodes and available capacity.

```bash
hdfs dfsadmin -report
```

## Run word count using hadoop
```bash
hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-3.4.2.jar wordcount /usr/hduser/gutenberg/pg5000.txt /usr/hduser/gutenberg-out
```

---
### Common pitfalls
1. If NameNode fails:
	- Check JAVA_HOME
	- Check permissions
	- Check logs in `$HADOOP_HOME/logs`   

### Further Experiments

- Change block size to 1MB → observe blocks
- Change replication to 2 → observe failure
- Kill DataNode → observe report

# References
- [Apache Hadoop 3.4.2 &#x2013; Hadoop: Setting up a Single Node Cluster.](https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-common/SingleCluster.html)
- [Running Hadoop On Ubuntu Linux (Single-Node Cluster) - outdated but good](https://www.michael-noll.com/tutorials/running-hadoop-on-ubuntu-linux-single-node-cluster)