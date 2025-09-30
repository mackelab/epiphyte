# Tutorial: Launch the MySQL database locally

### **Requirements:** 
* OS: Linux or Mac/OSx
* Python 3.5 or higher (either system-level, or in an IDE)
* 400 MB free disk space
* Permission to perform sudo-level commands

### Installation: 

The installation of `epiphyte` has three steps: 

1. Install and set-up the DataJoint docker container. 
2. Download and launch the DataJoint MySQL server via docker-compose.
3. Install `Epiphyte`.

### 1. Install and set-up the DataJoint docker container. 

* Install the correct [Docker](https://docs.docker.com/get-docker/) for your OS.
* Verify the Docker installation: 
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
docker --version
docker run hello-world
</pre>
* Install [Docker Compose](https://docs.docker.com/compose/install/).
* Verify the Docker Compose installation:
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
docker-compose --version
</pre>

### 2. Download and launch the DataJoint MySQL server via docker-compose.

(Following is taken from [DataJoint documentation](https://github.com/datajoint/mysql-docker).)

* Create a directory to store the docker-compose YAML file:
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
mkdir mysql-docker
cd mysql-docker
wget https://raw.githubusercontent.com/datajoint/mysql-docker/master/docker-compose.yaml
docker-compose up -d
</pre>
* Download a package that enables access to your locally running MySQL server:

> Linux: 
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
sudo apt-get install mysql-client
</pre>

> Mac (via [Homebrew](https://brew.sh/)): 
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
brew install mysql@5.7
brew tap homebrew/services
brew services start mysql@5.7
brew services list
brew link --force mysql@5.7
mysql -V # verify the installation
</pre>
* Test the server access. If there are issues, refer [here](https://github.com/mackelab/Epiphyte/wiki/Troubleshooting).
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
mysql -h 127.0.0.1 -u root -p
Enter password: [type in your password here: default is "simple"]
</pre>


### 3. Install `Epiphyte`:

There are two ways to install `epiphyte` -- via `pip` or cloning this repo. 

Note: certain features of the DataJoint python package have not been updated for more recent releases of Python. Therefore, DataJoint and epiphyte require an older version of Python (<=3.9). For this reason, we recommend using a conda environment to install all needed packages and to develop from. 

#### Install via `git`

* Clone the repository:
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
git clone git@github.com:mackelab/epiphyte.git
cd epiphyte
</pre>

* Create a new conda environment suitable for the `epiphyte` requirements: 
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
conda create --name epiphyte python=3.9.18 ipython
</pre>

* Activate the conda environment: 
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
conda activate epiphyte
</pre>

* Install the needed dependencies using `setup.py`:
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
pip install .
</pre>

* Verify the installation:
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
conda list
</pre>

#### Or, install via `pip` in a `conda` environment 

* Create a new conda environment suitable for the `epiphyte` requirements: 
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
conda create --name epiphyte python=3.9.18 ipython
</pre>
* Activate the conda environment and install `epiphyte`:
<pre style="background-color: #1E1E1E; color: white; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;">
conda activate epiphyte
pip install epiphyte
</pre>


[Continue to *Configure and connect to the database*.](<4. Configure and connect to the database.md>)
