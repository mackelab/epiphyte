import os
import datajoint as dj

dj.config["enable_python_native_blobs"] = True
dj.config['database.host'] = '127.0.0.1'            # localhost address, addresses the computer the code is run from 
dj.config['database.user'] = "root"                 # default username
dj.config['database.password'] = 'simple'           # default password, change before actually using a database

epi_schema = dj.schema('epiphyte_mock')

dj.config['stores'] = {
    'local': {  # store in files
        'protocol': 'file',
        'location': os.path.abspath('./dj-store')
    }}
