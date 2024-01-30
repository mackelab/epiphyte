import datajoint as dj

dj.config["enable_python_native_blobs"] = True
dj.config['database.host'] = '127.0.0.1'
dj.config['database.user'] = "root"
dj.config['database.password'] = 'simple'

epi_schema = dj.schema('epiphyte_mock')

dj.config['stores'] = {
    'local': {  # store in files
        'protocol': 'file',
        'location': os.path.abspath('./dj-store')
    }}
