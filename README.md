# dazel
Run Google's bazel inside a docker container via a seamless proxy.

bazel is awesome at creating fast and reproducible builds on your own development environemnt.
The problem is that it works in an imperfect and non-portable environment.
Enter dazel.

dazel allows you to create your build environment as a Docker image, either via a Dockerfile or a prebuilt repository.
The tool itself is a simple python script that sends the command line arguments directly to bazel inside the container, and mapping all of the necessary volumes to make it seamless to you.
It uses the 'docker exec' command to achieve this, and maps the current directory and the bazel-WORKDIR link directory so that the results appear on the host seamlessly.

It is run the same way you would bazel:
```bash
dazel build //my/cool/package/...
dazel run //my/cool/package:target
```

This was a simple build and run.
The command line arguments were sent as is into the docker container, and the output was run again inside the container.

Running the command for the first time will start the container on it's own, and it will automatically detect if there is need to rebuild or restart the container.
You can configure anything you need through the ".dazelrc" file in the same directory.
Take a look at the configuration section for information on how to write one.

## Installation

### Dependencies
```bash
apt-get install python python-pip
apt-get install docker
```

### Install dazel
```bash
pip install dazel
```

That's all there is to it.
Even bazel is not required!

## Configuration

You can configure dazel in two ways (or combine):
* A .dazelrc file in the current directory.
* Environment variables with the configuration parameters mentioned below.

Note that specific environment variables supercede the values in the .dazelrc file.

The possible parameters to set are:
* DAZEL_INSTANCE_NAME="name of the docker container to run" [Default: "dazel"]
* DAZEL_IMAGE_NAME="name of the dazel image to build or pull" [Default: "dazel"]
* DAZEL_DOCKERFILE="path to the Dockerfile to use to build the dazel image" [Default: "Dockerfile.dazel"]
* DAZEL_REPOSITORY="the repository to pull the dazel image from" [Default: "dazel"]
* DAZEL_DIRECTORY="the directory to build the dazel image in" [Default: $PWD]

