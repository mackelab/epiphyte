# DeepHumanVision

This project is a processing pipeline for high-dimensional single-unit neural activity colligated with meta data. 
We present a toolbox for organizing neural activity alongside meta-data and stimulus information, as well as a processing pipeline which allows ad-hoc importing, exporting, annotating, and visualizing of data. Our toolbox is developed for large sets of continuous single-unit recordings and introduces a set of modules for algorithmically and manually annotating data, defining data irregularities, and designating new layers of meta-data for further analyses.

## Installing the package

#### Note: These installation instructions assume that you have basic fluency in Python and command line interfaces. If you would like to set-up this package from scratch, check out the more robust instructions [here.](https://github.com/mackelab/DeepHumanVision_deploy/wiki/Installation)

### (1) Install the required packages by running the following command (Note: we highly recommend doing so within a virtual environment with Python==3.7):
```
pip install -r requirements.txt
```

### (2) Go to the top-level folder DeepHumanVision_deploy and install the package itself
```
pip install -e .
```

### (3) Set up a DataJoint database

**Prerequesites:**
- install [docker](https://www.docker.com/)
- install [docker compose](https://docs.docker.com/compose/install/)

**Actual setup:**
- follow instructions on DataJoint [tutorial page](https://tutorials.datajoint.io/setting-up/local-database.html) to set up for using a docker container with database.
- navigate to the top-level directory of DeepHumanVision_deploy and run the docker container:
```
sudo docker-compose up -d
```
- run [database/database_set_up.ipynb](https://github.com/mackelab/DeepHumanVision_deploy/blob/master/database/database_set_up.ipynb) notebook to fill the database with the mock data
- now everything should be set up and ready to go! 
- for troubleshooting issues, check out [here](https://github.com/datajoint/mysql-docker).
