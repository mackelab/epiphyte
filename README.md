# DeepHumanVision

This project is a processing pipeline for high-dimensional single-unit neural activity colligated with meta data. 
We present a toolbox for organizing neural activity alongside meta-data and stimulus information, as well as a processing pipeline which allows ad-hoc importing, exporting, annotating, and visualizing of data. Our toolbox is developed for large sets of continuous single-unit recordings and introduces a set of modules for algorithmically and manually annotating data, defining data irregularities, and designating new layers of meta-data for further analyses.

## Installing the package

### (1) Create a virtual environment, by installing all requirements:
```
pip install -r requirements.txt
```

### (2) Go to the top-level folder DeepHumanVision_deploy and install the package itself
```
pip install -e .
```

### (3) Set up a DataJoint database

**Prerequesites:**
- install docker (link)

**Actual setup**
- run docker container
```
sudo docker-compose up -d
```
(link and more information coming)
