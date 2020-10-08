import json

errors = {
    "REFUSE_AUTH": "Authentification failed",
    "NO_SUCH_USER": "No such user found",
    "USER_ALREADY_EXISTS": "User with such name already exists",
    "NO_SUCH_DIR" : "Requested directory doesn't exist",
    "NAME_EXISTS": "Object with such name already exists",
    "DIR_NOT_SPECIFIED": "Directory name wasn't specified",
    "NO_SUCH_FILE" : "Requested file doesn't exist"
}

def return_error(code):
    if not code:
        return "ERROR"
    return errors[code]