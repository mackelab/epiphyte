---
title: 'Epiphyte: a relational database framework for naturalistic neuroscience experiments'
tags:
  - Python
  - neuroscience
  - relational database
  - electrophysiology
  - single neuron activity
  - local field potential
authors:
- name: Alana Darcher
  orcid: 0000-0001-9048-9732
  equal-contrib: false
  affiliation: "1"
- name: Rachel Rapp
  orcid: 
  equal-contrib: false
  affiliation: "2, 3"
- name: Tamara T. Mueller
  orcid: 0000-0002-1818-1036
  equal-contrib: false
  affiliation: "4"
- name: Franziska Gerken
  orcid: 0009-0004-9668-719X
  equal-contrib: false
  affiliation: "5"
- name: Janne K. Lappalainen
  orcid: 0000-0002-0547-7401
  equal-contrib: false
  affiliation: "2, 3"
- name: Gert Dehnen
  orcid: 
  equal-contrib: false
  affiliation: "1"
- name: Marcel S. Kehl
  orcid: 0000-0002-6812-8604
  equal-contrib: false
  affiliation: "1"
- name: Stefanie Liebe
  orcid: 
  equal-contrib: false
  affiliation: "2, 7"
- name: Laura Leal-Taixé
  orcid: 
  equal-contrib: false
  affiliation: "5"
- name: Florian Mormann
  orcid: 0000-0003-1305-8028
  equal-contrib: false
  affiliation: "1"
- name: Jakob H. Macke
  orcid: 0000-0001-5154-8912
  equal-contrib: false
  affiliation: "2, 3, 6"
affiliations:
  - name: Department of Epileptology, University Hospital Bonn, Bonn, Germany
    index: 1
  - name: Machine Learning in Science, Tübingen University, Germany
    index: 2
  - name: Tübingen AI Center, University of Tübingen, Germany
    index: 3
  - name: Institute for Artificial Intelligence in Medicine and Healthcare, Technical University of Munich, Germany
    index: 4
  - name: Dynamic Vision and Learning Group, Technical University of Munich, Munich, Germany
    index: 5
  - name: Max Planck Institute for Intelligent Systems, Tübingen, Germany
    index: 6
  - name: Department of Epileptology and Neurology, University Hospital Tübingen, Tübingen, Germany
    index: 7
date: 8 March 2026
bibliography: paper.bib
---

# Summary

Neuroscience experiments generate increasingly large and complex datasets [@sejnowski2014putting]. In particular, the use of naturalistic stimuli --- such as movies [@aliko2020naturalistic; @keles2024multimodal; @GerkenDarcher_2025], podcasts [@zada2025podcast], and video games [@li2025eeg] --- has expanded as researchers aim to study brain activity under ecologically valid, dynamic conditions that better approximate real-world perception and cognition. These advances in experimental design and recording technologies introduce new challenges for data organization and analysis. Large-scale datasets often include multiple kinds of neural signals, complicating storage and retrieval. Continuous, naturalistic stimuli lack clearly defined event structures and require additional processing for alignment with neural activity, such as detailed annotations of stimulus features. Given these challenges, experiments comprised of high-dimensional neural data collected under naturalistic conditions can be cumbersome to analyze using standard, file system-based frameworks. To  enable flexible analysis of such datasets, we developed `epiphyte`, a Python-based toolkit for database-backed workflows. 

`epiphyte` implements a domain-specific relational database designed for analyzing spiking and field potential data recorded during continuous, dynamic stimuli. In addition to structuring and storing neural data, `epiphyte` provides a framework for organizing stimulus features and meta-data that simplifies the analysis of neural signals recorded during a movie, audio track, or similarly naturalistic stimulus. Our package offers Python modules for structuring neural data, managing stimulus metadata, and organizing results in a structured, queryable form. The package also includes modules for generating mock data,  [documentation](https://www.mackelab.org/epiphyte/), and [tutorials](https://www.mackelab.org/epiphyte/#tutorials) that guide users through setting up a database locally or remotely and building complete analysis workflows.

`epiphyte` includes components and tutorials that demonstrate how to: 

- host a database on a virtual machine and enable remote access for collaborators,
- attach an external storage backend for large-scale data such as local field potentials,
- structure annotations of continuous and naturalistic stimuli,
- add new neural or stimulus data,
- analyze neural responses in relation to stimulus features, and
- train computational models directly from the database.
  
Dependencies include:

- `DataJoint` [@DataJoint]
- `MinIO` (optional) [@MinIO]
- `numpy` [@harris2020array]
- `pandas` [@mckinney2011pandas]
- `matplotlib` [@Hunter2007]
- `seaborn` [@Waskom2021]

# Statement of need

With the development of DataJoint [@DataJoint], relational databases have become more accessible to neuroscientists. However, designing, deploying, and maintaining a database ecosystem for experimental data remains technically challenging and time-consuming. While many research projects already rely on relational backends (see [here](https://docs.datajoint.com/projects/publications/)), few provide domain-specific, worked examples that can be readily adapted to new datasets. 

`epiphyte` addresses this gap by offering a standalone, fully functional framework tailored for analysis of neural activity recorded during a concurrent naturalistic stimulus. It can be used as an experimental analysis framework, adapted to specific experimental designs, or studied as a reference implementation. 

# State of the field 

Naturalistic neuroscience is expanding as a field. However, codebases and tools for analyzing experiments utilizing naturalistic and continuous stimuli generally take the form of code released alongside a publication [@wang2023brainbert; @keles2024multimodal]. `epiphyte` was built as a standalone framework for structuring complex stimuli, namely movies, to support the analysis of large neural datasets by providing experimenters with an end-to-end worked solution and tools for relating the content of a complex, continuous stimulus with concurrently recorded spiking and field potential activity.

# Software design

`epiphyte` contains the following modules: 

- `database`: specification and implementation of the tailored database,
- `preprocessing`: utilities for processing neural and stimulus data,
- `data`: generators for creating mock neural and stimulus data.

Beyond the common Python data science dependencies, `epiphyte` is built using DataJoint, a package that enables implementing and querying a MySQL database, and optionally, MinIO, which stores large data objects (such as field potential recordings) in a queryable format.

The main design contribution is the structuring and organization of stimulus, neural, and experiment-related meta-data. Movies and other naturalistic and continuous stimulus can be difficult to align with concurrently recorded neural data. To allow for flexible use of stimulus annotations, all stimulus-related items are structured as onset and offset times and the associated content values, and all subsequent analysis interactions are built around this structure, such as binning by movie frame (`epiphyte.data_preprocessing.binning`). Since experiment set-ups and their constituent data formats can vary between labs, we provide methods for generating a full mock dataset so users can quickly implement and use the framework without adjusting to their specific data formats. 

To increase the utility of `epiphyte`, we provide a set of tutorials for implementing a database and centering subsequent data analysis around database interactions. We include walkthroughs detailing how to: 

1. launch the database locally or remotely,
2. attach a storage back-end to an existing database,
3. install Epiphyte locally or remotely,
4. configure and connect to a database,
5. design and implement a database,
6. develop an analysis workflow,
7. enable access for other users, and
8. run regular backups.

# Research impact statement

`epiphyte` has been used as the main analysis framework for several projects, including the decoding of movie content from human single neurons [@GerkenDarcher_2025], the organization of a decade's collection of screening experiments [@darcher2024identifying], and the analysis of semantic receptive fields in concept cells [@Karkowski2025]. 

# AI usage disclosure

AI tools were used to generate type hints and to expland and unify documentation. All generated type hints and documentation elements were verified via manual review. 

# Acknowledgements

We thank Fabian Sinz, Edgar Walker, and Christoph-Benjamin Blessing for their input on implementing DataJoint infrastructure on a cluster. We thank Aleksandar Levic for feedback on the pre-processing pipeline,  Matthijs Pals and Tharanika Thevururasa for establishing the DataJoint infrastructure on Tuebingen's computer cluster, Sebastian Bischoff for helping troubleshoot MinIO, and Muthu Jeyanthi Prakash for testing the implementation and providing feedback on the tutorials. 
This research was funded by German Ministry of Education and Research (BMBF), grant number 031L01978 and the German Research Foundation (DFG) through Germany’s Excellence Strategy (EXC-Number 2064/1, Project number 390727645).

# References