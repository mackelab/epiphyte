# Epiphyte

[![Docs](https://img.shields.io/badge/docs-online-success)](https://www.mackelab.org/epiphyte/) [![Docs](https://img.shields.io/website?url=https%3A%2F%2Fmackelab.github.io%2Fepiphyte%2F)](https://www.mackelab.org/epiphyte/)


## What is Epiphyte?

Epiphyte is a domain-specific relational database designed for analyzing spiking and field potential data recorded during movie presentations. 

At its core, Epiphyte is a worked solution for organizing movie annotations and neural data using [DataJoint](https://github.com/datajoint) and [MinIO](https://github.com/minio/minio).

We provide an open-source framework for building and remotely deploying a database structured specifically for working with naturalistic and continuous stimuli and neural recordings. As a worked example, we provide a module for generating a mock dataset and a configured database structure for the generated dataset to allow for users to immediately try out the framework. 

## Use

We provide detailed tutorials in the Docs for:
- [launching a MySQL database locally or on a virtual machine](https://www.mackelab.org/epiphyte/tutorials/1a.%20Launch%20a%20MySQL%20database%20locally/),
- [attaching an optional storage backend](https://www.mackelab.org/epiphyte/tutorials/2.%20%28Optional%29%20Attach%20a%20storage%20back-end%20to%20an%20existing%20database/),
- [installing](https://www.mackelab.org/epiphyte/tutorials/3.%20Install%20Epiphyte%20locally%20or%20remotely/) and [configuring](https://www.mackelab.org/epiphyte/tutorials/4.%20Configure%20and%20connect%20to%20a%20database/) the framework, 
- [designing and populating a database for analyzing a generated movie dataset](https://www.mackelab.org/epiphyte/tutorials/5.%20Design%20and%20implement%20a%20database/),
- [extending database access to other users](https://www.mackelab.org/epiphyte/tutorials/7.%20Enable%20access%20for%20other%20users/), 
- as well as analyzing data and running regular backups. 

