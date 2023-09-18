# Epiphyte

## What is Epiphyte?

This project is a processing pipeline for high-dimensional single-unit neural activity colligated with meta data. 
We present a toolbox for organizing neural activity alongside meta-data and stimulus information, as well as a processing pipeline which allows ad-hoc importing, exporting, annotating, and visualizing of data. Our toolbox is developed for large sets of continuous single-unit recordings and introduces a set of modules for algorithmically and manually annotating data, defining data irregularities, and designating new layers of meta-data for further analyses.

## How to install Epiphyte? 

#### Note: These installation instructions assume that you are familiar Python and using command line interfaces. If you would like to set this package up from scratch (no assumed experience), check out the more robust instructions [here.](https://github.com/mackelab/Epiphyte/wiki/Installation)

### (1) Clone the Epiphyte repository to your machine. 

```
git clone https://github.com/mackelab/epiphyte.git 
```

Navigate to the folder of the cloned package: 
```
cd epiphyte
```


### (2) Install the required packages by running the following command (Note: we highly recommend doing so within a virtual environment with Python==3.7):

If using PyPip:
```
pip install -r requirements_pip.txt
```

If using Conda:
```
conda create --name <env> --file requirements_conda.txt
```


### (3) Go to the top-level folder of Epiphyte and install the package itself
```
pip install -e .
```

### (4) Set up a DataJoint database

**Prerequesites:**
- install [docker](https://www.docker.com/)
- install [docker compose](https://docs.docker.com/compose/install/)

**Actual setup:**
- follow instructions on DataJoint [tutorial page](https://tutorials.datajoint.io/setting-up/local-database.html) to set up for using a docker container with database.

    **Note for macOS users:** we recommend installing MySQL via Homebrew (as opposed to the direct download via Docker or MySQL). For instructions, check out the [Homebrew instructions](https://gist.github.com/operatino/392614486ce4421063b9dece4dfe6c21) or [step 6 of the install tutorial](https://github.com/mackelab/Epiphyte/wiki/Installation#mac).
- navigate to the top-level directory of Epiphyte and run the docker container:
```
sudo docker-compose up -d
```
- run [database/database_set_up.ipynb](https://github.com/mackelab/Epiphyte/blob/master/database/database_set_up.ipynb) notebook to fill the database with the mock data
- now everything should be set up and ready to go! 
- for troubleshooting issues, check out [here](https://github.com/datajoint/mysql-docker).

## Example Usage

## How to set up the dev environment 

## Change log

## License and author info

If you have questions/comments/suggestions, either open an issue within GitHub, or feel free to email: alana.darcher@gmail.com
