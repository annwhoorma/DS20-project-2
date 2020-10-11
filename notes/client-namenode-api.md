```json
#		ok = "<3"
#		notok = "</3"

# auth
#		from client
{
    "action" : "auth",
    "args" : {
        "login" : login
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "free_space" : free_space,
        "cur_dir" : cur_dir,
        "error" : error
    }
}

# new user
# 		from client
{
    "action" : "new_user",
    "args" : {
        "login" : login
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "free_space" : free_space,
        "cur_dir" : cur_dir,
        "error" : error
    }
}

# file create
# 		from client
{
    "action" : "create_file",
    "args" : {
        "cur_dir" : cur_dir # includes file name
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "error" : error
    }
}

# file read
# 		from client
{
    "action" : "read_file",
    "args" : {
        "cur_dir" : cur_dir # includes file name
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "error" : error
    }
}

# file write
# 		from client
{
    "action" : "write_file",
    "args" : {
        "cur_dir" : cur_dir # includes file name
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "error" : error
    }
}

# file delete
# 		from client
{
    "action" : "delete_file",
    "args" : {
        "cur_dir" : cur_dir # includes file name
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "error" : error
    }
}

# file info
# 		from client
{
    "action" : "info_file",
    "args" : {
        "cur_dir" : cur_dir #includes file name
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "size" : size,
        "node_id" : node_id,
        "modified" : modified,
        "accessed" : accessed,
        "error" : error
    }
}

# file copy
# 		from client
{
    "action" : "copy_file",
    "args" : {
        "cur_dir" : cur_dir, # includes filename
        # file will be copied to the same directory only, so (because that s how it is at datanode's side)
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "error" : error
    }
}

# file move
# 		from client
{
    "action" : "move_file",
    "args" : {
        "cur_dir" : cur_dir, # includes file name
        "dest_dir" : dest_dir # full path like /ruslan/...
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "error" : error
    }
}

# open directory
# 		from client
{
    "action" : "open_dir",
    "args" : {
        "cur_dir" : cur_dir,
        "target_dir" : target_dir
        "up": true / false # true if go up in the directories tree, false is go deep
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "cur_dir" : cur_dir,
        "error" : error
    }
}

# read directory
# 		from client
{
    "action" : "read_dir",
    "args" : {
        "target_dir" : target_dir # full path (cur_dir + relative path)
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "dirs" : 
        [
            {
                "name" : name,
                "type" : type
            },
            {
                "name" : name,
                "type" : type
            }
        ],
        "error" : error
    }
}

# make directory
# 		from client
{
    "action" : "make_dir",
    "args" : {
        "cur_dir" : cur_dir # include the new_dir
		# like: /ruslan/existing_folder/new_folder 
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "error" : error
    }
}

# delete directory
# 		from client
{
    "action" : "del_dir",
    "args" : {
        "cur_dir" : cur_dir # includes the directory to delete
        # like: /ruslan/existing_folder/folder_to_delete
    }
}
# 		from server
{
    "status" : status,
    "args" : {
        "error" : error
    }
}
```

