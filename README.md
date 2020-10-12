# Group Project 2: Distributed File System
Alla Chepurova, Anna Boronina, Ruslan Mihailov

## How to launch and use

### Usage
First thing to do before using our DFS is to log in:
![](https://i.imgur.com/vcyOQAN.png)

If you type incorrect or invalid cridentials, you will be automatically redirected to tha sign up page where you can create new account for the user:
![](https://i.imgur.com/82QnZFt.png)

After creation of new user in our file system, you will be welcomed by the main page where all functionality is executed and managed along with displayed number of free bytes (if new file system was initialized):
![](https://i.imgur.com/BZIo1bm.png)

For the sake of visuality, actions among files and directories are separated into 2 sections, where one can easily execute needed commands. The command starts as the button (which represents the action itself) is pressed. Couple of examples of functionality and outputs of our DFS:
![](https://i.imgur.com/btaN6yu.png)
![](https://i.imgur.com/F3fAyoc.png)


## Architectural diagram
![](https://i.imgur.com/VjH02hl.png)

## Description of communication protocols

### Client-Namenode Protocol
The communication between the client and the namenode is very simple. Client sends a HTTP request with a json message to the server. The message describes the command and the arguments:

```json
{
    "command": "read_dir",
    "args":{
        "cur_dir": "ruslan/DS/"
    }
}
```

In all the commands, we used the full paths in order to simplify the processing at the namenode side.

In return, the client receives the following:

```json
# no error occured:
{
    "status": "<3"
}
# an error occured:
{
    "status": "</3",
    "args": {
        "error": "The path isn't valid"
    }
}
```

In case of a file read or write, the client sends a request, as usual. If the response is positive, the client starts to wait for a file from the namenode (which will get from the datanode, of course) or to send a file to the namenode.

### Namenode-Datanode Protocol

The communication between the namenode and the datanode is simple as well. The namenode send a HTTP request to the datanode of the following form:

```json
{
    "command": "delete_dir",
    "args": {
        "user": "/anya",
        "path": "/DS"
    }
}
```

In return, the namenode will receive a response message. An example is below.

```json
# no error occured:
{
    "status": "OK",
    "message" : ""
}
# an error occured:
{
    "status": "Failed",
    "message" : "Such directory doesn't exist"
}
```

## Heartbeat Protocol

### Initiation. Leader election.

![](https://i.imgur.com/IUMPM8J.png)

![](https://i.imgur.com/QReBpH0.png)

### Master node periodically polls with heart signal  datanode and slave replicas to let them node it is alive. Also it gets the response from slaves and decides whether all they are alive.
![](https://i.imgur.com/yuPwyE8.png)

### Master node fails. It is detected by timeout on the slaves and namenode as there would be no heart signal for some time. After that election process would be initiate again.

![](https://i.imgur.com/MXqFp0H.png)

### Slave failure is detected by the abcense of responce from it.
![](https://i.imgur.com/YxNICvV.png)

### Maintaining scalability. Adding one new node.
![](https://i.imgur.com/6Lm49MP.png)


#### Namenode-Datanode
All the message are managed using HTTP requests and the commands in json representation. 

The communication with the master node goes in the following way:

1) the master node requests list of the slaves from the namenode and updated its own - some new namenodes could join since the last update, and in this case the master should send them all the files;

2) the master node sends a heartbeat to show that it's alive;

3) the master checks on each of the slave nodes and updates its own list of active namenodes;

4) the master node send its own list of alive nodes to the namenode, then the namenode updates its own list of active slaves and those, who are not present in the received list, marks as inactive.

The communication with the other nodes is the following:

-  if the node has just joined, it will send a request to the namenode to include it in the list of slaves. If this node is the only one in the cluster, it will be set a master;
- nodes can send a request to become a master node. In such case, the namenode should check if the master is up (it is checked by checking how much time passed since the last time when the master performed its step 2). If the master is up, the node's request is denied. If the master is, indeed, down, the node will become a new master.


## Link to the GitHub and Docker Hub

[Github link](https://github.com/annwhoorma/DS20-project-2)

[Data nodes image](https://hub.docker.com/repository/docker/screemix/datastorage)

[Client Flask application image](https://hub.docker.com/r/dmmc123/client_web_app)

[Namenode image](https://hub.docker.com/repository/docker/whoorma/namenode)

[Neo4j used by Namenode image](https://hub.docker.com/repository/docker/whoorma/neo4j-for-namenode)

Note that the last two images are both needed for a namenode to work properly. For some reason, while testing, the exposed port 5000 didn't get mapped on the local machine. So, you can test it by running the command below *inside* the namenode container. 
``` json
curl --header "Content-Type: application/json" --request GET --data '{"command": "init_node", "args": {"node": "10.0.0.1"}}' http://localhost:5000/
```

## Contribution of each team member

### Anna Boronina

Anna was responsible for the naming server - we will call it a namenode. It is an interface between the client and the storage that makes sure that no bad request is satisfied and the state of the system is consistent.

The Namenode is designed in the following way: it accepts a request from the client, processes it, checks the validity of the request and then forwards it to the master datanode. After that, if the master datanode responded "OK", the namenode makes certain changes in its database according to the command received from the client. If the datanode said "Failed", then no changes are applied to the database and the client is notified that the requested operation failed. Some commands can be processed without bothering the datanodes, such as authentication or listing the files in the directory.

In addition to that, the namenode is responsible for keeping a list of all active datanodes (knowing who is the main datanode and who are the dependent ones) and check on the main datanode using the heartbeats protocol. Main datanode and the namenode exchange messages to keep the list of the active datanodes consistent. Also, whenever there is a datanode that just joined the system, this datanode will ask the namenode for initialization. 

### Alla Chepuróva

Alla's task was to implement the communication with the Namenode and logic of interaction between Datanodes: replication of data, dealing with storages, executing commands connecting with file systems, etc. Also the essential part of her task was to implement heartbeat protocol to maintain the consistency, fault tolerance and scalability of the application. As a result, the filesystems could be stored in consistent way on different machines.

### Ruslan Mihaylov

Ruslan was implementing a Flask web application for the client. In general, it serves one main purpose - graphical interface for DFS commands. Internally, it's just a bunch of forms and buttons which trigger an application to send json data with command description towards the Namenode. Along with sending json commands according to developed API Ruslan needed to handle file upload/download from the client side.

## Reflection

### Good points

1. Each one of us showed themselves as a completely independent developer.
2. Each one of us showed that they are ready to devote a huge amount of time to learn something new such as files replication across multiple machines or writing an HTTP-server and a client using different approaches.

### Things that could go better

1. We experienced lack of communication within the team. We had only one meeting during which we had discussed what we wanted to see as our final result and split the tasks. We thought that our parts were mostly independent and it would be easy to define how these part were going to communicate in the end. We were definitely wrong about that. 
2. Misunderstandings regarding the design. Since we were working mostly independently, some of our wrong conclusions stayed with each team member until the end. For example, the validity checks were implemented in both namenode and datanode. It had led to a lot of lines of redundant code.
3. We didn't agree upon the API from the very beginning. As was mentioned earlier, we thought we would specify it in the end. And then in the end we had to face how different our approaches are. That is why we didn't manage to connect our parts after all. 
