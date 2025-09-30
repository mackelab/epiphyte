## Installation

Epiphyte can be configured and deployed for three main use cases: 

![Installation flowchart](reference/installation_flowchart.png){ .img-center .w-600 }

### Option A: Install a local instance of Epiphyte. 

Use cases: 

* You want to test out the database infrastructure.
* You will be the only user and do not work with large data files. 

[Install locally,](tutorials/Launch%20the%20MySQL%20database%20locally.md)

[and continue to *Configure and connect to the database*.](tutorials/4.%20Configure%20and%20connect%20to%20the%20database.md)

### Option B: Install a remote instance of Epiphyte, without MinIO.

Use cases:

* Multiple people, accessing from separate locations, will use the database. 
* You do not need to support large data files. 

[Install on a server-hosted virtual machine,](tutorials/1.%20Launch%20the%20MySQL%20database%20on%20a%20virtual%20machine.md)

[and continue to *Install and set up Epiphyte*.](tutorials/3.%20Install%20Epiphyte.md)

### Option C: Install a remote instance of Epiphyte, with MinIO.

Use cases:

* Multiple people, accessing from separate locations, will use the database. 
* You use large data files (e.g., LFP, movie data, multi-hour calcium imaging).

[Start at *Launch the MySQL database on a virtual machine* and continue through the remaining tutorials.](tutorials/1.%20Launch%20the%20MySQL%20database%20on%20a%20virtual%20machine.md)
