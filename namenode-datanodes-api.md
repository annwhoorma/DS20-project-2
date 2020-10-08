```json
# to send files
{
    "user": "/anya", 
    "path": "/folder2/file3"
}
{
    "user": "/anya", 
    "path": "/folder2/folder3"
}
```

```json
{
    "command": "init",
    "args": {
        "user": "/anya", 
    	"path": "/folder2/folder3"
    }
}
```
```json
{
    "command": "create_dir",
    "args": {
        "user": "/anya",
        "path": "/folder1/folder2"
    }
}
```
```json
{
    "command": "delete_dir",
    "args": {
        "user": "/anya",
        "path": "/folder1/folder2"
    }
}
```
```json
{
    "command": "file_info",
    "args": {
        "user": "/anya",
        "path": "/folder1/folder2"
    }
}
```
```json
{
    "command": "file_delete",
    "args": {
        "user": "/anya",
        "path": "/folder1/folder2/file"
    }
}
```
```json
{
    "command": "file_copy",
    "args": {
        "user": "/anya",
        "src": "/folder1/folder2/file",
        "dst": "/folder1/folder2/"
    }
}
```
```json
{
    "command": "file_create",
    "args": {
        "user": "/anya"
        "path": "/folder1/folder2"
    }
}
```
```json
{
    "command": "file_move",
    "args": {
        "user": "/anya",
        "src": "/folder1/folder2/file",
        "dst": "/folder1/folder2/"
    }
}
```
```json
{
    "command": "read_file",
    "args": {
        "user": "/anya",
        "path": "/folder1/folder2/file"
    }
}
```
```json
{
    "command": "write_file",
    "args": {
        "user": "/anya",
        "path": "/folder1/folder2/file",
        "message": "msg"
    }
}
```

