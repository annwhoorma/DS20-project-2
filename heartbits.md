```json
// 1) init new node
// receive from Alla:
{
    "command": "init_node",
    "args": {
        "node": NODE_IP
    }
}
// send to Alla:
// change master and make it master if it s the very first node in the beginning
{
    "status": "OK"/"Failed",
    "args":{
        "master": MASTER_IP,
        "node_status": "new"/"old"
    }
}
```

```json
// 2) master sends <3 - update global variable!!!
// receive from Alla
{
    "command": "<3"
}
// send to Alla
// н и ч е г о
```

```json
// 3) slave(s) want(s) to be a master node - check if master node is actually down or not!
// receive from Alla
{
    "command": "change_master",
    "args": {
        "node": NODE_IP
    }
}
// send to Alla
{
    "status": "OK"/"Failed",
    "args":{
        "master": MASTER_IP // if it was updated to NODE_IP then MASTER_IP = NODE_IP
    }
}
```

```json
// I MAINTAIN LIST OF ALL-ALL SLAVES :)
// 4) 
// 1. master sends all active slaves
// i update my list: LIST_OF_ALL_SLAVES = LIST_OF_ALL_SLAVES_IP (from master)
{
    "command": "get_slaves",
    "args": {
        "slaves": LIST_OF_ALL_ACTIVE_SLAVES_IP
    }
}
// if i want:
{
    "status": "OK"/"Failed"
}

// 2. master requests list of ACTIVE slaves
// from Alla:
{
    "command": "share_slaves"
}
// to Alla:
{
    "status": "OK"/"Failed" // if i want
    args": {
        "slaves": LIST_OF_ALL_ACTIVE_SLAVES_IP
    }
}
```





