# Epiphyte

Welcome to the Epiphyte documentation! 

[Epiphyte](https://github.com/mackelab/epiphyte) is a toolkit for using a relational database to organize and analyze large neural datasets, particularly experiments which use dynamic, continuous stimuli like movies.

**The focus**: unit-wise and population analysis of single neurons paired with dynamic, continous, or otherwise complex stimuli. 

**The core**: a [DataJoint database](https://arxiv.org/abs/1807.11104) built for organizing spiking & field potential data and stimulus information such as feature annotations. 

**The shell**: a series of Python modules for building analysis pipelines using database, including modules for generating simulated data and setting up an example database. 


## Getting Started

### Installation

The [Install](install.md) page provides detailed instructions for setting up Epiphyte for your particular use case. 

### Tutorials

We provide a series of tutorials for setting up, configuring, and using the Epiphyte core database. No prior knowledge of relational databases is needed. 

The set-up and configuration scales to any DataJoint implementation, and can be used beyond the example database included in this project. 

1. [Launch the database locally](tutorials/Launch%20the%20MySQL%20database%20locally.md) or [Launch the database on a virtual machine](tutorials/1.%20Launch%20the%20MySQL%20database%20on%20a%20virtual%20machine.md)
2. [(Optional) Add MinIO to an existing virtual machine](tutorials/2.%20(Optional)%20Add%20MinIO%20to%20an%20existing%20virtual%20machine.md)
3. [Install Epiphyte](tutorials/3.%20Install%20Epiphyte.md)
4. [Configure and connect to the database](tutorials/4.%20Configure%20and%20connect%20to%20the%20database.md)
5. [Design and implement the database](tutorials/5.%20Design%20and%20implement%20the%20database.md)
6. [Compile the codebase](tutorials/6.%20Compile%20the%20codebase.md)
7. [(Optional) Run regular backups](tutorials/7.%20(Optional)%20Run%20regular%20backups.md)

### API Reference

- Browse API Reference for module-level documentation