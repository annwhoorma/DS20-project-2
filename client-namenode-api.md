```json
# Note: 
# 		ВСЕ directories end on "/"
# 		ДЕЛАТЬ ПРОВЕРКУ на ввод директорий с клиента - все должны кончаться на "/"
#		Обсудить загрузку и выгрузку файлов

#		ok = "<3"
#		notok = "</3"

# auth
#		from client
{
    "action" : "auth",
    "args" : {
        "login" : login,
        "password" : password
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
        "login" : login,
        "password" : password
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
        "cur_dir" : cur_dir,
        "filename" : filename
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
        "cur_dir" : cur_dir,
        "filename" : filename
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
        "cur_dir" : cur_dir,
        "filename" : filename
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
        "cur_dir" : cur_dir,
        "filename" : filename
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
        "cur_dir" : cur_dir,
        "filename" : filename
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
        "cur_dir" : cur_dir,
        "dest_dir" : dest_dir
        "filename" : filename
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
        "cur_dir" : cur_dir,
        "dest_dir" : dest_dir
        "filename" : filename
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
        "cur_dir" : cur_dir,
        "target_dir" : target_dir
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
        "cur_dir" : cur_dir,
        "new_dir" : new_dir
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
        "cur_dir" : cur_dir,
        "del_dir" : del_dir
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

