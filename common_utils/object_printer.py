# Print a string at a specific indentation level (to console/file)
### level = indentation, 1 level = 2 spaces
### text  = string to print
### file  = file to write to (if None, write to console)
def print_indented(level, text, file = None):
    string = '  ' * level + text
    if file is None:
        print(string)
    else:
        file.write(string + '\n')


# Dump the contents of an object recursively
### obj   = object to dump
### name  = displayed name of object
### level = indentation
### file  = file to write to (if None, write to console)
def print_object(obj, name = '', level = 0, file = None, int_as_hex = True):
    # Dictionaries
    if type(obj) is dict:
        # Print each key-value pair in the dictionary
        print_indented(level, '{} {{'.format(name) if name != '' else '{', file)
        for key in obj:
            item = obj[key]
            print_object(item, key, level + 1, file, int_as_hex)
        print_indented(level, '}', file)
    
    # Lists
    elif type(obj) is list:
        # Print each object in the list
        print_indented(level, '{} ({}) {{'.format(name, len(obj)) if name != '' else '({}) {{'.format(len(obj)), file)
        counter = 0
        for item in obj:
            print_object(item, '[{}]'.format(counter), level + 1, file, int_as_hex)
            counter += 1
        print_indented(level, '}', file)
    
    # Simple objects
    else:
        # Print integers in HEX, unless negative (or disabled)
        if type(obj) is int:
            if not int_as_hex or obj < 0:
                print_indented(level, '{}: {}'.format(name, obj), file)
            else:
                print_indented(level, '{}: 0x{:X}'.format(name, obj), file)
        
        # Print strings inside quotes
        elif isinstance(obj, str):
            print_indented(level, '{}: \'{}\''.format(name, obj), file)
        
        # Print all other objects without additional formatting
        else:
            print_indented(level, '{}: {}'.format(name, obj), file)
