# a file that was create to make the errors throwing process easier for the namenode
'''
a dictionary of the pairs <error_code, error_text>
'''
errors = {
    "REFUSE_AUTH": "Authentification failed",
    "NO_SUCH_USER": "No such user found",
    "USER_ALREADY_EXISTS": "User with such name already exists",
    "NO_SUCH_DIR" : "Requested directory doesn't exist",
    "NAME_EXISTS": "Object with such name already exists",
    "DIR_NOT_SPECIFIED": "Directory name wasn't specified",
    "NO_SUCH_FILE" : "Requested file doesn't exist",
    "EMPTY_USERNAME" : "Empty username is not permitted",
    "EMPTY_DIR_NAME" : "Empty username is not permitted",
    "EMPTY_FILE_NAME" : "Empty username is not permitted",
    "QUERY_DID_NOT_SUCCEED": "Query did not succeed",
    "INVALID_REQUEST": "Request is invalid",
    "DIR_EXISTS": "Directory with such name already exists",
    "NO_COPY_TO_ANOTHER_DIR": "Sorry, you can not copy to another directory"
}

'''
@param: code - error code which will return the description of the error
'''
def throw_error(code):
    if not code:
        return "ERROR"
    return errors[code]